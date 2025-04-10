import os
from pathlib import Path

# Configuración de rutas base
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CERTIFICATES_DIR = BASE_DIR / "certificado"

# Crear directorios si no existen
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
CERTIFICATES_DIR.mkdir(exist_ok=True)

# Configuración de Supabase
SUPABASE_CONFIG = {
    "url": "https://tmimwpzxmtezopieqzcl.supabase.co",
    "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"
}

# Configuración de Google Sheets
SHEETS_CONFIG = {
    "url": "https://docs.google.com/spreadsheets/d/1PX-GBjpNvv3LQaTkRMr_9MTvnwYaJPxAFM-7c-2s/edit?gid=0"
}

# Configuración de rutas de certificados
CREDENTIALS_PATHS = {
    "google": str(CERTIFICATES_DIR / "lioren-446620-e63e8a6e22d4.json"),
    "token": str(CERTIFICATES_DIR / "token.json")
}

# Configuración de directorios de salida
OUTPUT_PATHS = {
    "santander": str(OUTPUT_DIR / "EXCEL_SANTANDER"),
    "pdf": str(OUTPUT_DIR / "Facturas")
}

# Configuración de tokens de API
API_TOKENS = {
    "san_cristobal": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5ODMiLCJqdGkiOiI2MmM4MzgxOGQ1YjM3YjAwNDUyMDM4OTMzNDM4MjEzMGFhYjdmNmVlY2JjMmIwZjZhNjZmODFlNzc2NDJhYTkzZDk4MzE0ZTFiM2Y3Y2UwMCIsImlhdCI6MTczNjQ0NDYwNC4xMDI5NTYsIm5iZiI6MTczNjQ0NDYwNC4xMDI5NTgsImV4cCI6MTc2Nzk4MDYwNC4wOTg0OSwic3ViIjoiODA5MyIsInNjb3BlcyI6W119.P5tb-TZ-y2HMtxKs67V-lH-NTmHBYfMePHGVaHtqzpXXCPBqMBi2mWyqsjVA59jDOJI-3gXzp-OzryXB6XhxP8E6wElyhPW_eBKFqKApgwcIzYMRYfNqbLRJRK6OD8Wia3PM_CAYFIZ92WDMkk6vYVW5cX4JkQkHlL5T-9iaLw_I29h_NSrgX80BXmc7s4WwPg7_SZTF6pilc07edvB9eYNqRcmmGb-o6YuKAZY3LWQM3I0qzjRSgBx7u4QNsYxksRsMQp-2tnSv-HJNThR4yeq8GyFKuMr7BIbHj08HnskzzbZLMFTw8KlZTLSX7tj_0qwasA_nua-nR29ePPIH7aYoTPS2dZYOa2QRu6ZkTu4Yu5hzNoFXIRAVo8VZjlWQ_FmX1wf8fTsr43FtG-0GdUTNjsXRVknkVTOIlEZ4otIYm8y6rLUM5Y9J2urEr_qSpdsOyt50CjvvQiMPKazKCR03gwxwZenfpfYFP5cl3lni3RcXfVttsio44kxaFcfYKckjOF2OkeSsKMpVIUiZu3Jih-1QlMqDmGoVghiMNJYAuAPh5kH13DWydnemqRjYqO7yU3iokwQPStg1TzFf4ktK044iaRz1qGyZBjYgPEZMVsBmkLe4Ky5HcVy-_l5OoZKuZ8LKjPtEHshshZyRavU6C7AAwzxtci0LKYIM6QY",
    "st_cristobal": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5ODMiLCJqdGkiOiI2MmM4MzgxOGQ1YjM3YjAwNDUyMDM4OTMzNDM4MjEzMGFhYjdmNmVlY2JjMmIwZjZhNjZmODFlNzc2NDJhYTkzZDk4MzE0ZTFiM2Y3Y2UwMCIsImlhdCI6MTczNjQ0NDYwNC4xMDI5NTYsIm5iZiI6MTczNjQ0NDYwNC4xMDI5NTgsImV4cCI6MTc2Nzk4MDYwNC4wOTg0OSwic3ViIjoiODA5MyIsInNjb3BlcyI6W119.P5tb-TZ-y2HMtxKs67V-lH-NTmHBYfMePHGVaHtqzpXXCPBqMBi2mWyqsjVA59jDOJI-3gXzp-OzryXB6XhxP8E6wElyhPW_eBKFqKApgwcIzYMRYfNqbLRJRK6OD8Wia3PM_CAYFIZ92WDMkk6vYVW5cX4JkQkHlL5T-9iaLw_I29h_NSrgX80BXmc7s4WwPg7_SZTF6pilc07edvB9eYNqRcmmGb-o6YuKAZY3LWQM3I0qzjRSgBx7u4QNsYxksRsMQp-2tnSv-HJNThR4yeq8GyFKuMr7BIbHj08HnskzzbZLMFTw8KlZTLSX7tj_0qwasA_nua-nR29ePPIH7aYoTPS2dZYOa2QRu6ZkTu4Yu5hzNoFXIRAVo8VZjlWQ_FmX1wf8fTsr43FtG-0GdUTNjsXRVknkVTOIlEZ4otIYm8y6rLUM5Y9J2urEr_qSpdsOyt50CjvvQiMPKazKCR03gwxwZenfpfYFP5cl3lni3RcXfVttsio44kxaFcfYKckjOF2OkeSsKMpVIUiZu3Jih-1QlMqDmGoVghiMNJYAuAPh5kH13DWydnemqRjYqO7yU3iokwQPStg1TzFf4ktK044iaRz1qGyZBjYgPEZMVsBmkLe4Ky5HcVy-_l5OoZKuZ8LKjPtEHshshZyRavU6C7AAwzxtci0LKYIM6QY"
}

# Configuración de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(LOGS_DIR / "scraping.log"),
            "mode": "a"
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True
        }
    }
}