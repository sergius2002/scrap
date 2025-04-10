################################################################################
# proyecto_completo_minimizado.py
################################################################################

import asyncio  # Para manejar la asincronía
import os       # Para manejar rutas y directorios
import time     # Para time.sleep() en el bucle
import subprocess  # Para ejecutar Santander.py
from playwright.async_api import async_playwright, Page, Frame
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de conexión a Supabase y otras variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
SHEET_URL = os.getenv("SHEET_URL")
CARPETA_ARCHIVOS = os.getenv("CARPETA_ARCHIVOS")
PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR")
TOKEN_PATH = os.getenv("TOKEN_PATH")
API_TOKEN_SAN_CRISTOBAL = os.getenv("API_TOKEN_SAN_CRISTOBAL")
API_TOKEN_ST_CRISTOBAL = os.getenv("API_TOKEN_ST_CRISTOBAL")

# Verificar que CARPETA_ARCHIVOS esté definida
if not CARPETA_ARCHIVOS:
    raise EnvironmentError("La variable de entorno 'CARPETA_ARCHIVOS' no está definida.")

################################################################################
# Función principal asíncrona
################################################################################
async def run_flow_once():
    """
    Un ciclo completo de:
      1) Abrir navegador y navegar a la URL de login.
      2) Clic en "Ingresar".
      3) Llenar RUT y clave, y clic en "Aceptar".
      4) Clic en "Cuentas Corrientes" y "Saldos y movimientos".
      5) Descargar primer Excel con nombre fijo.
      6) Finalizar el flujo cerrando el navegador.
    """
    ############################################################################
    # Variables de configuración
    ############################################################################
    # Obtener el directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Carpeta donde se guardarán los archivos (usando CARPETA_ARCHIVOS)
    ruta_directorio = os.path.join(current_dir, CARPETA_ARCHIVOS)

    # Verificar que la ruta_directorio exista; si no, crearla
    if not os.path.exists(ruta_directorio):
        os.makedirs(ruta_directorio)
        print(f"Directorio creado: {ruta_directorio}")

    # Nombre fijo para el Excel
    nombre_excel_1 = "000094288371.xlsx"

    ############################################################################
    # Iniciar Playwright con la ventana minimizada y mejoras de stealth
    ############################################################################
    async with async_playwright() as p:
        # Se usa Chrome y se inicia la ventana minimizada
        browser = await p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--start-minimized"]
        )

        # Crear un nuevo contexto con un User-Agent real
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        # Inyectar script de stealth para modificar propiedades de navigator
        await context.add_init_script("""
            // Eliminar la propiedad webdriver para evitar la detección de automatización
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Simular plugins instalados
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            // Simular idiomas del navegador
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
        """)

        page = await context.new_page()

        ########################################################################
        # Navegar a la página de login y esperar
        ########################################################################
        await page.goto("https://empresas.officebanking.cl")
        await page.wait_for_timeout(5000)

        ########################################################################
        # Clic en "Ingresar" (forzado)
        ########################################################################
        try:
            await page.wait_for_selector("app-login-button:has-text('Ingresar')", timeout=10000)
            await page.wait_for_timeout(1000)
            await page.locator("app-login-button:has-text('Ingresar')").click(force=True)
            print("Clic en 'Ingresar' realizado.")
        except Exception as e:
            print(f"Error haciendo clic en 'Ingresar': {e}")
            await page.screenshot(path="error_ingresar.png")
            await browser.close()
            return

        await page.wait_for_timeout(5000)

        ########################################################################
        # Identificar si el login está en un iframe
        ########################################################################
        frame = None
        for f in page.frames:
            try:
                if await f.query_selector("#userInput"):
                    frame = f
                    print(f"Iframe encontrado para login: {f.name}, URL: {f.url}")
                    break
            except Exception:
                continue

        if not frame:
            frame = page
            print("No se encontró un iframe para login. Usando la página principal.")

        ########################################################################
        # Llenar RUT y clave
        ########################################################################
        try:
            await frame.wait_for_selector("#userInput", timeout=10000)
            await frame.fill("#userInput", "17109134-9")
            print("RUT llenado correctamente.")
        except Exception as e:
            print(f"Error llenando RUT: {e}")

        try:
            await frame.wait_for_selector("#userCodeInput", timeout=5000)
            await frame.fill("#userCodeInput", "Kj6m-86.")
            print("Clave llenada correctamente.")
        except Exception as e:
            print(f"Error llenando clave: {e}")

        ########################################################################
        # Clic en "Aceptar" (forzado)
        ########################################################################
        try:
            await frame.wait_for_selector("span:has-text('Aceptar')", timeout=5000)
            await frame.locator("span:has-text('Aceptar')").click(force=True)
            print("Clic en 'Aceptar' realizado.")
        except Exception as e:
            print(f"Error haciendo clic en 'Aceptar': {e}")

        await page.wait_for_timeout(5000)

        ########################################################################
        # Clic en "Cuentas Corrientes"
        ########################################################################
        try:
            await page.wait_for_selector("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]", timeout=5000)
            await page.click("xpath=(//span[contains(.,'Cuentas Corrientes')])[1]")
            print("Clic en 'Cuentas Corrientes' realizado correctamente.")
        except Exception as e:
            print(f"Error haciendo clic en 'Cuentas Corrientes': {e}")

        await page.wait_for_timeout(3000)

        ########################################################################
        # Clic en "Saldos y movimientos"
        ########################################################################
        try:
            await page.wait_for_selector(
                "xpath=(//a[@class='obLink'][contains(.,'Saldos y movimientos')])[2]",
                timeout=5000
            )
            await page.click("xpath=(//a[@class='obLink'][contains(.,'Saldos y movimientos')])[2]")
            print("Clic en 'Saldos y movimientos' realizado correctamente.")
        except Exception as e:
            print(f"Error haciendo clic en 'Saldos y movimientos': {e}")

        await page.wait_for_timeout(3000)

        ########################################################################
        # Acceder al iframe 'derecho' y hacer scroll final
        ########################################################################
        try:
            print("\n>>> Accediendo al iframe 'derecho'...")
            iframe_handle = page.frame(name="derecho")
            if not iframe_handle:
                print("No se encontró el iframe 'derecho'.")
                await browser.close()
                return

            print("Iframe 'derecho' encontrado.")
            await iframe_handle.wait_for_load_state("load")
            print("Contenido del iframe 'derecho' cargado.")

            print("Iniciando scroll hasta el final dentro del iframe 'derecho'...")
            await iframe_handle.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        const distance = 100;
                        const delay = 100;
                        const timer = setInterval(() => {
                            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
                            window.scrollBy(0, distance);
                            if (scrollTop + clientHeight >= scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, delay);
                    });
                }
            """)
            print("Scroll final dentro del iframe completado.")
            await iframe_handle.wait_for_timeout(2000)
        except Exception as e:
            print(f"Error accediendo al iframe 'derecho': {e}")
            await browser.close()
            return

        ########################################################################
        # Descargar PRIMER Excel con nombre fijo
        ########################################################################
        try:
            print("\n>>> Interactuando con el iframe 'derecho' para descargar el PRIMER Excel...")
            if not iframe_handle:
                print("Iframe 'derecho' no está disponible.")
                raise Exception("Iframe 'derecho' no encontrado.")

            descargar_xpath = "//section[@id='3']//a[@class='wrapper-descarga-link'][normalize-space()='Descargar']"

            # Hacer hover en el botón "Descargar"
            await iframe_handle.hover(descargar_xpath)
            print(f"Hover realizado sobre 'Descargar' usando el XPath: {descargar_xpath}")
            await iframe_handle.wait_for_timeout(1500)

            # Apuntar al enlace "Excel"
            excel_xpath = "(//a[contains(.,'Excel')])[2]"
            await iframe_handle.wait_for_selector(excel_xpath, state="visible", timeout=15000)
            print(f"Enlace 'Excel' visible usando el XPath: {excel_xpath}")

            # Desplazar hacia la vista y forzar clic para descargar
            await iframe_handle.locator(excel_xpath).scroll_into_view_if_needed()

            async with page.expect_download() as download_info:
                await iframe_handle.click(excel_xpath, force=True)
            download = await download_info.value

            ruta_descarga_excel_1 = os.path.join(ruta_directorio, nombre_excel_1)
            await download.save_as(ruta_descarga_excel_1)
            print(f"Descarga del Excel completada y guardada en: {ruta_descarga_excel_1}")
        except Exception as e:
            print(f"Error al descargar el Excel: {e}")

        ########################################################################
        # Finalizar el flujo
        ########################################################################
        print("\n>>> Finalizando flujo. Cerrando el navegador.")
        await browser.close()

################################################################################
# Ejecutar el flujo cada 20 minutos (en este caso, cada 2 horas)
################################################################################
def run_script_every_20_minutes():
    """
    Ejecuta 'run_flow_once()' cada 20 minutos (o cada 2 horas, según el sleep)
    de forma indefinida. Presiona Ctrl+C para interrumpir.
    """
    while True:
        try:
            asyncio.run(run_flow_once())
            # Ejecutar Santander.py después de cada ejecución exitosa
            print("\n>>> Ejecutando Santander.py...")
            subprocess.run(["python", "Santander.py"])
        except Exception as e:
            print(f"Error en la ejecución del flujo: {e}")
        print("\n>>> Flujo completado. Esperando 20 minutos para la próxima ejecución...\n")
        time.sleep(7200)  # 7200 segundos = 2 horas

################################################################################
# Punto de entrada
################################################################################
if __name__ == "__main__":
    run_script_every_20_minutes()
