import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import os
import sys
import time
import datetime
import subprocess

async def fill_input(frame, selector, text):
    """Rellena un campo de entrada en el frame especificado."""
    await frame.click(selector)
    await frame.fill(selector, "")
    await frame.type(selector, text, delay=100)  # Simula tipeo humano

async def get_target_frame(page):
    """Obtiene un frame cuyo URL contenga 'bancoestado.cl' o retorna None."""
    frames = page.frames
    for frame in frames:
        if "bancoestado.cl" in frame.url:
            print(f"Frame objetivo encontrado: {frame.url}")
            return frame
    print("No se encontró el frame objetivo.")
    return None

async def process_login(page, rut, password):
    """Procesa el ingreso del RUT y clave en la página de BancoEstado."""
    try:
        print("Navegando a la página de BancoEstado...")
        await page.goto(
            "https://www.bancoestado.cl/content/bancoestado-public/cl/es/home/home/productos-/cuentas/cuentarut.html#/login",
            wait_until="networkidle")
        await page.wait_for_load_state("networkidle")

        target_frame = await get_target_frame(page)
        if not target_frame:
            print("No se encontró el frame de login.")
            return False

        print("Rellenando el campo RUT...")
        await target_frame.wait_for_selector("input#rut", state="visible", timeout=7000)
        await fill_input(target_frame, "input#rut", rut)
        print(f"RUT {rut} ingresado exitosamente")

        print("Rellenando el campo Clave...")
        await target_frame.wait_for_selector("input#pass", state="visible", timeout=7000)
        await fill_input(target_frame, "input#pass", password)
        print("Clave ingresada exitosamente")

        print("Haciendo clic en el botón Ingresar...")
        await target_frame.wait_for_selector("button#btnLogin", state="visible", timeout=7000)
        await target_frame.click("button#btnLogin")
        print("Botón Ingresar presionado")
        
        return True

    except Exception as e:
        print(f"Error durante el proceso: {e}")
        return False

async def main():
    rut = "269983663"  # RUT proporcionado
    password = "Kj6mm866"  # Clave proporcionada

    while True:  # Bucle infinito
        print(f"\nIniciando nuevo ciclo a las {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False,  # Navegador visible
                                          args=["--disable-blink-features=AutomationControlled"])
            context_browser = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                accept_downloads=True
            )
            page = await context_browser.new_page()

            # Configurar el navegador para evitar detección
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

            try:
                # Minimizar la ventana del navegador usando osascript
                subprocess.run(['osascript', '-e', 'tell application "System Events" to set visible of process "Chromium" to false'])
                
                success = await process_login(page, rut, password)
                if success:
                    print("Proceso completado exitosamente")
                else:
                    print("No se pudo completar el proceso")

            except Exception as e:
                print(f"Error en el proceso principal: {e}")

            finally:
                await browser.close()
                
        # Esperar 10 segundos antes del siguiente ciclo
        print("Esperando 10 segundos para el siguiente ciclo...")
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main()) 