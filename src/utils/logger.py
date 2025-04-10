import logging
import logging.config
from pathlib import Path
import sys
from config import LOGGING_CONFIG

def setup_logger(name):
    """
    Configura y retorna un logger con el nombre especificado.
    
    Args:
        name (str): Nombre del logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    # Configurar el logging
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Obtener el logger
    logger = logging.getLogger(name)
    
    return logger

def log_error(logger, error, context=None):
    """
    Registra un error en el logger con contexto adicional.
    
    Args:
        logger (logging.Logger): Logger a usar
        error (Exception): Error a registrar
        context (dict, optional): Contexto adicional del error
    """
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg += f" | Contexto: {context}"
    logger.error(error_msg, exc_info=True)

def log_info(logger, message, context=None):
    """
    Registra un mensaje informativo en el logger.
    
    Args:
        logger (logging.Logger): Logger a usar
        message (str): Mensaje a registrar
        context (dict, optional): Contexto adicional
    """
    if context:
        message = f"{message} | Contexto: {context}"
    logger.info(message) 