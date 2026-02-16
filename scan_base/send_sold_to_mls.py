#!/usr/bin/env python3
"""
Функция для отправки объявлений в статус "продано" в MLS
"""

import json
import time
from typing import List, Optional, Tuple, Any
import requests
from psycopg2.extras import RealDictCursor
# from scan_avito_v5.const import *
from scan_base.db import execute_db_query
from scan_base.config import Config

# Конфигурация MLS
MLS_MSK_ELASTIC_URL="test"
MLS_RGN_ELASTIC_URL = 'test'
MLS_SOLD_URL = 'test'
MLS_ACCESS_TOKEN = 'test'


def get_scanner_name_by_project(project: int) -> str:
    project_to_scanner = {
        10: 'avito', 
        24: 'domclick',
        11: 'cian',
    }
    return project_to_scanner.get(project, '')


def get_previous_sessions_avito(conn, scan_session: int, db_config: str, project: int) -> Tuple[int, Optional[str], Any]:
    """
    Получаем минимальный id сессии, старше которой объекты должны быть помечены как проданные.
    
    Логика: объект помечается как проданный, если его scan_session < (текущая_сессия - SKIP_SESSIONS_COUNT)
    То есть, если объект не обновлялся в последних SKIP_SESSIONS_COUNT сессиях.
    
    Args:
        conn: Подключение к БД
        scan_session: ID текущей сессии
        db_config: Строка конфигурации БД для переподключения
    
    Returns:
        Кортеж (минимальный id сессии для проверки, код региона, обновленное соединение)
    """

    # Количество прошлых сессий, среди которых будем искать проданные объявления
    limit_previous_sessions = 5

    scanner_name = get_scanner_name_by_project(project)

    # Получаем region и facet текущей сессии
    def get_current_session_query(current_conn):
        if scanner_name == 'avito':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT region, facet FROM scan_sessionlar_v5 WHERE id = %s",
                    (scan_session,)
                )
                return cursor.fetchone()
        elif scanner_name == 'domclick':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT region, facet FROM scan_sessionlar_v2 WHERE id = %s",
                    (scan_session,)
                )
                return cursor.fetchone()
    
    current_session, conn = execute_db_query(conn, db_config, get_current_session_query)
    
    if not current_session:
        print(f"   ⚠️  Не удалось получить region и facet для сессии {scan_session}")
        return 0, None, conn
    
    region_id = current_session['region']
    facet_id = current_session['facet']
    
    # Получаем код региона
    def get_region_code_query(current_conn):
        if scanner_name == 'avito':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT code FROM regionlar_v5 WHERE id = %s",
                    (region_id,)
                )
                return cursor.fetchone()
        elif scanner_name == 'domclick':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT code FROM regionlar_v2 WHERE id = %s",
                    (region_id,)
                )
                return cursor.fetchone()
    
    region_row, conn = execute_db_query(conn, db_config, get_region_code_query)
    region_code = region_row['code'] if region_row else None
    
    # Ищем прошлые сессии
    def get_previous_sessions_query(current_conn):
        if scanner_name == 'avito':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id 
                    FROM scan_sessionlar_v5 
                    WHERE region = %s 
                        AND facet = %s 
                        AND id < %s 
                        AND finished_at IS NOT NULL
                    ORDER BY id DESC 
                    LIMIT %s
                    """,
                    (region_id, facet_id, scan_session, limit_previous_sessions)
                )
                return cursor.fetchall()
        elif scanner_name == 'domclick':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id 
                    FROM scan_sessionlar_v2 
                    WHERE region = %s 
                        AND facet = %s 
                        AND id < %s 
                        AND finished_at IS NOT NULL
                    ORDER BY id DESC 
                    LIMIT %s
                    """,
                    (region_id, facet_id, scan_session, limit_previous_sessions)
                )
                return cursor.fetchall()
    
    previous_sessions, conn = execute_db_query(conn, db_config, get_previous_sessions_query)
    session_ids = [row['id'] for row in previous_sessions]
    
    # SKIP_SESSIONS_COUNT означает: сколько сессий ПОДРЯД объект должен отсутствовать в ЭТОМ разделе
    # Если SKIP_SESSIONS_COUNT = 2, то объект отправляется в проданные,
    # если его scan_session < (id сессии, которая на 2 позиции назад от текущей в ЭТОМ разделе)
    # То есть, если объект не обновлялся в последних 2 сессиях ЭТОГО раздела
    
    # Вычисляем минимальный id сессии: объекты с scan_session меньше этого значения
    # не обновлялись в последних SKIP_SESSIONS_COUNT сессиях ЭТОГО раздела
    if len(session_ids) >= SKIP_SESSIONS_COUNT:
        # Берем id сессии, которая на SKIP_SESSIONS_COUNT позиций назад от текущей
        min_session_id = session_ids[SKIP_SESSIONS_COUNT - 1] if session_ids else 0
    else:
        # Если сессий меньше, чем SKIP_SESSIONS_COUNT, то все объекты считаются "старыми"
        min_session_id = session_ids[-1] if session_ids else 0
    
    return min_session_id, region_code, conn



