#!/bin/bash

# URL='https://www.migros.com.tr/carte-dor-isvicre-cikolatasi-karamel-muz-850-ml-p-b08bff'

# HEADERS=(
#   -H 'Referer: https://www.migros.com.tr/dondurma-c-41b?sayfa=3&sirala=onerilenler'
#   -H 'Upgrade-Insecure-Requests: 1'
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
#   -H 'sec-ch-ua: "Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"'
#   -H 'sec-ch-ua-mobile: ?0'
#   -H 'sec-ch-ua-platform: "Linux"'
# )

# # Бесконечный цикл
# while true; do
#   RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" "${HEADERS[@]}")
#   echo "Статус ответа: $RESPONSE"
#   #sleep 0.1
# done


while true; do
  curl 'https://bff-search-web.domclick.ru/api/offers/v1?address=1d1463ae-c80f-4d19-9331-a1b68a85b553&offset=0&limit=20&sort=qi&sort_dir=desc&deal_type=sale&category=living&offer_type=flat&offer_type=layout&aids=2299&rooms=1&sort_by_tariff_date=1' \
    -H 'Accept: application/json, text/plain, */*' \
    -H 'Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7' \
    -H 'Cache-Control: no-cache' \
    -H 'Connection: keep-alive' \
    -H 'Origin: https://domclick.ru' \
    -H 'Pragma: no-cache' \
    -H 'Referer: https://domclick.ru/' \
    -H 'Sec-Fetch-Dest: empty' \
    -H 'Sec-Fetch-Mode: cors' \
    -H 'Sec-Fetch-Site: same-site' \
    -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36' \
    -H 'sec-ch-ua: "Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"' \
    -H 'sec-ch-ua-mobile: ?0' \
    -H 'sec-ch-ua-platform: "Linux"'

  sleep 1
done