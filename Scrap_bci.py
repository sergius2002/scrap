import asyncio
import hashlib
from playwright.async_api import async_playwright
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import os
import random
import time
import json
import platform
import uuid
import subprocess
import gc
import psutil
from pathlib import Path

# Obtener la ruta del directorio actual
current_dir = Path(__file__).parent.absolute()

# Cargar variables de entorno desde el archivo .env en el directorio actual
with open(os.path.join(current_dir, '.env')) as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# Configuración de conexión a Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH")
SHEET_URL = os.environ.get("SHEET_URL")
CARPETA_ARCHIVOS = os.environ.get("CARPETA_ARCHIVOS")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
PDF_OUTPUT_DIR = os.environ.get("PDF_OUTPUT_DIR")
TOKEN_PATH = os.environ.get("TOKEN_PATH")
API_TOKEN_SAN_CRISTOBAL = os.environ.get("API_TOKEN_SAN_CRISTOBAL")
API_TOKEN_ST_CRISTOBAL = os.environ.get("API_TOKEN_ST_CRISTOBAL")

# Configuración de rutas
EXCEL_OUTPUT_DIR = os.path.join(current_dir, "Bancos")
os.makedirs(EXCEL_OUTPUT_DIR, exist_ok=True)
EXCEL_FILE_PATH = os.path.join(EXCEL_OUTPUT_DIR, "excel_detallado.xlsx")

# Configuración de perfiles de navegador
BROWSER_PROFILES = [
    {
        "name": "Windows_Chrome",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "platform": "Windows",
        "color_depth": 24,
        "pixels_depth": 24
    },
    {
        "name": "Windows_Edge",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "Windows",
        "color_depth": 24,
        "pixels_depth": 24
    },
    {
        "name": "Windows_Firefox",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "viewport": {"width": 1440, "height": 900},
        "platform": "Windows",
        "color_depth": 24,
        "pixels_depth": 24
    }
]

# Headers predefinidos por navegador
BROWSER_HEADERS = {
    "Windows_Chrome": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    },
    "Windows_Edge": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Microsoft Edge";v="122", "Chromium";v="122", "Not(A:Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    },
    "Windows_Firefox": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }
}

class BrowserProfile:
    def __init__(self):
        self.profile = random.choice(BROWSER_PROFILES)
        self.session_id = str(uuid.uuid4())
        self.headers = BROWSER_HEADERS[self.profile["name"]]
        
    async def setup_context(self, playwright):
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                f'--window-size={self.profile["viewport"]["width"]},{self.profile["viewport"]["height"]}',
                '--start-maximized',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-browser-side-navigation',
                '--disable-features=site-per-process',
                '--disable-notifications',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--no-default-browser-check',
                '--no-first-run',
                f'--user-agent={self.profile["user_agent"]}',
                '--lang=es-CL'
            ]
        )
        
        context = await browser.new_context(
            viewport=self.profile["viewport"],
            user_agent=self.profile["user_agent"],
            accept_downloads=True,
            java_script_enabled=True,
            ignore_https_errors=True,
            locale='es-CL',
            timezone_id='America/Santiago',
            extra_http_headers=self.headers,
            bypass_csp=True,
            geolocation={'latitude': -33.4369, 'longitude': -70.6483},
            permissions=['geolocation'],
            color_scheme='light',
            forced_colors='none',
            reduced_motion='no-preference',
            has_touch=False
        )
        
        await context.add_cookies([
            {
                'name': 'session_id',
                'value': self.session_id,
                'domain': '.bci.cl',
                'path': '/'
            },
            {
                'name': 'region',
                'value': 'CL',
                'domain': '.bci.cl',
                'path': '/'
            },
            {
                'name': 'timezone',
                'value': 'America/Santiago',
                'domain': '.bci.cl',
                'path': '/'
            }
        ])
        
        await context.add_init_script("""
            (() => {
                delete Object.getPrototypeOf(navigator).webdriver;
                
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    const context = originalGetContext.apply(this, arguments);
                    if (type === '2d') {
                        const originalFillText = context.fillText;
                        context.fillText = function() {
                            return originalFillText.apply(this, arguments);
                        }
                    }
                    return context;
                };

                ['mousedown', 'mouseup', 'mousemove'].forEach(eventType => {
                    document.addEventListener(eventType, function(event) {
                        event.isTrusted = true;
                    }, true);
                });

                Object.defineProperty(navigator, 'fonts', {
                    get: () => new class FontFaceSet extends EventTarget {
                        check() { return true; }
                        load() { return Promise.resolve([]); }
                    }
                });
            })();
        """)
        
        return browser, context
    
    def _get_evasion_script(self):
        return f"""
            (() => {{
                // Ocultar webdriver
                Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                
                // Simular plataforma
                Object.defineProperty(navigator, 'platform', {{ get: () => '{self.profile["platform"]}' }});
                
                // Simular plugins específicos del navegador
                const plugins = {self._get_browser_plugins()};
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => {{
                        return {{
                            ...plugins,
                            length: plugins.length,
                            item: (i) => plugins[i],
                            namedItem: (name) => plugins.find(p => p.name === name),
                            refresh: () => {{}},
                        }};
                    }}
                }});
                
                // Simular características específicas del navegador
                window.chrome = {{
                    app: {{
                        InstallState: {{
                            DISABLED: 'DISABLED',
                            INSTALLED: 'INSTALLED',
                            NOT_INSTALLED: 'NOT_INSTALLED'
                        }},
                        RunningState: {{
                            CANNOT_RUN: 'CANNOT_RUN',
                            READY_TO_RUN: 'READY_TO_RUN',
                            RUNNING: 'RUNNING'
                        }},
                        getDetails: function() {{}},
                        getIsInstalled: function() {{}},
                        installState: function() {{}},
                        isInstalled: false,
                        runningState: function() {{}}
                    }},
                    runtime: {{}},
                    webstore: {{}}
                }};
                
                // Simular características de hardware
                Object.defineProperty(screen, 'colorDepth', {{ get: () => {self.profile["color_depth"]} }});
                Object.defineProperty(screen, 'pixelDepth', {{ get: () => {self.profile["pixels_depth"]} }});
                
                // Simular WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{
                        return 'Intel Inc.';
                    }}
                    if (parameter === 37446) {{
                        return 'Intel Iris OpenGL Engine';
                    }}
                    return getParameter.apply(this, [parameter]);
                }};
            }})();
        """
    
    def _get_browser_plugins(self):
        if "Firefox" in self.profile["name"]:
            return "[]"
        return """[
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' }
        ]"""

