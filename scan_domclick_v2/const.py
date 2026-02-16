HOME_URL = "domclick.ru"

DIP_MODULE_ID = 23
PROJECT_ID = 24

MAX_PAGES = 99 # максимум 99, offset=1980

# Задержка перед запросом к API Домклика (в секундах)
INTERVAL = (1, 4)

# Количество повторных попыток получить данные от Домклика в случае ошибки
MAX_RETRY_SCAN_URL = 10

# Количество сессий подряд, в которых объект должен отсутствовать, чтобы отправиться в проданные
# Например:
# если = 1, то объект отправляется в проданные, если его не было в последней сессии
# если = 2, то объект отправляется в проданные, если его не было в последних 2 сессиях подряд и тд
SKIP_SESSIONS_COUNT = 4

DEBUGGER_HOST = "127.0.0.1"
DEBUGGER_PORT = 9222


RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"


# купить кв в Мск, сначала дешевые
# scan_url = https://bff-search-web.domclick.ru/api/offers/v1?address=1d1463ae-c80f-4d19-9331-a1b68a85b553&offset=0&limit=20&sort=price&sort_dir=asc&deal_type=sale&category=living&offer_type=layout&offer_type=flat&aids=2299&sale_price__gte=1000

# купить комнату в Мск, сначала дешевые 
# https://bff-search-web.domclick.ru/api/offers/v1?address=1d1463ae-c80f-4d19-9331-a1b68a85b553&offset=0&limit=20&sort=price&sort_dir=asc&deal_type=sale&category=living&offer_type=room&aids=2299&sale_price__gte=1000&disable_payment=true

# https://bff-search-web.domclick.ru/api/offers/v1?address=9930cc20-32c6-4f6f-a55e-cd67086c5171&offset=320&limit=20&sort=qi&sort_dir=desc&deal_type=sale&category=living&offer_type=house_part&aids=2298


# ===================== # ===================== #
"""
ЗАПУСК СКАНИРОВАНИЯ

1. Запустить браузер на нужном порту через командную строку
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile-9222

2. В открывшимся браузере открыть ссылку https://domclick.ru/

3. Перейти в папку 
cd ~/python

4. Создать и активировать виртуальное окружение 
python3 -m venv venv
source venv/bin/activate

5. Запустить сканирование. например,

Мск - продажа
python3 -m scan_domclick_v2.main flat-sale-msk && python3 -m scan_domclick_v2.main layout-sale-msk && python3 -m scan_domclick_v2.main room-sale-msk && python3 -m scan_domclick_v2.main house-sale-msk && python3 -m scan_domclick_v2.main house_part-sale-msk && python3 -m scan_domclick_v2.main townhouse-sale-msk && python3 -m scan_domclick_v2.main lot-sale-msk && python3 -m scan_domclick_v2.main garage-sale-msk && python3 -m scan_domclick_v2.main comm-sale-msk

Мск - аренда
python3 -m scan_domclick_v2.main flat-rent-msk && python3 -m scan_domclick_v2.main room-rent-msk && python3 -m scan_domclick_v2.main house-rent-msk && python3 -m scan_domclick_v2.main house_part-rent-msk && python3 -m scan_domclick_v2.main townhouse-rent-msk && python3 -m scan_domclick_v2.main garage-rent-msk && python3 -m scan_domclick_v2.main comm-rent-msk

МО - продажа
python3 -m scan_domclick_v2.main flat-sale-mo && python3 -m scan_domclick_v2.main layout-sale-mo && python3 -m scan_domclick_v2.main room-sale-mo && python3 -m scan_domclick_v2.main house-sale-mo && python3 -m scan_domclick_v2.main house_part-sale-mo && python3 -m scan_domclick_v2.main townhouse-sale-mo && python3 -m scan_domclick_v2.main lot-sale-mo && python3 -m scan_domclick_v2.main garage-sale-mo && python3 -m scan_domclick_v2.main comm-sale-mo

МО - аренда
python3 -m scan_domclick_v2.main flat-rent-mo && python3 -m scan_domclick_v2.main room-rent-mo && python3 -m scan_domclick_v2.main house-rent-mo && python3 -m scan_domclick_v2.main house_part-rent-mo && python3 -m scan_domclick_v2.main townhouse-rent-mo && python3 -m scan_domclick_v2.main garage-rent-mo && python3 -m scan_domclick_v2.main comm-rent-mo


список типов недвижимости хранится в таблице facetlar_v2:
- flat
- layout (новостройка. только продажа)
- room
- house
- house_part
- townhouse
- lot
- garage
- comm

"""