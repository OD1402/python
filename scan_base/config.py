import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Загружаем переменные из .env 
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Config:
    """ Все конфиги для всех сканеров """
    
    _elasticsearch: Optional[Dict[str, Any]] = None
    _rabbitmq: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def get_db_config(scanner_name: str) -> str:
        """
        scanner_name: Имя сканера (например, 'avito', 'cian')
        
        Returns:
            Строка DSN для подключения к PostgreSQL
        """
        prefix = scanner_name.upper()
        host = os.getenv(f'{prefix}_DB_HOST', 'localhost')
        port = os.getenv(f'{prefix}_DB_PORT', '5432')
        database = os.getenv(f'{prefix}_DB_NAME', f'{scanner_name}_db')
        user = os.getenv(f'{prefix}_DB_USER', 'postgres')
        password = os.getenv(f'{prefix}_DB_PASSWORD', '')
        
        return f"host={host} port={port} dbname={database} user={user} password={password} connect_timeout=10"
    
    @classmethod
    def get_elasticsearch_config(cls) -> Dict[str, Any]:
        # !!!! добавить в аргументы раздел - Мск или РФ
        if cls._elasticsearch is None:
            hosts_str = os.getenv('ELASTICSEARCH_HOSTS', 'localhost:9200')
            cls._elasticsearch = {
                'hosts': [h.strip() for h in hosts_str.split(',')],
                'username': os.getenv('ELASTICSEARCH_USER', ''),
                'password': os.getenv('ELASTICSEARCH_PASSWORD', ''),
                'index_prefix': os.getenv('ELASTICSEARCH_INDEX_PREFIX', 'scan'),
                'timeout': int(os.getenv('ELASTICSEARCH_TIMEOUT', '30')),
            }
        return cls._elasticsearch
    
    @classmethod
    def get_rabbitmq_config(cls) -> Dict[str, Any]:
        if cls._rabbitmq is None:
            cls._rabbitmq = {
                'host': os.getenv('RABBITMQ_HOST', 'localhost'),
                'port': int(os.getenv('RABBITMQ_PORT', '5672')),
                'username': os.getenv('RABBITMQ_USER', 'guest'),
                'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
                'vhost': os.getenv('RABBITMQ_VHOST', '/'),
                'exchange': os.getenv('RABBITMQ_EXCHANGE', 'scan_exchange'),
            }
        return cls._rabbitmq




