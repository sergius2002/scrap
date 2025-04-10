import asyncio
import re
import datetime
import hashlib
import subprocess
import sys
import time
import os
import shutil
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from openpyxl import Workbook
import pandas as pd


# --------------------------
# Funciones Auxiliares
# --------------------------

async def fill_input(frame, selector, text):
    """Rellena un campo de entrada en el frame especificado."""
    await frame.click(selector)
    await frame.fill(selector, "")
    await frame.type(selector, text, delay=100)  # Simula tipeo humano


async def click_with_retries(page, frame, selector, max_retries=3):
    """Intenta hacer clic en un elemento con varios reintentos."""
    for attempt in range(max_retries):
        try:
            if not frame.is_detached():
                await frame.wait_for_selector(selector, state="visible", timeout=7000)
                await frame.hover(selector)
                await frame.click(selector)
                print(f"Click en '{selector}' exitoso en el intento {attempt + 1}")
                return
            else:
                print("El frame fue desvinculado. Reintentando obtener el frame...")
                frame = await get_target_frame(page)
                if not frame:
                    raise Exception("No se pudo obtener el frame luego de que fue desvinculado.")
        except PlaywrightTimeoutError:
            print(f"Intento {attempt + 1} fallido al hacer clic en '{selector}': Timeout.")
        except Exception as e:
            print(f"Intento {attempt + 1} fallido al hacer clic en '{selector}': {e}")
        await asyncio.sleep(1)
    raise Exception(f"No se pudo hacer clic en '{selector}' tras {max_retries} intentos.")


async def get_target_frame(page):
    """Obtiene un frame cuyo URL contenga 'appempresas.bancoestado.cl' o retorna None."""
    frames = page.frames
    for frame in frames:
        if re.search(r"appempresas\.bancoestado\.cl", frame.url):
            print(f"Frame objetivo encontrado: {frame.url}")
            return frame
    print("No se encontró el frame objetivo.")
    return None


async def find_and_click(context, selector):
    """Busca y hace clic en un elemento en el contexto dado (Page o Frame)."""
    try:
        if await context.is_visible(selector):
            await context.hover(selector)
            await context.click(selector)
            print(f"Click en '{selector}' exitoso en el contexto dado.")
            return True
    except Exception as e:
        print(f"Error al intentar clic en '{selector}' en el contexto dado: {e}")
    return False


async def extract_transfers(iframe):
    """Extrae datos de la tabla de Transferencias Recibidas en la página actual."""
    try:
        await iframe.wait_for_selector("table.table__container", state="visible", timeout=15000)
        print("Tabla encontrada, extrayendo datos...")
    except PlaywrightTimeoutError:
        print("No se encontró la tabla de transferencias.")
        return []

    table = await iframe.query_selector("table.table__container")
    if not table:
        print("Tabla de transferencias no encontrada.")
        return []

    rows = await table.query_selector_all("tbody tr")
    transfers = []
    print(f"Se encontraron {len(rows)} filas en la tabla")
    
    for row in rows:
        cols = await row.query_selector_all("td")
        if len(cols) < 7:
            continue
            
        try:
            num_operacion = (await cols[0].inner_text()).strip()
            fecha_hora = (await cols[1].inner_text()).strip()
            cuenta_destino = (await cols[2].inner_text()).strip()
            rut_origen = (await cols[3].inner_text()).strip()
            cuenta_origen = (await cols[4].inner_text()).strip()
            nombre_origen = (await cols[5].inner_text()).strip()
            monto = (await cols[6].inner_text()).strip()
            
            # Limpiar el monto
            monto = monto.replace("$", "").replace(".", "").replace(" ", "").strip()
            
            transfer = {
                "N° Operación": num_operacion,
                "Fecha - Hora": fecha_hora,
                "Cuenta Destino": cuenta_destino,
                "Rut Origen": rut_origen,
                "Cuenta Origen": cuenta_origen,
                "Nombre Origen": nombre_origen,
                "Monto": monto
            }
            transfers.append(transfer)
            print(f"Transferencia extraída: {num_operacion} - {monto}")
            
        except Exception as e:
            print(f"Error al procesar una fila: {e}")
            continue
            
    return transfers


