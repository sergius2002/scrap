import asyncio
import datetime
import time
import sys
from pathlib import Path

# Agregar el directorio src al path
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from utils.logger import setup_logger, log_info, log_error
from scrapers.santander import run_santander_scraper
from scrapers.estado import run_estado_scraper
from scrapers.bci import run_bci_scraper

logger = setup_logger(__name__)

async def run_all_scrapers():
    """Ejecuta todos los scrapers en secuencia."""
    try:
        log_info(logger, "Iniciando ejecución de todos los scrapers")
        
        # Ejecutar scrapers en secuencia
        await run_santander_scraper()
        await run_estado_scraper()
        await run_bci_scraper()
        
        log_info(logger, "Ejecución de todos los scrapers completada exitosamente")
    except Exception as e:
        log_error(logger, e, {"context": "Ejecución de scrapers"})
        raise

def calculate_sleep_interval():
    """Calcula el intervalo de espera basado en la hora actual."""
    now = datetime.datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    if 480 <= current_minutes < 660:  # 8:00 - 11:00
        return 5 * 60  # 5 minutos
    elif 660 <= current_minutes <= 1080:  # 11:00 - 18:00
        return 20 * 60  # 20 minutos
    elif current_minutes >= 1081 or current_minutes == 0:  # 18:00 - 24:00
        return 5 * 60  # 5 minutos
    elif 1 <= current_minutes < 480:  # 0:00 - 8:00
        return 58 * 60  # 58 minutos
    else:
        return 5 * 60  # 5 minutos por defecto

async def main():
    """Función principal que ejecuta los scrapers en bucle."""
    while True:
        try:
            await run_all_scrapers()
            
            # Calcular y esperar el siguiente intervalo
            sleep_interval = calculate_sleep_interval()
            log_info(logger, f"Esperando {int(sleep_interval / 60)} minutos para la siguiente ejecución")
            time.sleep(sleep_interval)
            
        except Exception as e:
            log_error(logger, e, {"context": "Bucle principal"})
            # En caso de error, esperar 5 minutos antes de reintentar
            time.sleep(5 * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info(logger, "Programa detenido por el usuario")
    except Exception as e:
        log_error(logger, e, {"context": "Programa principal"})
        sys.exit(1) 