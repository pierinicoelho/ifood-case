"""
Fábrica de loggers centralizada para garantir padronização em toda a aplicação.
"""

import logging
from functools import wraps
import time



def get_logger(module_name: str) -> logging.Logger:
    """
    Configura e retorna uma instância centralizada de logger.
    Args: 
        module_name: nome do módulo registrado
    Retorna: 
        logging.Logger: instância de logger configurada
    """

    logger = logging.getLogger(module_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.propagate = False
    return logger

def log_execution(logger_instance=None):
    """
    Decorador para registrar o início, fim e quaisquer erros durante a execução de uma função.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_instance or get_logger(func.__module__)
            log.info(f"INICIO | Iniciando execução de: '{func.__name__}'...")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                log.info(f"SUCESSO | '{func.__name__}' concluída em {execution_time:.2f} segundos.")
                return result
                
            except Exception as e:
                log.error(f"FALHA | Falha na função '{func.__name__}': {str(e)}", exc_info=True)
                raise
                
        return wrapper
    return decorator