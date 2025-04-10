from supabase import create_client
from config import SUPABASE_CONFIG
from src.utils.logger import setup_logger, log_error

logger = setup_logger(__name__)

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa la conexión con Supabase."""
        try:
            self.client = create_client(
                SUPABASE_CONFIG["url"],
                SUPABASE_CONFIG["key"]
            )
            logger.info("Conexión a Supabase establecida exitosamente")
        except Exception as e:
            log_error(logger, e, {"context": "Inicialización de Supabase"})
            raise
    
    def insert_data(self, table_name, data):
        """
        Inserta datos en una tabla de Supabase.
        
        Args:
            table_name (str): Nombre de la tabla
            data (dict): Datos a insertar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            result = self.client.table(table_name).insert(data).execute()
            logger.info(f"Datos insertados en {table_name} exitosamente")
            return result
        except Exception as e:
            log_error(logger, e, {
                "context": "Inserción de datos",
                "table": table_name,
                "data": data
            })
            raise
    
    def update_data(self, table_name, data, match_condition):
        """
        Actualiza datos en una tabla de Supabase.
        
        Args:
            table_name (str): Nombre de la tabla
            data (dict): Datos a actualizar
            match_condition (dict): Condición para encontrar los registros
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            result = self.client.table(table_name).update(data).match(match_condition).execute()
            logger.info(f"Datos actualizados en {table_name} exitosamente")
            return result
        except Exception as e:
            log_error(logger, e, {
                "context": "Actualización de datos",
                "table": table_name,
                "data": data,
                "condition": match_condition
            })
            raise
    
    def query_data(self, table_name, query=None):
        """
        Consulta datos de una tabla de Supabase.
        
        Args:
            table_name (str): Nombre de la tabla
            query (dict, optional): Condiciones de la consulta
            
        Returns:
            list: Resultados de la consulta
        """
        try:
            if query:
                result = self.client.table(table_name).select("*").eq(**query).execute()
            else:
                result = self.client.table(table_name).select("*").execute()
            
            logger.info(f"Consulta en {table_name} realizada exitosamente")
            return result.data
        except Exception as e:
            log_error(logger, e, {
                "context": "Consulta de datos",
                "table": table_name,
                "query": query
            })
            raise 