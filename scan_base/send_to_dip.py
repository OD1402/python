"""
Модуль для отправки карточек в DIP через RabbitMQ
"""

import json
import time
import pika
from scan_base.config import Config


def send_to_dip(card_json: dict, dip_module_id: int, file_name: str) -> bool:
    """
    Отправляет карточку в DIP через RabbitMQ
    
    Args:
        card_json: json одной карточки
        dip_module_id: ID модуля разбора данных из DIP
        file_name: Имя job'а для DIP в формате "avito-sale-flat-mo", последовательность не имеет значения, главное передать суть
    
    Returns:
        True если отправка успешна (всегда возвращает True, так как попытки бесконечные)
    """
    rmq_config = Config.get_rabbitmq_config()
    attempt = 0
    
    while True:
        attempt += 1
        connection = None
        channel = None
        
        try:
            credentials = pika.PlainCredentials(rmq_config['username'], rmq_config['password'])
            parameters = pika.ConnectionParameters(
                host=rmq_config['host'],
                port=rmq_config['port'],
                virtual_host=rmq_config['vhost'],
                credentials=credentials,
                # Увеличиваем таймауты для более надежного соединения
                socket_timeout=30,
                connection_attempts=3,
                retry_delay=2
            )
            
            # Подключаемся к RabbitMQ
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            queue = 'process-source-wcrawler'
            message = {
                "workerName": "process-source-wcrawler",
                "params": {
                    "params": {
                        "dip_module_id": dip_module_id,
                        "fileName": file_name
                    },
                    "source": [card_json]
                }
            }
            
            # Отправляем сообщение
            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                )
            )
            
            # Закрываем канал и соединение безопасно
            def safe_close():
                """Безопасно закрывает канал и соединение"""
                try:
                    if channel and not channel.is_closed:
                        channel.close()
                except (Exception, KeyboardInterrupt):
                    pass
                
                try:
                    if connection and not connection.is_closed:
                        connection.close()
                except (Exception, KeyboardInterrupt):
                    pass
            
            safe_close()
            
            # Успешная отправка
            if attempt > 1:
                print(f"   ✓ Карточка успешно отправлена в RabbitMQ (попытка {attempt})")
            return True
        
        except Exception as e:
            # Закрываем соединение при любой ошибке
            try:
                if channel and not channel.is_closed:
                    channel.close()
            except Exception:
                pass
            try:
                if connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass
            
            print(f"   ⚠️  Ошибка при отправке в RabbitMQ (попытка {attempt}): {type(e).__name__}: {e}")
            print(f"   ⏳ Повторная попытка через 2 секунды...")
            time.sleep(2)
            continue