def get_external_ids_to_mark_sold(conn, min_session_id: int, current_session: int, region_id: int, facet_id: int, db_config: str, project: int):
    """
    Получаем external_id, которые нужно пометить как проданные.
    """
    scanner_name = get_scanner_name_by_project(project)
    db_config = Config.get_db_config(scanner_name)

    if min_session_id <= 0:
        return [], conn
    
    def get_external_ids_query(current_conn):
        if scanner_name == 'avito':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT cs.external_id 
                    FROM card_shotlar_v5 cs
                    INNER JOIN scan_sessionlar_v5 ss ON cs.scan_session = ss.id
                    WHERE cs.scan_session < %s
                        AND cs.scan_session < %s
                        AND ss.region = %s
                        AND ss.facet = %s
                    """,
                    (min_session_id, current_session, region_id, facet_id)
                )
                return cursor.fetchall()
        elif scanner_name == 'domclick':
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT cs.external_id 
                    FROM card_shotlar_v2 cs
                    INNER JOIN scan_sessionlar_v2 ss ON cs.scan_session = ss.id
                    WHERE cs.scan_session < %s
                        AND cs.scan_session < %s
                        AND ss.region = %s
                        AND ss.facet = %s
                    """,
                    (min_session_id, current_session, region_id, facet_id)
                )
                return cursor.fetchall()
    
    rows, conn = execute_db_query(conn, db_config, get_external_ids_query)
    return [row['external_id'] for row in rows], conn



def get_mls_guid(external_id: int, region_code: Optional[str], project: int) -> List[str]:
    """
        Получаем список guid из MLS Elasticsearch для указанного external_id
    """
    mls_guid_list = []

    if region_code in ('msk', 'mo'):
        elastic_url = MLS_MSK_ELASTIC_URL
    else:
        elastic_url = MLS_RGN_ELASTIC_URL

    search_url = f"{elastic_url}_search?q=external_id:{external_id}%20AND%20project_id:{project}%20AND%20deal_status_id:1"

    try:
        response = requests.get(search_url, timeout=30)
        if response.status_code == 200:
            response_json = response.json()             
            if response_json.get('hits') and response_json['hits'].get('hits'):
                for hit in response_json['hits']['hits']:
                    if hit.get('_source') and hit['_source'].get('guid'):
                        mls_guid_list.append(hit['_source']['guid'])
        elif response.status_code >= 500:
            print(f'   ⏳ status == {response.status_code}, попробуем еще раз получить guid для external_id: {external_id}')
            time.sleep(2)
            return get_mls_guid(external_id, region_code, project)  # Рекурсивный повтор
        else:
            print(f'   ❌ Не удалось получить guid из МЛС в get_mls_guid')
            print(f'   response status: {response.status_code}')
            print(f'   response text: {response.text[:200]}')
            return mls_guid_list
    except Exception as e:
        print(f'   ❌ Ошибка при получении guid из МЛС в get_mls_guid: {e}')
        return mls_guid_list
    return mls_guid_list
    


