import os
import hashlib
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Cargar las variables de entorno (Supabase, si las tienes en .env)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Instanciar cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Definir los RUTs que no deben subirse a la base de datos
RUTS_A_ELIMINAR = [
    "77773448-2",
    "77469173-1",
    "77936187-K"
]

def normalizar_fecha(fecha_str):
    """
    Normaliza la fecha al formato 'YYYY-MM-DD'.
    """
    try:
        dt = pd.to_datetime(fecha_str, errors='coerce', dayfirst=True)
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error al normalizar fecha '{fecha_str}': {e}")
        return None

def normalizar_monto(valor):
    """
    Normaliza el monto asegurando que sea un entero positivo.
    Retorna el valor como entero o None si no es válido.
    """
    try:
        num = float(valor)
        if num.is_integer() and num > 0:
            return int(num)
        else:
            raise ValueError(f"Valor de monto inválido: {valor}")
    except ValueError as e:
        print(f"Error al normalizar monto '{valor}': {e}")
        return None

def normalizar_rut(rut_str):
    """
    Normaliza el RUT eliminando puntos y convirtiéndolo a mayúsculas.
    """
    try:
        rut = str(rut_str).replace(".", "").upper().strip()
        return rut
    except Exception as e:
        print(f"Error al normalizar RUT '{rut_str}': {e}")
        return rut_str

def calcular_fecha_detec(fecha, hora):
    """
    Combina la fecha y la hora en un solo string en el formato "%Y-%m-%d %H:%M:%S".
    Si la hora no contiene segundos (por ejemplo, "19:59"), se le agregan ":00".
    """
    try:
        # Si la hora solo tiene horas y minutos, agregar ":00"
        if len(hora.split(':')) == 2:
            hora = f"{hora}:00"
        dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error calculando fecha_detec para fecha '{fecha}' y hora '{hora}': {e}")
        return None

