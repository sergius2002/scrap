#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import psutil
import logging
from datetime import datetime
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    filename='supervisor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Obtener el directorio actual
current_dir = Path(__file__).parent.absolute()

# Scripts a monitorear
SCRIPTS = [
    "Scrap_bci.py",
    "Scrap_santander.py",
    "Scrap_santander_cla.py",
    "Scrap_estado.py",
    "Facturador_lioren.py"
]

def check_script(script_name):
    """Verifica si un script está en ejecución."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
            return True
    return False

def restart_script(script_name):
    """Reinicia un script."""
    try:
        logging.info(f"Reiniciando {script_name}")
        # Usar python3 explícitamente y el directorio actual
        subprocess.Popen(
            ["python3", str(current_dir / script_name)],
            cwd=str(current_dir)
        )
        return True
    except Exception as e:
        logging.error(f"Error al reiniciar {script_name}: {e}")
        return False

def cleanup_resources():
    """Limpia recursos no utilizados."""
    try:
        # Cerrar navegadores Chrome huérfanos
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                try:
                    proc.terminate()
                except:
                    pass
        logging.info("Recursos limpiados exitosamente")
    except Exception as e:
        logging.error(f"Error al limpiar recursos: {e}")

def main():
    logging.info("Iniciando supervisor de scripts...")
    
    # Iniciar todos los scripts al comienzo
    for script in SCRIPTS:
        if not check_script(script):
            logging.info(f"Iniciando {script} por primera vez")
            restart_script(script)
    
    last_cleanup = datetime.now()
    
    while True:
        try:
            current_time = datetime.now()
            
            # Verificar cada script
            for script in SCRIPTS:
                if not check_script(script):
                    logging.warning(f"{script} no está en ejecución")
                    restart_script(script)
            
            # Limpiar recursos cada hora
            if (current_time - last_cleanup).total_seconds() >= 3600:
                cleanup_resources()
                last_cleanup = current_time
            
            time.sleep(60)  # Verificar cada minuto
            
        except Exception as e:
            logging.error(f"Error en el supervisor: {e}")
            time.sleep(300)  # Esperar 5 minutos en caso de error

if __name__ == "__main__":
    main() 