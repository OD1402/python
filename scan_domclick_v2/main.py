#!/usr/bin/env python3
"""
Скрипт для сканирования domclick

Можно получить за раз:
    * 99 страниц
    * 20 объявлений на странице

Ссылка на API, которое сканируем:
https://bff-search-web.domclick.ru/api/offers/v1?address=1d1463ae-c80f-4d19-9331-a1b68a85b553&offset=0&limit=20&sort=price&sort_dir=asc&deal_type=sale&category=living&offer_type=layout&offer_type=flat&aids=2299&sale_price__gte=1000
"""

import time
import json
import sys
import random
import re
import socket
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from scan_base.config import Config
from scan_base.send_to_dip import send_to_dip
from scan_base.send_sold_to_mls import send_sold_to_mls
from scan_base.db import execute_db_query, connect_to_db
from scan_domclick_v2.const import *


def check_port_available(host: str, port: int, timeout: float = 2.0) -> bool:
    """Проверяет, доступен ли порт для подключения"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0  # Порт доступен, если connect_ex вернул 0
    except Exception:
        return False


def connecting_to_browser():
    """
    Подключается к уже запущенному браузеру Chrome с remote debugging
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    print(f"\n{'='*60}")
    print(f"🔌 Подключение к браузеру Chrome (remote debugging)")
    print(f"   ✓ Хост: {DEBUGGER_HOST}:{DEBUGGER_PORT}")
    
    # Проверяем доступность порта перед попыткой подключения
    if not check_port_available(DEBUGGER_HOST, DEBUGGER_PORT):
        raise Exception(
            f"❌ Порт {DEBUGGER_HOST}:{DEBUGGER_PORT} недоступен!\n"
        )
    print(f"   ✓ Порт {DEBUGGER_PORT} доступен")
    
    # Создаем опции для подключения к уже запущенному браузеру
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"{DEBUGGER_HOST}:{DEBUGGER_PORT}")
    
    # Selenium запускает ChromeDriver и через него подключается к уже запущенному Chrome
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("   ✓ WebDriver создан")
    except Exception as e:
        raise Exception(
            f"❌ Не удалось подключиться к браузеру!\n"
            f"   Ошибка: {str(e)}\n"
        )
    
    # Получаем адрес текущей открытой страницы в браузере
    try:
        current_url = driver.current_url
        print(f"   ✓ Подключились к браузеру")
        print(f"   Текущий URL: {current_url}")
    except Exception as e:
        raise Exception(
            f"❌ Не удалось получить информацию о текущей странице!\n"
            f"   Ошибка: {e}\n"
        )
    
    # Проверяем, что мы на странице Домклик
    if HOME_URL not in driver.current_url:
        print(f"   ⚠️ ВНИМАНИЕ: Мы не на странице {HOME_URL} ")
        print(f"   Текущий URL: {driver.current_url}")
        # Можно автоматически открыть страницу, но лучше вручную
        # driver.get("https://domclick.ru/")
    
    # Настраиваем CDP Network domain
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        print("   ✓ CDP Network domain включен")
    except Exception as e:
        print(f"   ⚠️ Не удалось включить Network domain: {e}")
    
    print(f"{'='*60}\n")
    
    return driver



def parse_arguments():
    if len(sys.argv) < 2:
        sys.exit("Укажите раздел для сканирования, например, 'flat-sale-msk'")
    parts = sys.argv[1].split('-')
    if len(parts) != 3:
        sys.exit("Укажите раздел для сканирования, например, 'flat-sale-msk'")
    return parts[0], parts[1], parts[2]


def _execute_cdp_request_single(driver, api_url: str) -> Dict[str, Any]:
    """
    Выполняет один запрос через CDP Runtime.evaluate (внутренняя функция)
    
    Args:
        driver: WebDriver объект
        api_url: URL для запроса
    
    Returns:
        Словарь с результатом запроса
    """
    fetch_script = f"""
        (async function() {{
            try {{
                const response = await fetch('{api_url}', {{
                    method: 'GET',
                    credentials: 'include',
                    headers: {{
                        'Accept': '*/*',
                        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    }}
                }});
                
                const text = await response.text();
                let jsonData = null;
                try {{
                    jsonData = JSON.parse(text);
                }} catch (e) {{
                    // Если не JSON, возвращаем текст
                }}
                
                return {{
                    success: true,
                    status: response.status,
                    statusText: response.statusText,
                    body: jsonData || text,
                    bodyLength: text.length
                }};
            }} catch (error) {{
                return {{
                    success: false,
                    error: error.toString(),
                    message: error.message,
                    status: error.status || null,
                    statusText: error.statusText || null
                }};
            }}
        }})()
    """
    
    try:
        cdp_result = driver.execute_cdp_cmd('Runtime.evaluate', {
            'expression': fetch_script,
            'awaitPromise': True,
            'returnByValue': True
        })
        
        result_data = cdp_result.get('result', {})
        
        if cdp_result.get('exceptionDetails'):
            exception = cdp_result.get('exceptionDetails', {})
            return {
                'success': False,
                'error': exception.get('text', 'Unknown error'),
                'message': exception.get('exception', {}).get('description', 'Unknown exception')
            }
        elif result_data.get('type') == 'object' and 'value' in result_data:
            return result_data['value']
        else:
            return {
                'success': False,
                'error': 'Unexpected result format',
                'message': f"Result type: {result_data.get('type', 'unknown')}"
            }
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        return {
            'success': False,
            'error': 'CDP execution error',
            'message': error_message,
            'exception_type': error_type,
            'traceback': error_traceback
        }


