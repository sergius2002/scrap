# Scrap - Sistema de Automatización de Procesos

Este proyecto contiene scripts de automatización para diferentes procesos de scraping y procesamiento de datos.

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

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Git

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/sergius2002/scrap.git
cd scrap
```

2. Crear y activar un entorno virtual:
```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate
```

3. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar las variables de entorno:
   - Copiar el archivo `.env.example` a `.env`
   - Actualizar las variables en `.env` con tus credenciales

## Instalación con Docker

1. Asegúrate de tener Docker y Docker Compose instalados en tu sistema.

2. Clonar el repositorio:
```bash
git clone https://github.com/sergius2002/scrap.git
cd scrap
```

3. Configurar las variables de entorno:
   - Copiar el archivo `.env.example` a `.env`
   - Actualizar las variables en `.env` con tus credenciales

4. Construir y ejecutar el contenedor:
```bash
# Construir la imagen
docker-compose build

# Ejecutar el contenedor
docker-compose up
```

5. Para ejecutar un script específico:
```bash
# Scrap BCI
docker-compose run scrap python Scrap_bci.py

# Scrap Santander
docker-compose run scrap python Scrap_santander.py

# Scrap Santander CLA
docker-compose run scrap python Scrap_santander_cla.py
```

6. Para ver los logs:
```bash
docker-compose logs -f
```

## Estructura del Proyecto

- `Scrap_bci.py`: Script para scraping de BCI
- `Scrap_santander.py`: Script para scraping de Santander
- `Scrap_santander_cla.py`: Script alternativo para scraping de Santander
- `bci.py`: Módulo de procesamiento para BCI
- `santander.py`: Módulo de procesamiento para Santander
- `certificado/`: Directorio para archivos de certificados y credenciales
- `archivos/`: Directorio para archivos descargados y procesados

## Uso

### Scrap BCI
```bash
python Scrap_bci.py
```

### Scrap Santander
```bash
python Scrap_santander.py
```

### Scrap Santander CLA
```bash
python Scrap_santander_cla.py
```

## Configuración

El proyecto utiliza las siguientes variables de entorno (definidas en `.env`):

- `SUPABASE_URL`: URL de la base de datos Supabase
- `SUPABASE_KEY`: Clave de API de Supabase
- `SHEET_URL`: URL de la hoja de cálculo de Google
- `CARPETA_ARCHIVOS`: Ruta para almacenar archivos descargados
- `API_TOKEN_SAN_CRISTOBAL`: Token de API para San Cristóbal
- `API_TOKEN_ST_CRISTOBAL`: Token de API para St. Cristóbal
- `CREDENTIALS_PATH`: Ruta al archivo de credenciales de Google
- `TOKEN_PATH`: Ruta al archivo de token de Google

## Notas Importantes

- Los archivos de certificados y credenciales deben mantenerse seguros y no compartirse
- El directorio `.venv` no debe incluirse en el control de versiones
- Se recomienda mantener actualizado el archivo `requirements.txt`

## Contribución

1. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
2. Hacer commit de tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
3. Push a la rama (`git push origin feature/nueva-funcionalidad`)
4. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

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

## Soporte

Para problemas o consultas, contactar al administrador del sistema. 