def put_status_sold(mls_guid_list: List[str]) -> bool:
    if not mls_guid_list:
        return True
    
    try:
        response = requests.put(
            MLS_SOLD_URL,
            headers={
                "Content-Type": "application/json",
                "Access-Token": MLS_ACCESS_TOKEN
            },
            json=mls_guid_list,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f'   ✅ Выставили "продано" объявлениям: {mls_guid_list}')
            return True
        elif response.status_code >= 500:
            print(f'   ⏳ status == {response.status_code}, попробуем еще раз получить данные')
            time.sleep(2)
            return put_status_sold(mls_guid_list)  # Рекурсивный повтор
        else:
            print(f'   ❌ Не удалось получить данные из МЛС')
            print(f'   response status: {response.status_code}')
            print(f'   response text: {response.text[:200]}')
            return False
    except Exception as e:
        print(f'   ❌ Ошибка при установке статуса "продано": {e}')
        return False



def send_sold_to_mls(conn, scan_session: int, project: int) -> None:
    """
    Основная функция для отправки объявлений в статус "продано"
    
    Выполняет следующие шаги:
    1. Получает id прошлых сессий сканирования этого же раздела
    2. Получает все external_id из card_shotlar_v5 для этих сессий
    3. Для каждого external_id получает guid из MLS Elasticsearch
    4. Устанавливает статус "продано" для всех найденных guid
    
    Args:
        conn: Подключение к БД
        scan_session: ID текущей сессии
        project: ID проекта (например, AVITO_PROJECT_ID или CIAN_PROJECT_ID)
    """
    print("\n   🔄 Начинаем актуализацию - ставим статус 'продано'...")
    
    # Определяем источник данных по project ID и получаем конфиг БД
    scanner_name = get_scanner_name_by_project(project)
    db_config = Config.get_db_config(scanner_name)
    
    # Шаг 1: Получаем минимальный id сессии и код региона
    min_session_id, region_code, conn = get_previous_sessions_avito(conn, scan_session, db_config, project)
    
    if not region_code:
        print("   ⚠️  Не удалось определить код региона")
        return
    
    if min_session_id <= 0:
        print(f"   ℹ️  Недостаточно прошлых сессий для проверки (нужно больше {SKIP_SESSIONS_COUNT})")
        return
    
    # Получаем region_id и facet_id для фильтрации
    if scanner_name == 'avito':
        def get_current_session_data_query(current_conn):
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT region, facet FROM scan_sessionlar_v5 WHERE id = %s",
                    (scan_session,)
                )
                return cursor.fetchone()
    elif scanner_name == 'domclick':
        def get_current_session_data_query(current_conn):
            with current_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT region, facet FROM scan_sessionlar_v2 WHERE id = %s",
                    (scan_session,)
                )
                return cursor.fetchone()
    
    current_session_data, conn = execute_db_query(conn, db_config, get_current_session_data_query)
    if not current_session_data:
        print("   ⚠️  Не удалось получить данные текущей сессии")
        return
    region_id = current_session_data['region']
    facet_id = current_session_data['facet']
    
    print(f"   📋 Минимальный id сессии для проверки: {min_session_id}")
    print(f"   📋 Объекты с scan_session < {min_session_id} будут помечены как проданные")
    
    # Шаг 2: Получаем external_id объектов, которые не обновлялись в последних SKIP_SESSIONS_COUNT сессиях
    external_ids, conn = get_external_ids_to_mark_sold(conn, min_session_id, scan_session, region_id, facet_id, db_config, project)
    
    if not external_ids:
        print("   ℹ️  Объявления для пометки как проданные не найдены")
        return
    
    print(f"   📋 Найдено объявлений для пометки как проданные: {len(external_ids)}")
    
    # Шаг 3 и 4: Для каждого external_id получаем guid и устанавливаем статус
    total_processed = 0
    total_sold = 0
    
    for external_id in external_ids:
        # Получаем guid из MLS с учетом региона и project
        mls_guid_list = get_mls_guid(external_id, region_code, project)
        
        if mls_guid_list:
            # Устанавливаем статус "продано"
            if put_status_sold(mls_guid_list):
                total_sold += len(mls_guid_list)
            total_processed += 1

            time.sleep(0.5)
    
    print(f"   ✅ Обработано объявлений: {total_processed}, установлено статус 'продано' для {total_sold} guid")