def execute_cdp_request(driver, api_url: str, page_num: int = 0):
    """
    Выполняем запрос через CDP с повторными попытками при ошибках.
    
    Args:
        driver: WebDriver объект
        api_url: URL для запроса
        page_num: Номер страницы (пока что не используется)
    
    Returns:
        Словарь (json) с объявлениями
    """
    retry_count = 0
    
    while retry_count <= MAX_RETRY_SCAN_URL:
        if retry_count > 0:
            delay = random.randint(30, 60)
            print(f"   ⏳ Повторная попытка {retry_count} из {MAX_RETRY_SCAN_URL}. Ждем {delay} секунд...")
            time.sleep(delay)
        
        result = _execute_cdp_request_single(driver, api_url)
        
        status = result.get('status', 'N/A')
        status_text = result.get('statusText', 'N/A')
        
        if status == 200:
            return result  # Успешный запрос, возвращаем результат
        else:
            print(f"   ⚠️  HTTP {status} ({status_text})")
            retry_count += 1
            if retry_count <= MAX_RETRY_SCAN_URL:
                continue
            else:
                # Все попытки исчерпаны - завершаем программу
                print(f"\n❌ Не удалось получить успешный ответ (HTTP {status}) после {MAX_RETRY_SCAN_URL + 1} попыток")
                print("Завершаем выполнение программы")
                sys.exit(1)


def add_card_shot(conn, scan_session: int, external_id: int, external_url: str, card: dict, db_config: str = None) -> Tuple[Optional[int], Any]:
    """
    Сохраняет карточку в БД с автоматическим переподключением при обрыве соединения.
    
    Args:
        conn: Подключение к БД (может быть пересоздано при обрыве)
        scan_session: ID сессии сканирования
        external_id: Внешний ID объявления
        external_url: URL объявления
        card: Данные карточки
        db_config: Строка конфигурации БД для переподключения (обязательно для retry-логики)
    
    Returns:
        Кортеж (card_id или None, новое соединение)
    """
    if not db_config:
        raise ValueError("db_config обязателен для add_card_shot")
    
    def add_card_query(current_conn):
        with current_conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM add_card_shot_v2(%s, %s, %s, %s)",
                (scan_session, external_id, external_url, json.dumps(card))
            )
            result = cursor.fetchone()
            current_conn.commit()
            return result[0] if result else None
    
    try:
        card_id, conn = execute_db_query(conn, db_config, add_card_query)
        return (card_id, conn)
    except Exception as e:
        # Если это не ошибка соединения, пробрасываем исключение
        print(f"❌ Ошибка при сохранении карточки {external_id}: {e}")
        raise


def process_items(conn, scan_session: int, items: list, facet_name: str, file_name: str, db_config: str = None) -> Tuple[int, Any]:
    """
    Обрабатывает список объявлений и возвращает максимальную цену и обновленное соединение
    
    Args:
        conn: Подключение к БД
        scan_session: ID сессии сканирования
        items: Список объявлений
        facet_name: Название фасета
        file_name: Имя файла
        db_config: Строка конфигурации БД для переподключения (опционально)
    
    Returns:
        Кортеж (min_price, обновленное соединение)
    """
    min_price = 0
    
    for item in items:

        external_id = item.get('id')
        external_url = item.get('path')
        
        if external_url:
            if external_url.startswith('/'):
                external_url = 'https://domclick.ru' + external_url
        
        if not external_id or not external_url:
            print(f"!!!!!!!!!!! кажется этот элемент не карточка. item = ", item)
            continue

        # Сохраняем карточку в БД mirror
        card_id, conn = add_card_shot(conn, scan_session, external_id, external_url, item, db_config=db_config)
        if not card_id:
            print(f"Карточка {external_id} не сохранена в БД")
            sys.exit(1)

        # Отправляем карточку в DIP 
        send_to_dip(item, DIP_MODULE_ID, file_name)

        if price := item.get('price'):
            if price > min_price:
                min_price = price
                
    return (min_price, conn)


