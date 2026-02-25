
SEARCH_TERMS = [
    'пальто из натуральной шерсти',
    # 'кофе',
    # 'я водитель нло'
]

# цену и страну производства будем пока что считать базовыми параметрами, так как у нас нет полной картины - как обычно выглядят запросы клиентов
API_SEARCH_URL = "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1257786&f14177451=15000203&hide_vflags=4294967296&inheritFilters=false&lang=ru&page={page}&priceU=60400%3B1000000&query={query}&resultset=catalog&sort=rate&spp=30&suppressSpellcheck=false"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",    
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-requested-with': 'XMLHttpRequest',
    'x-spa-version': '13.24.6',
    'x-userid': '0',
}

# x_wbaas_token живет предположительно несколько дней
# каждые нескольк дней его нужно обновлять вручную, алгоритм автоматического получения токена пока не делаем, так как это тестовое задание
COOKIES = {
    'x_wbaas_token': '1.1000.ccc9781d91ae4f33b36e166472669a52.MHw1LjIyOC4xMTMuMnxNb3ppbGxhLzUuMCAoWDExOyBMaW51eCB4ODZfNjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNDQuMC4wLjAgU2FmYXJpLzUzNy4zNnwxNzcyOTAzNzQ5fHJldXNhYmxlfDJ8ZXlKb1lYTm9Jam9pSW4wPXwwfDN8MTc3MjI5ODk0OXwx.MEUCIQDJ7t6gOKZdJGsUGXAcY1OqKirdPNI07LoXEdlEJvdn2gIgUHl3D3ht2CBqF6h2FDWJtA8WN9tz4U0SbhMFpMn7yGw=',
    # 'routeb': '1771694151.298.74.547277|3c1054d09865b256a0b95190d0b86bd8',
    # '_wbauid': '4843252531771694150',
    # 'wbx-validation-key': '211bb496-3c3a-43bd-aa5f-f2ba9862a9f4',
    # '_cp': '1',
}


# https://www.wildberries.ru/catalog/173989115/detail.aspx
API_ITEM_URL = "https://basket-{basket_num}.wbbasket.ru/vol{vol_num}/part{part_num}/{item_id}/info/ru/card.json"

# https://basket-12.wbbasket.ru/vol1739/part173989/173989115/images/big/1.webp
PHOTO_URL = 'https://basket-{basket_num}.wbbasket.ru/vol{vol_num}/part{part_num}/{item_id}/images/big/{photo_num}.webp'

ITEM_URL = "https://www.wildberries.ru/catalog/{item_id}/detail.aspx"
SELLER_URL = "https://www.wildberries.ru/seller/{seller_id}"


# !!!!!!!!!!!!!!!!!!!
# это заглушка
# здесь должны быть данные с определенными числами
WB_API_CONSTS = [11, 22, 33]