async def random_delay(min_seconds=0.5, max_seconds=1.5):
    """Genera una pausa aleatoria para simular comportamiento humano"""
    base_delay = random.uniform(min_seconds, max_seconds)
    # Añadir micro-variaciones
    micro_delay = random.uniform(0, 0.05)
    await asyncio.sleep(base_delay + micro_delay)

async def simular_comportamiento_humano(page):
    try:
        # Simular movimientos más naturales del mouse
        num_movements = random.randint(4, 8)
        for _ in range(num_movements):
            # Generar puntos de control para curva Bezier
            points = []
            for _ in range(random.randint(3, 5)):
                points.append({
                    'x': random.randint(100, 800),
                    'y': random.randint(100, 600)
                })
            
            # Movimiento suave entre puntos
            for i in range(len(points) - 1):
                steps = random.randint(10, 20)
                for step in range(steps):
                    t = step / steps
                    x = points[i]['x'] + (points[i+1]['x'] - points[i]['x']) * t
                    y = points[i]['y'] + (points[i+1]['y'] - points[i]['y']) * t
                    await page.mouse.move(x, y)
                    await random_delay(0.01, 0.03)
        
        # Simular scroll más natural
        if random.random() > 0.3:
            scroll_steps = random.randint(5, 10)
            for _ in range(scroll_steps):
                delta = random.randint(50, 150)
                await page.mouse.wheel(0, delta)
                await random_delay(0.2, 0.5)
        
        # Simular pausas de lectura más realistas
        if random.random() > 0.4:
            await random_delay(2, 5)
            
    except Exception as e:
        print(f"Error en simulación de comportamiento: {e}")