def scan_pages(
    driver,
    conn,
    scan_session: int,
    scan_url: str,
    page_num: int,
    min_price: int,
    facet_name: str,
    file_name: str,
    db_config: str = None
) -> tuple:
    """
    Сканирует страницы от page_num до MAX_PAGES
    
    Args:
        driver: WebDriver объект
        conn: Подключение к БД
        scan_session: ID сессии сканирования
        scan_url: Начальный URL для сканирования
        page_num: Начальный номер страницы
        offer_type: Тип предложения
        deal_type: Тип сделки
        region_code: Код региона
    
    Returns:
        Кортеж (page_num, min_price, scan_url) - последний номер страницы, минимальная цена и URL
    """
    new_min_price = 0
    
    while page_num <= MAX_PAGES:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'\n[{current_time}]{GREEN}\n   facet_name = "{facet_name}", \n   сессия = {scan_session}, min_price = {min_price}, page_num = {page_num}{RESET}')
        print(f"   URL: {scan_url}")
        time.sleep(random.randint(*INTERVAL))

        result = execute_cdp_request(driver, scan_url, page_num)

        # Извлекаем body.catalog.items - это массив объявлений
        items = result.get('body', {}).get('result', {}).get('items')
        
        items_count = len(items)
        print(f"   Получено карточек: {items_count}")

        if not items_count:
            # Сохраняем body в файл result.json
            # body_data = result.get('body', {})
            # try:
            #     with open('result.json', 'w', encoding='utf-8') as f:
            #         json.dump(body_data, f, ensure_ascii=False, indent=2)
            #     print(f"   💾 Сохранено body в result.json")
            # except Exception as e:
            #     print(f"   ⚠️  Ошибка при сохранении result.json: {e}")
            
            # если массив карточек пустой, значит прошлая страница была последней, закрываем сессию
            def finish_session_query(current_conn):
                with current_conn.cursor() as cursor:
                    cursor.execute("SELECT finish_scan_session_v2(%s)", (scan_session,))
                    result = cursor.fetchone()
                    session_finished = result[0] if result else False
                    current_conn.commit()
                    return session_finished
            
            session_finished, conn = execute_db_query(conn, db_config, finish_session_query)
            
            if session_finished:
                print(f"   ✅ Сессия {scan_session} завершена (finished_at установлен)")

                # Отправляем объявления из прошлых сессий в статус "продано"
                try:
                    send_sold_to_mls(conn, scan_session, PROJECT_ID)
                except Exception as e:
                    print(f"   ⚠️  Ошибка при отправке объявлений в статус 'продано': {e}")
            else:
                print(f"   ⚠️ Сессия {scan_session} не найдена в БД")
            
            print("Завершаем выполнение программы")
            sys.exit(0)
        
        new_min_price, conn = process_items(conn, scan_session, items, facet_name, file_name, db_config)
        # print(f"   Максимальная цена на странице = {new_min_price} (будет использована как pmin для следующего цикла)")

        page_num = page_num + 1
        scan_url = re.sub(r'&offset=\d+&', f'&offset={page_num*20-20}&', scan_url)
    
    return page_num, new_min_price, scan_url, conn



# ============================================================================== #
# ============================================================================== #

