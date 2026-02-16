"""
Модуль для работы с базой данных 
"""

import time
import psycopg2


def connect_to_db(db_config: str):
    """
    Подключается к БД с retry-логикой.
    При ошибке подключения повторяет попытки с интервалом 2 секунды.
    """
    while True:
        try:
            conn = psycopg2.connect(db_config)
            print("✅ Подключение к БД установлено")
            return conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"⚠️ Ошибка подключения к БД: {e}. Повторная попытка через 2 секунды...")
            time.sleep(2)
            continue


def execute_db_query(conn, db_config: str, query_func):
    """
    Выполняет запрос к БД с retry-логикой и переподключением.
    При любой ошибке переподключается и повторяет запрос.
    
    Args:
        conn: Текущее подключение к БД (может быть закрыто)
        db_config: Строка конфигурации БД для переподключения
        query_func: Функция, которая принимает соединение и выполняет запрос
    
    Returns:
        Кортеж (результат выполнения query_func, новое соединение)
    """
    current_conn = conn
    
    while True:
        try:
            # Проверяем, что соединение активно
            if current_conn.closed:
                raise psycopg2.InterfaceError("Connection is closed")
            
            # Выполняем запрос
            result = query_func(current_conn)
            return (result, current_conn)
            
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"⚠️ Ошибка при запросе к БД: {e}. Переподключаемся...")
            
            # Закрываем старое соединение
            old_conn = current_conn
            try:
                if not old_conn.closed:
                    old_conn.close()
            except Exception:
                pass
            
            time.sleep(2)
            
            try:
                current_conn = connect_to_db(db_config)
                # current_conn = psycopg2.connect(db_config)
                print(f"   ✅ Переподключение к БД успешно")
                continue # Выполняем запрос еще раз с новым соединением
            except Exception as reconnect_error:
                print(f"   ❌ Ошибка переподключения: {reconnect_error}")
                time.sleep(2)
                continue