async def login_to_bci(page):
    try:
        print("🌐 Iniciando proceso de login en BCI...")
        
        # Reducir tiempo de espera inicial
        await random_delay(5, 8)
        
        # Navegar primero a la página principal de BCI
        await page.goto("https://www.bci.cl", timeout=30000)
        await random_delay(2, 3)
        await simular_comportamiento_humano(page)
        
        # Luego navegar a empresas
        await page.goto("https://www.bci.cl/empresas", timeout=30000)
        await random_delay(2, 3)
        await simular_comportamiento_humano(page)
        
        # Finalmente ir a la página de login
        print("🔄 Navegando a página de login...")
        await page.goto(
            "https://www.bci.cl/corporativo/banco-en-linea/pyme",
            timeout=30000,
            wait_until="domcontentloaded"
        )
        await random_delay(2, 3)
        
        # Simular más interacción humana antes del login
        await simular_comportamiento_humano(page)
        
        print("🔍 Esperando elementos del formulario...")
        # Esperar y llenar RUT con pausas entre cada carácter
        rut = "25880004-4"
        for char in rut:
            await page.type("input#rut_aux", char, delay=random.randint(50, 150))
            await random_delay(0.1, 0.2)
        
        await random_delay(1, 2)
        
        # Simular que se revisa lo escrito
        await page.hover("input#rut_aux")
        await random_delay(0.5, 1)
        
        # Escribir contraseña con pausas variables
        clave = "Ps178445"
        for char in clave:
            await page.type("input#clave", char, delay=random.randint(75, 175))
            await random_delay(0.1, 0.2)
        
        await random_delay(1, 2)
        
        # Simular revisión final antes de hacer clic
        await simular_comportamiento_humano(page)
        
        print("🔑 Intentando iniciar sesión...")
        submit_button = "//button[@type='submit'][contains(.,'Ingresar')]"
        
        # Mover el mouse al botón de forma más natural
        await page.hover(submit_button)
        await random_delay(0.5, 1)
        
        # Ocasionalmente mover el mouse un poco antes de hacer clic
        if random.random() > 0.5:
            button = await page.query_selector(submit_button)
            bbox = await button.bounding_box()
            if bbox:
                x = bbox['x'] + bbox['width'] * random.uniform(0.1, 0.9)
                y = bbox['y'] + bbox['height'] * random.uniform(0.1, 0.9)
                await page.mouse.move(x, y)
                await random_delay(0.2, 0.4)
        
        # Hacer clic con delay variable
        async with page.expect_navigation(timeout=15000):
            await page.click(submit_button, delay=random.randint(50, 150))
        
        await random_delay(2, 3)
        
        # Verificar si hay bloqueo
        if await handle_security_block(page):
            print("⚠️ Detectado bloqueo de seguridad, esperando...")
            # Reducir tiempo de espera en caso de bloqueo
            await random_delay(5, 10)  # 5-10 segundos
            return False
            
        print("✅ Login exitoso")
        return True
        
    except Exception as e:
        print(f"❌ Error durante el login: {str(e)}")
        return False

async def handle_security_block(page):
    """Maneja los bloqueos de seguridad del sitio con reinicio de sesión"""
    try:
        blocked_text = await page.text_content("body")
        blocked_indicators = [
            "Ha sido bloqueado por nuestra política de seguridad",
            "política de seguridad",
            "acceso bloqueado",
            "acceso denegado"
        ]
        
        if any(indicator.lower() in blocked_text.lower() for indicator in blocked_indicators):
            print("⚠️ Detectado bloqueo de seguridad...")
            print("🔄 Reiniciando sesión...")
            
            # Limpiar cookies y caché
            await page.context.clear_cookies()
            await page.reload()
            
            # Esperar tiempo aleatorio entre 8 y 15 minutos
            espera = random.randint(480, 900)
            print(f"⏳ Esperando {espera} segundos antes de reintentar...")
            await asyncio.sleep(espera)
            return True
        return False
    except Exception:
        return False

async def cleanup_resources(browser, context, page):
    """Limpia los recursos del navegador y libera memoria"""
    try:
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()
        gc.collect()
    except Exception as e:
        print(f"Error al limpiar recursos: {e}")

