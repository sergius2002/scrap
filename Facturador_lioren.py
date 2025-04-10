# --------------------------------------------------------------------------------
# Este script se mantiene en constante ejecución, revisando periódicamente la base
# de datos en busca de nuevas facturas pendientes. Al encontrar registros sin
# emitir, emite la factura vía API (Lioren) y lo envía por Gmail.
# --------------------------------------------------------------------------------

import os
import requests
import base64
import logging
from datetime import datetime, timedelta
import re
import time
import io  # Importa io para manejar el PDF en memoria
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from supabase import create_client, Client
from dotenv import load_dotenv  # Importa dotenv para cargar .env
import colorama
from colorama import Fore, Style

# Inicializar colorama
colorama.init()

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# ---------------------------
# Configuración de Logging
# ---------------------------
class ColoredFormatter(logging.Formatter):
    """Formateador personalizado para logs con colores"""
    
    def format(self, record):
        # Definir colores según el nivel
        colors = {
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Style.BRIGHT
        }
        
        # Aplicar color según el nivel
        color = colors.get(record.levelname, Fore.WHITE)
        
        # Formatear el mensaje
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        
        return super().format(record)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Formato personalizado para los logs
formatter = ColoredFormatter(
    f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler para archivo de log (sin colores)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
file_handler = logging.FileHandler('facturacion.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Handler para consola (con colores)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ---------------------------
# Configuración de Supabase y otras variables
# ---------------------------
# Obtener el directorio actual del script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta al certificado
CERTIFICADO_PATH = os.path.join(current_dir, "certificado", "lioren-446620-e63e8a6e22d4.json")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
SHEET_URL = os.getenv("SHEET_URL")
CARPETA_ARCHIVOS = os.getenv("CARPETA_ARCHIVOS")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TOKEN_PATH = os.getenv("TOKEN_PATH")
API_TOKEN_SAN_CRISTOBAL = os.getenv("API_TOKEN_SAN_CRISTOBAL")
API_TOKEN_ST_CRISTOBAL = os.getenv("API_TOKEN_ST_CRISTOBAL")

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

API_URL = "https://www.lioren.cl/api/dtes"

# ---------------------------
# Funciones Auxiliares
# ---------------------------

def es_fecha_valida(fecha_str: str) -> bool:
    patron = r'^\d{4}-\d{2}-\d{2}$'
    return re.match(patron, fecha_str) is not None

def formatear_fecha(fecha_str: str) -> str:
    try:
        # Intentar parsear fecha en formato ISO 8601
        dt = datetime.fromisoformat(fecha_str)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # Si falla, intentar con otros formatos
        formatos = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d"
        ]
        for fmt in formatos:
            try:
                dt = datetime.strptime(fecha_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # Si ninguno de los formatos coincide, retornar el original
        return fecha_str

def es_mediopago_valido(mediopago: int) -> bool:
    MEDIOPAGO_VALIDOS = [1, 2, 3, 4, 5]
    return mediopago in MEDIOPAGO_VALIDOS

def obtener_servicio_gmail():
    creds = None
    if os.path.exists(TOKEN_PATH):
        logger.info(f"Cargando credenciales existentes de: {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refrescando credenciales Gmail API...")
            creds.refresh(Request())
        else:
            logger.info("No hay credenciales válidas, abriendo flujo OAuth2.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("Autenticación completada.")
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            logger.info(f"Credenciales guardadas en: {TOKEN_PATH}")

    service = build("gmail", "v1", credentials=creds)
    return service

def crear_mensaje_con_pdf(destinatario, asunto, mensaje, pdf_bytes, pdf_nombre):
    mensaje_mime = MIMEMultipart()
    mensaje_mime["to"] = destinatario
    mensaje_mime["subject"] = asunto
    mensaje_mime.attach(MIMEText(mensaje, "plain", "utf-8"))

    if pdf_bytes:
        mime_part = MIMEBase("application", "octet-stream")
        mime_part.set_payload(pdf_bytes)
        encoders.encode_base64(mime_part)
        mime_part.add_header("Content-Disposition", f'attachment; filename="{pdf_nombre}"')
        mensaje_mime.attach(mime_part)
    else:
        logger.warning("No se proporcionaron bytes del PDF para adjuntar.")

    raw = base64.urlsafe_b64encode(mensaje_mime.as_bytes()).decode("utf-8")
    return {"raw": raw}

def enviar_mensaje_gmail(service, user_id, message):
    try:
        sent_msg = service.users().messages().send(userId=user_id, body=message).execute()
        logger.info(f"Mensaje enviado. ID: {sent_msg.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo: {e}")
        return False

def enviar_factura_email(destinatario, asunto, mensaje, pdf_bytes, pdf_nombre):
    service = obtener_servicio_gmail()
    msg = crear_mensaje_con_pdf(destinatario, asunto, mensaje, pdf_bytes, pdf_nombre)
    exito = enviar_mensaje_gmail(service, "me", msg)
    return exito

# ---------------------------
# Funciones de Supabase
# ---------------------------

def obtener_facturas_pendientes():
    try:
        # Se define el filtro de facturas sin enviar y de empresas específicas
        enviada = 0
        empresas = ["SAN CRISTOBAL SPA", "ST CRISTOBAL SPA"]
        # Filtro para facturas desde 3 días atrás
        fecha_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')

        logger.info(f"{Fore.CYAN}Consultando facturas:{Style.RESET_ALL}")
        logger.info(f"  • Enviada: {enviada}")
        logger.info(f"  • Empresas: {', '.join(empresas)}")
        logger.info(f"  • Fecha límite: {fecha_limite}")

        response = (
            supabase.table("transferencias")
            .select("hash, monto, rut, fecha, empresa, facturación")
            .eq("enviada", enviada)
            .eq("facturación", "empresa")
            .in_("empresa", empresas)
            .gte("fecha", fecha_limite)
            .execute()
        )

        if hasattr(response, 'error') and response.error:
            logger.error(f"Error al obtener facturas pendientes: {response.error}")
            return []

        facturas = response.data
        if facturas:
            logger.info(f"{Fore.GREEN}Se encontraron {len(facturas)} facturas pendientes:{Style.RESET_ALL}")
            for factura in facturas:
                logger.info(f"  • RUT: {factura['rut']} | Monto: ${factura['monto']:,} | Fecha: {factura['fecha']} | Empresa: {factura['empresa']}")
        else:
            logger.info(f"{Fore.YELLOW}No hay facturas pendientes.{Style.RESET_ALL}")
        return facturas
    except Exception as e:
        logger.error(f"Error al obtener facturas pendientes: {e}")
        return []

def actualizar_factura_enviada(hash_id):
    try:
        response = (
            supabase.table("transferencias")
            .update({"enviada": 1})
            .eq("hash", hash_id)
            .execute()
        )
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error al actualizar factura {hash_id}: {response.error}")
        else:
            logger.info(f"Factura con hash {hash_id} marcada como enviada.")
    except Exception as e:
        logger.error(f"Error al actualizar factura {hash_id}: {e}")

def obtener_datos_faltantes(rut):
    try:
        response = (
            supabase.table("datos_faltantes")
            .select("rs, email, direccion, comuna")
            .eq("rut", rut)
            .execute()
        )
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error al obtener datos faltantes para RUT {rut}: {response.error}")
            return {}
        datos = response.data
        if datos:
            return datos[0]
        else:
            logger.warning(f"No se encontraron datos faltantes para RUT {rut}.")
            return {}
    except Exception as e:
        logger.error(f"Error al obtener datos faltantes para RUT {rut}: {e}")
        return {}

# ---------------------------
# Función Principal
# ---------------------------

def procesar_facturas():
    ruts_excluidos = {"77773448-2", "77469173-1", "77936187-K","77218613-4"}
    try:
        facturas = obtener_facturas_pendientes()
        if not facturas:
            logger.info("No hay facturas pendientes.")
            return

        fecha_facturacion = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"\n{Fore.CYAN}Procesando facturas...{Style.RESET_ALL}")

        for factura in facturas:
            hash_id = factura['hash']
            monto = factura['monto']
            rut = factura['rut']
            fecha_detectada = factura['fecha']
            empresa = factura['empresa']
            facturacion = factura.get('facturación', '').lower()

            logger.info(f"\n{Fore.CYAN}Procesando factura:{Style.RESET_ALL}")
            logger.info(f"  • RUT: {rut}")
            logger.info(f"  • Monto: ${monto:,}")
            logger.info(f"  • Fecha: {fecha_detectada}")
            logger.info(f"  • Empresa: {empresa}")

            # Verificar que la fecha de la factura sea igual o posterior a 3 días atrás
            try:
                fecha_factura_dt = datetime.strptime(formatear_fecha(fecha_detectada), '%Y-%m-%d')
                fecha_inicio = datetime.now() - timedelta(days=3)
                if fecha_factura_dt < fecha_inicio:
                    logger.info(f"Factura con fecha {fecha_detectada} es anterior al {fecha_inicio.strftime('%Y-%m-%d')}. Se omite.")
                    continue
            except Exception as e:
                logger.error(f"Error al procesar fecha de la factura: {fecha_detectada}. Error: {e}")
                continue

            if rut.upper() in ruts_excluidos:
                logger.info(f"RUT {rut} está excluido. Marcando como enviada.")
                actualizar_factura_enviada(hash_id)
                continue

            # Verificación de que el RUT corresponde a una empresa
            if facturacion != 'empresa':
                logger.warning(f"RUT {rut} no es una empresa ({facturacion}). NO marcando como enviada.")
                continue

            datos_faltantes = obtener_datos_faltantes(rut)
            if not datos_faltantes:
                logger.error(f"Datos faltantes incompletos para RUT {rut}. NO marcando como enviada.")
                continue

            rs = datos_faltantes.get('rs', '')
            email = datos_faltantes.get('email', '')
            direccion = datos_faltantes.get('direccion', '')
            comuna_db = datos_faltantes.get('comuna', 0)
            try:
                comuna_value = int(comuna_db) if comuna_db else 295
            except ValueError:
                comuna_value = 295
                logger.warning(f"Comuna inválida '{comuna_db}' para RUT {rut}. Usando 295.")

            data = {
                "emisor": {
                    "tipodoc": "34",
                    "fecha": fecha_facturacion,
                    "email": "sergio.plaza.altamirano@gmail.com",
                    "telefono": "971073454",
                    "observaciones": "Factura exenta generada masivamente"
                },
                "receptor": {
                    "rut": rut,
                    "rs": rs,
                    "giro": "Edición de programas informáticos",
                    "comuna": comuna_value,
                    "ciudad": 176,
                    "direccion": direccion,
                    "email": email,
                    "telefono": "971073454"
                },
                "detalles": [
                    {
                        "codigo": "001",
                        "nombre": "Activo digital no corpóreo",
                        "cantidad": 1,
                        "precio": monto,
                        "exento": True
                    }
                ],
                "pagos": [
                    {
                        "fecha": fecha_facturacion,
                        "mediopago": 1,
                        "monto": monto,
                        "cobrar": False
                    }
                ],
                "expects": "all"
            }

            mediopago = data["pagos"][0]["mediopago"]
            if not es_mediopago_valido(mediopago):
                logger.error(f"Mediopago inválido para RUT {rut}. NO marcando como enviada.")
                continue

            # Seleccionar el token correcto según la empresa
            empresa_normalizada = empresa.strip().upper()
            if empresa_normalizada == "SAN CRISTOBAL SPA":
                token = API_TOKEN_SAN_CRISTOBAL
            elif empresa_normalizada == "ST CRISTOBAL SPA":
                token = API_TOKEN_ST_CRISTOBAL
            else:
                token = API_TOKEN_SAN_CRISTOBAL
                logger.warning(f"Empresa '{empresa}' no reconocida. Usando token SAN CRISTOBAL.")

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.post(API_URL, json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Factura exenta emitida OK para RUT {rut} ({empresa}).")
                # Marcar como enviada inmediatamente después de emitir la factura
                actualizar_factura_enviada(hash_id)

                pdf_base64 = response_data.get("pdf", None)
                if pdf_base64:
                    pdf_bytes = base64.b64decode(pdf_base64)
                    pdf_filename = f"{fecha_facturacion.replace('-', '')}_{rut}.pdf"
                    logger.info(f"Preparando para enviar PDF de {pdf_filename} por correo electrónico.")

                    try:
                        monto_int = int(float(monto))
                        formatted_monto = "${:,}".format(monto_int).replace(",", ".")
                    except ValueError:
                        formatted_monto = f"${monto}"

                    asunto_email = "Factura Emitida"
                    cuerpo_email = (
                        f"Estimado/a {rs},\n\n"
                        f"Adjuntamos la factura emitida con fecha {fecha_facturacion} "
                        f"por un monto de {formatted_monto}.\n\n"
                        f"Saludos,\nEquipo SAN CRISTOBAL"
                    )

                    if email and re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        exito = enviar_factura_email(email, asunto_email, cuerpo_email, pdf_bytes, pdf_filename)
                        if exito:
                            logger.info(f"Correo enviado a {email}, RUT {rut}.")
                        else:
                            logger.warning(f"Fallo al enviar correo a {email}, RUT {rut}.")
                    else:
                        logger.warning(f"Email inválido o vacío para RUT {rut}. NO enviando correo.")
                else:
                    logger.warning(f"No se recibió PDF para RUT {rut}.")
            else:
                logger.error(f"Error al emitir factura (status {response.status_code}) para RUT {rut}.")
                try:
                    logger.error(f"Detalle error: {response.json()}")
                except Exception:
                    logger.error("No se pudo parsear el error.")
    except Exception as e:
        logger.critical(f"Error crítico en procesar_facturas: {e}")

# ---------------------------
# Ejecución del Script
# ---------------------------

if __name__ == "__main__":
    logger.info(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}Iniciando monitoreo facturas lioren{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}Presione CTRL+C para salir{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
    
    try:
        while True:
            procesar_facturas()
            logger.info(f"\n{Fore.CYAN}Esperando 10 minutos para la siguiente revisión...{Style.RESET_ALL}\n")
            time.sleep(36000)
    except KeyboardInterrupt:
        logger.info(f"\n{Fore.YELLOW}Proceso detenido por usuario.{Style.RESET_ALL}")
    except Exception as e:
        logger.critical(f"\n{Fore.RED}Proceso detenido por error inesperado: {e}{Style.RESET_ALL}")