async def extract_all_transfers(iframe):
    """Extrae datos de todas las páginas de la tabla de Transferencias Recibidas."""
    all_transfers = []
    page_num = 1
    previous_first_op = None

    while True:
        print(f"\nExtrayendo datos de la página {page_num}...")
        transfers = await extract_transfers(iframe)
        if not transfers:
            print("No se encontraron transferencias en esta página, finalizando paginación.")
            break

        current_first_op = transfers[0].get("N° Operación", "")
        if previous_first_op is not None and current_first_op == previous_first_op:
            print("El contenido de la tabla no ha cambiado. Fin de la paginación.")
            break

        previous_first_op = current_first_op
        print(f"Se extrajeron {len(transfers)} transferencias en la página {page_num}")
        all_transfers.extend(transfers)

        try:
            next_button = iframe.locator("(//div[contains(.,'Siguiente')])[15]")
            if await next_button.count() == 0:
                print("No se encontró el botón 'Siguiente'. Fin de la paginación.")
                break

            await next_button.scroll_into_view_if_needed()
            await next_button.wait_for(state="visible", timeout=5000)

            disabled_attr = await next_button.get_attribute("disabled")
            if disabled_attr is not None:
                print("El botón 'Siguiente' está deshabilitado. Fin de la paginación.")
                break

            print("Avanzando a la siguiente página...")
            await next_button.click()
            await iframe.wait_for_timeout(3000)
            page_num += 1
        except Exception as e:
            print(f"No se pudo avanzar a la siguiente página: {e}")
            break

    print(f"Total de transferencias extraídas: {len(all_transfers)}")
    return all_transfers