def calcular_hash_fila(datos_fila: dict):
    """
    Genera un hash MD5 a partir de los datos normalizados.
    datos_fila debe contener las llaves: 'monto', 'Fecha', 'rut', 'codigo_transaccion', 'hora_transaccion'
    """
    data = f"{datos_fila['monto']}_{datos_fila['Fecha']}_{datos_fila['rut']}_{datos_fila['codigo_transaccion']}_{datos_fila['hora_transaccion']}"
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def process_and_store_excel(file_path):
    """
    Lee el archivo Excel, procesa sus columnas y los inserta en la tabla 'transferencias' de Supabase.
    Solo se insertan registros que tengan todos los datos requeridos.
    """
    print(f"[{datetime.now()}] Iniciando procesamiento del archivo: {file_path}")
    try:
        df = pd.read_excel(file_path)
        print(f"[{datetime.now()}] Archivo '{file_path}' leído exitosamente. Número de filas: {len(df)}")
    except Exception as e:
        print(f"[{datetime.now()}] Error al leer el archivo '{file_path}': {e}")
        return

    # Columnas que nos interesan
    columnas_presentes = df.columns.tolist()
    print(f"[{datetime.now()}] Columnas presentes en el archivo: {columnas_presentes}")
    columnas_necesarias = [
        "Fecha de transacción", "Ingreso (+)", "RUT", "Nombre",
        "Código de transacción", "Hora transacción"
    ]

    # Verificar si todas las columnas necesarias están presentes
    for col in columnas_necesarias:
        if col not in columnas_presentes:
            print(f"[{datetime.now()}] La columna '{col}' no está presente en el archivo. Abortando procesamiento.")
            return

    print(f"[{datetime.now()}] Todas las columnas necesarias están presentes. Continuando con el procesamiento...")

    df = df[columnas_necesarias]

    # Renombrar columnas para estandarizar
    df.rename(columns={
        "Fecha de transacción": "Fecha",
        "Ingreso (+)": "monto",
        "RUT": "rut",
        "Nombre": "rs",
        "Código de transacción": "codigo_transaccion",
        "Hora transacción": "hora_transaccion"
    }, inplace=True)

    # Eliminar filas sin monto
    df = df[df["monto"].notna()]

    # Normalizar fecha
    print(f"[{datetime.now()}] Normalizando fechas...")
    df["Fecha"] = df["Fecha"].apply(normalizar_fecha)
    # Eliminar registros con fecha inválida
    df = df[df["Fecha"].notnull()]
    print(f"[{datetime.now()}] Fechas normalizadas. Filas restantes: {len(df)}")

    # Normalizar monto
    print(f"[{datetime.now()}] Normalizando montos...")
    df["monto"] = df["monto"].apply(normalizar_monto)
    # Eliminar filas donde la normalización de monto falló
    df = df[df["monto"].notna()]
    print(f"[{datetime.now()}] Montos normalizados. Filas restantes: {len(df)}")

    # Normalizar RUT
    print(f"[{datetime.now()}] Normalizando RUTs...")
    df["rut"] = df["rut"].apply(normalizar_rut)

    # Filtrar filas donde 'codigo_transaccion' o 'hora_transaccion' sean NaN
    df = df[df["codigo_transaccion"].notna() & df["hora_transaccion"].notna()]
    print(f"[{datetime.now()}] Filas después de filtrar códigos y horas: {len(df)}")

    # Añadir columna "empresa"
    df["empresa"] = "ST CRISTOBAL SPA"

    # Etiquetar tipo de facturación según RUT
    df["facturación"] = df["rut"].apply(lambda x: "empresa" if str(x).startswith("7") else "persona")
    print(f"[{datetime.now()}] Facturación asignada. Filas restantes: {len(df)}")

    # Calcular fecha_detec combinando 'Fecha' y 'hora_transaccion'
    print(f"[{datetime.now()}] Calculando fechas de detección...")
    df["fecha_detec"] = df.apply(lambda row: calcular_fecha_detec(row["Fecha"], row["hora_transaccion"]), axis=1)
    print(f"[{datetime.now()}] Fechas de detección calculadas. Filas restantes: {len(df)}")

    # Crear hash único por fila incluyendo los nuevos campos
    print(f"[{datetime.now()}] Calculando hashes...")
    df["hash"] = df.apply(lambda row: calcular_hash_fila({
        "monto": row["monto"],
        "Fecha": row["Fecha"],
        "rut": row["rut"],
        "codigo_transaccion": row["codigo_transaccion"],
        "hora_transaccion": row["hora_transaccion"]
    }), axis=1)
    print(f"[{datetime.now()}] Hashes calculados. Filas restantes: {len(df)}")

    # Reordenar columnas
    column_order = [
        "monto", "Fecha", "rut", "facturación", "hash",
        "empresa", "rs", "codigo_transaccion", "hora_transaccion", "fecha_detec"
    ]
    df = df[column_order]

    # Filtrar los RUTs que no deben subirse
    initial_count = len(df)
    df = df[~df["rut"].isin(RUTS_A_ELIMINAR)]
    filtered_count = len(df)
    print(f"[{datetime.now()}] Se eliminaron {initial_count - filtered_count} registros con RUTs no permitidos.")

    if df.empty:
        print(f"[{datetime.now()}] No hay registros para insertar después del filtrado. Saltando inserción.")
        return

    # Insertar datos en la tabla `transferencias` de Supabase
    for _, row in df.iterrows():
        # Verificar que no falte ningún dato requerido proveniente de las columnas originales o derivadas.
        required_fields = ["monto", "Fecha", "rut", "rs", "codigo_transaccion", "hora_transaccion", "fecha_detec"]
        if any(pd.isna(row[field]) or row[field] is None for field in required_fields):
            print(f"[{datetime.now()}] Registro con hash {row['hash']} omitido por datos faltantes.")
            continue

        try:
            # Verificar si el hash ya existe en la base de datos
            existe = supabase.table("transferencias").select("hash").eq("hash", row["hash"]).execute()
            if existe.data:
                print(f"[{datetime.now()}] El registro con hash={row['hash']} ya existe. Omitiendo.")
                continue

            # Crear nuevo registro
            nuevo_registro = {
                "monto": row["monto"],
                "fecha": row["Fecha"],
                "rut": row["rut"],
                "facturación": row["facturación"],
                "hash": row["hash"],
                "empresa": row["empresa"],
                "rs": row["rs"],
                "fecha_detec": row["fecha_detec"],
                "enviada": 0
            }

            # Sanitizar el diccionario: reemplazar cualquier NaN por None
            nuevo_registro = {k: (None if pd.isna(v) else v) for k, v in nuevo_registro.items()}

            # Insertar el registro (se envía como lista para cumplir con el formato JSON esperado)
            insert_result = supabase.table("transferencias").insert([nuevo_registro]).execute()

            if insert_result.data:
                print(f"[{datetime.now()}] Registro insertado: {insert_result.data}")
            else:
                print(f"[{datetime.now()}] Error al insertar el registro: {insert_result.error}")

        except Exception as e:
            print(f"[{datetime.now()}] Error al procesar fila con hash={row['hash']}: {e}")

    print(f"[{datetime.now()}] Archivo '{file_path}' procesado e insertado en 'transferencias'.")

def main_loop(file_path, interval_seconds=300):
    """
    Ejecuta el procesamiento del archivo cada 'interval_seconds' segundos.
    """
    while True:
        print(f"[{datetime.now()}] Iniciando procesamiento del archivo.")
        process_and_store_excel(file_path)
        print(f"[{datetime.now()}] Procesamiento completado. Esperando {interval_seconds} segundos para la siguiente ejecución.")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Obtener el directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Ruta al archivo Excel usando ruta relativa
    ruta_excel = os.path.join(current_dir, "Bancos", "excel_detallado.xlsx")

    try:
        main_loop(ruta_excel, interval_seconds=300)
    except KeyboardInterrupt:
        print("\n[INFO] Ejecución interrumpida por el usuario. Saliendo del script.")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado en el bucle principal: {e}")