def main():

    # ============================ ПОДКЛЮЧАЕМСЯ К БД ============================ #
    db_config = Config.get_db_config('domclick')
    conn = connect_to_db(db_config)
    

    # ===================== ФОРМИРУЕМ ССЫЛКУ ДЛЯ СКАНИРОВАНИЯ ===================== #
    
    # Парсим аргументы командной строки
    offer_type, deal_type, region_code = parse_arguments()
    page_num = 1

    scan_url = ''
    # scan_url = 'https://bff-search-web.domclick.ru/api/offers/v1?address=1d1463ae-c80f-4d19-9331-a1b68a85b553&offset=0&limit=20&sort=price&sort_dir=asc&deal_type=sale&category=living&offer_type=layout&offer_type=flat&aids=2299&sale_price__gte=1000'

    def get_params_for_url_query(current_conn):
        # with - контекстный менеджер, гарантирует автоматическое закрытие ресурса при выходе из блока
        with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM get_params_for_url_v2(%s, %s, %s)",
                (region_code, deal_type, offer_type)
            )
            return cursor.fetchone()
    
    params_for_url, conn = execute_db_query(conn, db_config, get_params_for_url_query)
    # Формируем базовый URL
    scan_url = (
        f"https://bff-search-web.domclick.ru/api/offers/v1?address={params_for_url['o_region']}&"
        f"offset=0&limit=20&sort=price&sort_dir=asc&deal_type={params_for_url['o_deal_type']}&"
        f"category={params_for_url['o_category']}&"
    )
        
    # для Коммерческой и Гаражей offer_type отсутствует
    if params_for_url.get('o_offer_type'):
        scan_url += f"offer_type={params_for_url.get('o_offer_type')}&"
        
    scan_url += f"aids={params_for_url['o_aids']}"
    
        

    # ============================ ПОЛУЧАЕМ FACET NAME ДЛЯ DIP ============================ #
    def get_facet_name_query(current_conn):
        with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM get_params_for_dip_facet_v2(%s, %s, %s)",
                (region_code, deal_type, offer_type)
            )
            return cursor.fetchone()
    
    result, conn = execute_db_query(conn, db_config, get_facet_name_query)
    facet_name = result['o_facet_name'] if result else None
    # facet_name = "Московская область::Квартира::Купить"
    print('\nfacet_name =', facet_name)
        
    if not facet_name:
        print(f"Не удалось получить facet для region_code='{region_code}', deal_type='{deal_type}', offer_type='{offer_type}'")
        sys.exit(1)



    # =============================== ПОЛУЧАЕМ СЕССИЮ ================================ #
    def get_or_create_session_query(current_conn):
        with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM get_or_create_scan_session_v2(%s, %s, %s)",
                (region_code, deal_type, offer_type)
            )
            result = cursor.fetchone()
            current_conn.commit()
            return result
    
    result, conn = execute_db_query(conn, db_config, get_or_create_session_query)
    scan_session = result['_session']
    min_price = result['_min_price']
    page_num = result['_page_num']
    
    if min_price > 0:
        scan_url = f"{scan_url}&sale_price__gte={min_price}" # rent_price__gte
    if page_num < MAX_PAGES:
        scan_url = scan_url.replace('&offset=0&', f'&offset={page_num*20-20}&')

    print(f"сессия = {scan_session}, min_price = {min_price}, page_num = {page_num}")
    print(f"\nscan_url = {scan_url}")


    # ============================ ПОДКЛЮЧАЕМСЯ К БРАУЗЕРУ ============================ #
    driver = None
    try:
        driver = connecting_to_browser()
    except Exception as e:
        print(f"\n❌ Не удалось подключиться к браузеру: {e}")
        if conn:
            conn.close()
        return
    

    # ========================== ФОРМИРУЕМ FILE_NAME ДЛЯ DIP ========================= #
    file_name = f"domclick-{offer_type}-{deal_type}-{region_code}"


    # ========================= ПОЛУЧАЕМ ДАННЫЕ ПО scan_url ========================== #     
    try:
        while True:            
            # min_price для первого цикла берется из сессии, для последующих - из результата scan_pages
            page_num, min_price, scan_url, conn = scan_pages(
                driver,
                conn,
                scan_session,
                scan_url,
                page_num,
                min_price,
                facet_name,
                file_name,
                db_config
            )
            
            print(f"\n🔄 Обновляем сессию в БД: session_id={scan_session}, page_num=1, min_price={min_price}")
            # Обновляем сессию в БД после завершения цикла с retry-логикой
            def update_session_query(current_conn):
                with current_conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT update_scan_session_v2(%s::bigint, %s::smallint, %s::bigint)",
                        (scan_session, 1, min_price)
                    )
                    result = cursor.fetchone()
                    session_updated = result[0] if result else False
                    current_conn.commit()
                    return session_updated
            
            session_updated, conn = execute_db_query(conn, db_config, update_session_query)
            
            if session_updated:
                print(f"✅ Сессия обновлена в БД\n")
            else:
                print(f"⚠️ Сессия {scan_session} не найдена в БД\n")
            

            # Формируем новый URL и начинаем снова с первой страницы
            print(f"   Формируем новый URL для следующего цикла с min_price={min_price}")
            page_num = 1
            
            # базовый URL
            scan_url = (
                f"https://bff-search-web.domclick.ru/api/offers/v1?address={params_for_url['o_region']}&"
                f"offset=0&limit=20&sort=price&sort_dir=asc&deal_type={params_for_url['o_deal_type']}&"
                f"category={params_for_url['o_category']}&"
            )
            
            # для Коммерческой и Гаражей offer_type отсутствует
            if params_for_url.get('o_offer_type'):
                scan_url += f"offer_type={params_for_url.get('o_offer_type')}&"
            
            # добавляем min_price
            scan_url += f"aids={params_for_url['o_aids']}&"
            scan_url += f"sale_price__gte={min_price}"


            print(f"   URL: {scan_url}\n")
    except KeyboardInterrupt:
        print("\n\n⚠️ Получено прерывание (Ctrl+C). Завершаем выполнение...")
    finally:
        # Закрываем соединение с БД
        if conn:
            conn.close()
            print("✓ Соединение с БД закрыто")
            print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()