async def monitor_table_changes():
    """Función principal para monitorear y descargar datos"""
    browser = None
    context = None
    page = None
    
    try:
        browser_profile = BrowserProfile()
        async with async_playwright() as p:
            browser, context = await browser_profile.setup_context(p)
            page = await context.new_page()
            
            # Configurar límites de memoria para el contexto
            await context.set_extra_http_headers({
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
            
            login_successful = await login_to_bci(page)
            if not login_successful:
                raise Exception("No se pudo completar el login")

            await random_delay(4, 6)
            print("🔄 Navegando a la sección de descarga...")
            
            # Continuar con la navegación
            print("⏳ Esperando por iframe principal...")
            await page.wait_for_selector("iframe#iframeContenido", timeout=40000)
            iframe_element = await page.query_selector("iframe#iframeContenido")
            iframe = await iframe_element.content_frame()
            if not iframe:
                raise Exception("No se pudo acceder al primer iframe")

            # Simular comportamiento natural entre navegaciones
            await simular_comportamiento_humano(page)
            
            print("🔍 Buscando menú de navegación...")
            await random_delay(2, 3)
            menu_button = await iframe.wait_for_selector("#item-title2", timeout=20000)
            
            # Simular hover antes de click
            await menu_button.hover()
            await random_delay(0.5, 1)
            print("📌 Haciendo clic en primer menú...")
            await menu_button.click()
            
            await random_delay(2, 3)
            print("🔍 Buscando submenú...")
            submenu_button = await iframe.wait_for_selector("#subitem-title21", timeout=20000)
            
            # Simular movimiento natural al submenú
            await submenu_button.hover()
            await random_delay(0.3, 0.7)
            print("📌 Haciendo clic en submenú...")
            await submenu_button.click()

            await random_delay(3, 4)
            print("⏳ Esperando por iframe secundario...")
            await iframe.wait_for_selector("iframe#oss-layout-iframe", timeout=40000)
            second_iframe_element = await iframe.query_selector("iframe#oss-layout-iframe")
            second_iframe = await second_iframe_element.content_frame()
            if not second_iframe:
                raise Exception("No se pudo acceder al segundo iframe")

            # Más comportamiento humano
            await simular_comportamiento_humano(page)
            
            print("📥 Iniciando proceso de descarga...")
            await random_delay(2, 3)
            print("🔍 Buscando botón de descarga...")
            download_button = await second_iframe.wait_for_selector(
                "button.bci-wk-button-with-icon:has-text('Descargar')",
                timeout=20000
            )
            
            # Simular interacción natural con el botón de descarga
            await download_button.hover()
            await random_delay(0.5, 1)
            print("📌 Haciendo clic en botón de descarga...")
            await download_button.click()
            
            await random_delay(2, 3)
            print("🔍 Buscando opción de excel detallado...")
            excel_option = await second_iframe.wait_for_selector(
                "li.item:has-text('Descargar excel detallado')",
                timeout=20000
            )
            
            # Simular selección natural de la opción de Excel
            await excel_option.hover()
            await random_delay(0.5, 1)
            
            print("📥 Iniciando descarga del archivo...")
            async with page.expect_download() as download_info:
                await excel_option.click()
            
            download = await download_info.value
            file_path = await download.path()
            
            if file_path:
                # Asegurar que el directorio existe
                os.makedirs(EXCEL_OUTPUT_DIR, exist_ok=True)
                local_file = os.path.join(EXCEL_OUTPUT_DIR, "excel_detallado.xlsx")
                await download.save_as(local_file)
                print(f"✅ Archivo descargado exitosamente: {local_file}")
                
                # Verificar el archivo descargado
                if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                    print("✅ Verificación de archivo completada")
                else:
                    raise Exception("El archivo descargado parece estar vacío o corrupto")

    except Exception as e:
        print(f"❌ Error en la automatización BCI: {str(e)}")
        print(f"📍 Stack trace completo: {e.__class__.__name__}")
    finally:
        await cleanup_resources(browser, context, page)
        gc.collect()

async def monitor_table_changes_with_retry():
    """Función principal con sistema de reintentos mejorado"""
    max_retries = 3
    retry_count = 0
    last_error = None
    
    while True:
        try:
            # Verificar memoria disponible antes de iniciar
            available_memory = psutil.virtual_memory().available / 1024 / 1024
            if available_memory < 1000:  # Menos de 1GB disponible
                print(f"⚠️ Memoria baja ({available_memory:.2f}MB). Esperando...")
                await asyncio.sleep(300)  # Esperar 5 minutos
                continue
            
            await monitor_table_changes()
            print("✅ Proceso BCI completado. Ejecutando bci.py...")
            subprocess.run(["python", "bci.py"])
            
            retry_count = 0
            last_error = None
            
            # Esperar con intervalo aleatorio
            wait_time = random.randint(15, 30)
            print(f"⏳ Esperando {wait_time} segundos antes de la siguiente ejecución...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            retry_count += 1
            last_error = str(e)
            
            base_wait = min(3 * (2 ** (retry_count - 1)), 5)
            variation = random.uniform(-1, 1)
            wait_time = max(1, base_wait + variation)
            
            print(f"❌ Error detectado (intento {retry_count}/{max_retries}): {e}")
            print(f"⏳ Esperando {int(wait_time)} segundos antes de reintentar...")
            
            if retry_count >= max_retries:
                print("⚠️ Máximo número de reintentos alcanzado.")
                print(f"🔍 Último error: {last_error}")
                print("⏳ Esperando 15 segundos antes de reiniciar el ciclo...")
                retry_count = 0
                await asyncio.sleep(15)
            else:
                await asyncio.sleep(wait_time)

if __name__ == "__main__":
    print("🤖 Iniciando automatización BCI...")
    print(f"📅 Fecha y hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        asyncio.run(monitor_table_changes_with_retry())
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
    finally:
        print("👋 Finalizando automatización BCI")
        gc.collect()