def export_to_excel(transfers, filename="transferencias_combinadas.xlsx"):
    """Transforma y exporta la lista de transferencias a un archivo Excel."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Transferencias"

        headers = ["N° Operación", "fecha_detec", "fecha", "rs", "rut", "monto", "facturación", "empresa", "hash", "cuenta"]
        ws.append(headers)

        for transfer in transfers:
            try:
                op = str(transfer.get("N° Operación", "")).strip()
                fecha_detec = str(transfer.get("Fecha - Hora", "")).strip()
                try:
                    fecha_part = fecha_detec.split(" ")[0]
                    fecha_obj = datetime.datetime.strptime(fecha_part, "%d/%m/%Y")
                    fecha = fecha_obj.strftime("%Y-%m-%d")
                except Exception:
                    fecha = ""
                rs = str(transfer.get("Nombre Origen", "")).strip()
                rut_raw = str(transfer.get("Rut Origen", ""))
                rut = rut_raw.replace(" ", "").replace(".", "").strip()
                monto_raw = str(transfer.get("Monto", "")).strip()
                try:
                    monto_clean = monto_raw.replace("$", "").replace(".", "").replace(" ", "").replace(",", "")
                    monto = int(monto_clean)
                except Exception:
                    monto = 0
                try:
                    rut_num_str = rut.split("-")[0]
                    rut_num = int(rut_num_str)
                    facturacion = "empresa" if rut_num > 50000000 else "persona"
                except Exception:
                    facturacion = ""
                
                # Asignar empresa basada en el RUT de la empresa
                rut_empresa = str(transfer.get("rut_empresa", "")).strip()
                empresa = ""
                if rut_empresa == "774691731":
                    empresa = "STS CRISTOBAL"
                elif rut_empresa == "777734482":
                    empresa = "DETAL"
                elif rut_empresa == "77936187K":
                    empresa = "ST CRISTOBAL ESTADO"
                
                hash_input = f"{int(op)}{fecha_detec}{int(monto)}{rut}{empresa}{rs}"
                hash_md5 = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
                cuenta = str(transfer.get("cuenta", "")).strip()

                row = [op, fecha_detec, fecha, rs, rut, monto, facturacion, empresa, hash_md5, cuenta]
                ws.append(row)
            except Exception as e:
                print(f"Error al procesar transferencia: {e}")
                continue

        # Crear directorio para los archivos si no existe
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar el archivo en el directorio de salida
        file_path = os.path.join(output_dir, filename)
        wb.save(file_path)
        print(f"Archivo Excel guardado en: {file_path}")
        print(f"Total de transferencias guardadas: {len(transfers)}")
    except Exception as e:
        print(f"Error al guardar el archivo Excel: {e}")


# --------------------------
# Procesamiento de Cuenta
# --------------------------

async def process_account(account, p):
    """Procesa una cuenta: inicia sesión, extrae información y cierra sesión."""
    browser = None
    context_browser = None
    page = None
    account_transfers = []

    try:
        browser = await p.chromium.launch(headless=False,
                                      args=["--disable-blink-features=AutomationControlled", "--start-maximized"])
        context_browser = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        page = await context_browser.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            Object.defineProperty(navigator, 'oscpu', { get: () => 'Windows NT 10.0; Win64; x64' });
            Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)

        print("Navegando a la página de login de BancoEstado Empresas...")
        await page.goto(
            "https://www.bancoestado.cl/content/bancoestado-public/cl/es/home/inicio---bancoestado-empresas.html#/login-empresa",
            wait_until="networkidle")
        await page.wait_for_load_state("networkidle")

        target_frame = await get_target_frame(page)
        if not target_frame:
            print("No se encontró el frame de login.")
            return account_transfers

        print("Rellenando el campo RUT de la Empresa...")
        await target_frame.wait_for_selector("input#rutEmpresa", state="visible", timeout=7000)
        await fill_input(target_frame, "input#rutEmpresa", account["rutEmpresa"])

        print("Rellenando el campo RUT de la Persona...")
        await target_frame.wait_for_selector("input#rutPersona", state="visible", timeout=7000)
        await fill_input(target_frame, "input#rutPersona", account["rutPersona"])

        print("Rellenando el campo Contraseña...")
        await target_frame.wait_for_selector("input#idPassword", state="visible", timeout=7000)
        await fill_input(target_frame, "input#idPassword", account["password"])

        print("Haciendo clic en el botón de inicio de sesión...")
        await click_with_retries(page, target_frame, "button.dsd-button.primary")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)

        print("Haciendo clic en 'Transferencias'...")
        transferencias_xpath = "//body/be-root/div[@class='app-home']/div[@class='ng-star-inserted']/div[@class='container-home']/div[@class='asd-container-sidebar']/be-menu/asd-menu-sidebar/div[@class='menu-sidebar-home ng-star-inserted']/nav[@class='menu-sidebar-home__content']/ul[@class='link_list']/li[2]/a[1]"
        await page.wait_for_selector(transferencias_xpath, state="visible", timeout=15000)
        await page.click(transferencias_xpath)
        await asyncio.sleep(3)

        print("Haciendo clic en 'Consultar'...")
        consultar_xpath = "//div[@class='asd-container-sidebar']//ul[@id='Transferencias']//div[@class='submenu-link-name'][normalize-space()='Consultar']"
        await page.wait_for_selector(consultar_xpath, state="visible", timeout=15000)
        await page.click(consultar_xpath)
        await asyncio.sleep(3)

        print("Cambiando al iframe de consultas-transferencias...")
        iframes = page.frames
        iframe = next((frame for frame in iframes if "consultas-transferencias-pj-app" in frame.url), None)
        if not iframe:
            print("No se encontró el iframe de consultas-transferencias")
            return account_transfers

        print("Haciendo clic en 'Recibidas'...")
        await iframe.wait_for_selector('li:has-text("Recibidas")', state="visible", timeout=15000)
        await iframe.click('li:has-text("Recibidas")')
        await asyncio.sleep(3)

        print("Calculando rango de fechas...")
        fecha_final = datetime.datetime.now()
        fecha_inicial = fecha_final - datetime.timedelta(days=5)
        
        print("Ingresando fechas...")
        fecha_inicial_str = fecha_inicial.strftime("%d/%m/%Y")
        fecha_final_str = fecha_final.strftime("%d/%m/%Y")
        
        try:
            # Esperar a que el formulario esté disponible
            await iframe.wait_for_selector('form', state="visible", timeout=10000)
            await asyncio.sleep(5)  # Dar más tiempo para que todo cargue
            
            # Intentar ingresar fecha inicial
            try:
                print("Intentando ingresar fecha inicial...")
                # Esperar y hacer clic en el primer campo de fecha
                await iframe.wait_for_selector('dsd-datepicker-only input[type="text"]', state="visible", timeout=10000)
                await iframe.click('dsd-datepicker-only input[type="text"]')
                await asyncio.sleep(2)
                
                # Limpiar y escribir la fecha
                await iframe.fill('dsd-datepicker-only input[type="text"]', "")
                await asyncio.sleep(1)
                await iframe.type('dsd-datepicker-only input[type="text"]', fecha_inicial_str, delay=100)
                await asyncio.sleep(2)
                
                # Presionar Tab para mover el foco al siguiente campo
                await page.keyboard.press('Tab')
                await asyncio.sleep(1)
                
                # Escribir la fecha final directamente
                fecha_final_ddmmyyyy = fecha_final.strftime("%d%m%Y")
                await page.keyboard.type(fecha_final_ddmmyyyy, delay=100)
                await asyncio.sleep(2)
                
                print("Fechas ingresadas exitosamente")
            except Exception as e:
                print(f"Error al ingresar fechas: {e}")
                return account_transfers
            
            await asyncio.sleep(3)  # Esperar a que los cambios se apliquen
            
        except Exception as e:
            print(f"Error general al intentar ingresar fechas: {e}")
            return account_transfers
            
        print("Haciendo clic en el botón 'Consultar'...")
        await iframe.click('button:has-text("Consultar")')
        await asyncio.sleep(5)

        print("Seleccionando 200 registros por página...")
        try:
            # Esperar a que el select esté visible
            await iframe.wait_for_selector('select[name="select"]', state="visible", timeout=10000)
            print("Select encontrado, intentando seleccionar 200 registros...")
            
            # Seleccionar la opción 200
            await iframe.select_option('select[name="select"]', "200")
            print("200 registros seleccionados exitosamente")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error al seleccionar 200 registros: {e}")
            return account_transfers

        print("Extrayendo datos de la tabla...")
        try:
            # Esperar a que la tabla esté visible en el iframe
            await iframe.wait_for_selector("table.table__container", state="visible", timeout=10000)
            await asyncio.sleep(5)  # Dar tiempo extra para que todo cargue
            
            # Extraer todas las transferencias
            account_transfers = await extract_all_transfers(iframe)
            
            # Agregar el RUT de la empresa a cada transferencia
            for transfer in account_transfers:
                transfer["rut_empresa"] = account["rutEmpresa"]
            
            if account_transfers:
                print(f"Se extrajeron {len(account_transfers)} transferencias exitosamente")
                # Generar nombre de archivo basado en el RUT de la empresa
                filename = f"transferencias_{account['rutEmpresa']}.xlsx"
                # Guardar en Excel
                export_to_excel(account_transfers, filename)
            else:
                print("No se encontraron transferencias para extraer")
                
        except Exception as e:
            print(f"Error al extraer datos de la tabla: {e}")
            return account_transfers

        print("Cerrando sesión...")
        try:
            # Primero intentar cerrar sesión desde el iframe
            try:
                await iframe.wait_for_selector("button:has-text('Cerrar Sesión')", state="visible", timeout=10000)
                await iframe.click("button:has-text('Cerrar Sesión')")
                await asyncio.sleep(3)
                
                # Verificar si hay diálogo de confirmación en el iframe
                try:
                    confirm_button = await iframe.wait_for_selector("button:has-text('Confirmar')", timeout=5000)
                    if confirm_button:
                        await iframe.click("button:has-text('Confirmar')")
                        await asyncio.sleep(2)
                except:
                    pass
            except Exception as e:
                print(f"No se pudo cerrar sesión desde el iframe: {e}")
            
            # Si no se pudo desde el iframe, intentar desde la página principal
            try:
                await page.wait_for_selector("button:has-text('Cerrar Sesión')", state="visible", timeout=10000)
                await page.click("button:has-text('Cerrar Sesión')")
                await asyncio.sleep(3)
                
                # Verificar si hay diálogo de confirmación en la página principal
                try:
                    confirm_button = await page.wait_for_selector("button:has-text('Confirmar')", timeout=5000)
                    if confirm_button:
                        await page.click("button:has-text('Confirmar')")
                        await asyncio.sleep(2)
                except:
                    pass
            except Exception as e:
                print(f"No se pudo cerrar sesión desde la página principal: {e}")
            
            # Esperar un momento para asegurar que la sesión se cierre
            await asyncio.sleep(5)
            print("Sesión cerrada exitosamente")
            
        except Exception as e:
            print(f"Error al cerrar sesión: {e}")
        finally:
            # Asegurarse de que el navegador se cierre
            try:
                await browser.close()
            except Exception as e:
                print(f"Error al cerrar el navegador: {e}")
            return account_transfers

    except Exception as e:
        print(f"Error al procesar la cuenta {account['rutEmpresa']}: {e}")
        return account_transfers

    finally:
        # Cierre de sesión y limpieza de recursos
        try:
            if page:
                print(f"Cerrando sesión para la cuenta {account['rutEmpresa']}...")
                try:
                    # Intentar hacer clic en el botón de cerrar sesión
                    await page.click("dsd-button-icon button")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"No se pudo hacer clic en el botón de cerrar sesión: {e}")
                
                # Cerrar la página
                await page.close()
                print(f"Página cerrada para la cuenta {account['rutEmpresa']}")

            if context_browser:
                await context_browser.close()
                print(f"Contexto del navegador cerrado para la cuenta {account['rutEmpresa']}")

            if browser:
                await browser.close()
                print(f"Navegador cerrado para la cuenta {account['rutEmpresa']}")

        except Exception as e:
            print(f"Error durante el cierre de sesión para la cuenta {account['rutEmpresa']}: {e}")

    return account_transfers


# --------------------------
# Función Principal
# --------------------------

async def main():
    # Lista de cuentas a procesar
    accounts = [
        {"rutEmpresa": "774691731", "rutPersona": "156089753", "password": "Kj6mm866"},
        {"rutEmpresa": "777734482", "rutPersona": "156089753", "password": "Kj6mm866"},
        {"rutEmpresa": "77936187K", "rutPersona": "171091349", "password": "Kj6mm866"}
    ]
    
    async with async_playwright() as p:
        # Procesar todas las cuentas simultáneamente
        results = await asyncio.gather(*[process_account(account, p) for account in accounts])

    # Combinar todas las transferencias para el archivo combinado
    aggregated_transfers = []
    for account_transfers in results:
        aggregated_transfers.extend(account_transfers)
    
    # Guardar todas las transferencias en un archivo Excel combinado
    if aggregated_transfers:
        export_to_excel(aggregated_transfers, "transferencias_combinadas.xlsx")
        print(f"Archivo Excel 'transferencias_combinadas.xlsx' guardado exitosamente con {len(aggregated_transfers)} transferencias en total.")
        
        # Ejecutar estado.py para subir los datos a Supabase
        print("\nIniciando subida de datos a Supabase...")
        try:
            # Obtener la ruta absoluta del directorio del script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Obtener la ruta absoluta de estado.py
            estado_script = os.path.join(script_dir, "estado.py")
            
            # Verificar que el archivo existe
            if not os.path.exists(estado_script):
                print(f"Error: No se encontró el archivo estado.py en: {estado_script}")
                return
                
            print(f"Ejecutando estado.py desde: {estado_script}")
            
            # Cambiar al directorio del script antes de ejecutar estado.py
            original_dir = os.getcwd()
            os.chdir(script_dir)
            
            # Ejecutar estado.py
            subprocess.run([sys.executable, estado_script], check=True)
            print("Proceso completado exitosamente.")
            
            # Volver al directorio original
            os.chdir(original_dir)
            
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar estado.py: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        finally:
            # Asegurarse de volver al directorio original incluso si hay errores
            try:
                os.chdir(original_dir)
            except:
                pass


# --------------------------
# Ejecución con Scheduling
# --------------------------

if __name__ == "__main__":
    # Asegurarse de que el directorio de trabajo sea el correcto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    while True:
        asyncio.run(main())
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute
        if 480 <= current_minutes < 660:
            sleep_interval = 5 * 60
        elif 660 <= current_minutes <= 1080:
            sleep_interval = 20 * 60
        elif current_minutes >= 1081 or current_minutes == 0:
            sleep_interval = 5 * 60
        elif 1 <= current_minutes < 480:
            sleep_interval = 58 * 60
        else:
            sleep_interval = 5 * 60
        print(f"Esperando {int(sleep_interval / 60)} minutos para la siguiente ejecución...")
        time.sleep(sleep_interval)