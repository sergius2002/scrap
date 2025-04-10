# Sistema de Scraping Automatizado

Este proyecto automatiza la extracción de datos de diferentes bancos y servicios financieros.

## Estructura del Proyecto

```
.
├── config.py              # Configuración centralizada
├── requirements.txt       # Dependencias del proyecto
├── src/                  # Código fuente
│   ├── scrapers/         # Scripts de scraping
│   ├── utils/            # Utilidades comunes
│   └── database/         # Conexión a bases de datos
├── output/               # Archivos de salida
│   ├── EXCEL_SANTANDER/  # Archivos Excel de Santander
│   └── Facturas/         # Facturas PDF
├── logs/                 # Archivos de log
└── certificado/          # Certificados y credenciales
```

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Playwright (para automatización web)

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd [NOMBRE_DEL_DIRECTORIO]
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Instalar los navegadores de Playwright:
```bash
playwright install
```

## Configuración

1. Copiar los certificados necesarios a la carpeta `certificado/`:
   - `lioren-446620-e63e8a6e22d4.json`
   - `token.json`

2. Verificar que las rutas en `config.py` sean correctas para tu sistema.

## Uso

Para ejecutar todos los scrapers:

```bash
python src/main.py
```

Para ejecutar un scraper específico:

```bash
python src/scrapers/santander.py
python src/scrapers/estado.py
python src/scrapers/bci.py
```

## Programación Automática

El sistema está configurado para ejecutarse automáticamente en diferentes intervalos según la hora del día:
- Durante horario laboral (8:00 - 18:00): cada 20 minutos
- Fuera de horario laboral: cada 5 minutos
- Durante la noche (0:00 - 8:00): cada 58 minutos

## Logs

Los logs se guardan en la carpeta `logs/` con el nombre `scraping.log`. Cada ejecución registra:
- Hora de inicio y fin
- Errores y advertencias
- Resultados de las operaciones

## Notas Importantes

- Mantener las credenciales y tokens seguros
- No compartir los archivos de certificados
- Verificar periódicamente los logs para detectar errores
- Mantener actualizadas las dependencias

## Soporte

Para problemas o consultas, contactar al administrador del sistema. 