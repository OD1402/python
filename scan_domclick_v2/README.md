# О программе

Программа для выполнения fetch запросов через Selenium + Chrome DevTools Protocol.




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


## Настройка среды

**1. Установить Python**

Версия 3.10 или выше
В Убунте 24 он уже есть.
<br>Проверить версию:
```
python3 --version
```

**2. Установить виртуальное окружение для Питона**
```
sudo apt install python3-venv -y
```

**3. Перейти в папку**
```
cd ~/python
```

**4. Создать в этой папке виртуальное окружение**
```
python3 -m venv venv
```
После выполнения команды появится папка "venv/."

**5. Активировать виртуальное окружение**
```
source venv/bin/activate
```
В начале строки терминала должно появиться (venv).

**6. Установить Python зависимости**
```
pip install --upgrade pip
pip install -r requirements.txt
```



## Запуск сканирования

**1. Запустить браузер на нужном порту через командную строку**
```
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile-9222
```

**2. В открывшимся браузере открыть ссылку**
```
https://domclick.ru/
```

**3. Перейти в папку**
```
cd ~/python
```

**4. Активировать виртуальное окружение**
```
source venv/bin/activate
```

**5. Запустить сканирование**
например,

Мск - продажа
python3 -m scan_domclick_v2.main flat-sale-msk && python3 -m scan_domclick_v2.main layout-sale-msk && python3 -m scan_domclick_v2.main room-sale-msk && python3 -m scan_domclick_v2.main house-sale-msk && python3 -m scan_domclick_v2.main house_part-sale-msk && python3 -m scan_domclick_v2.main townhouse-sale-msk && python3 -m scan_domclick_v2.main lot-sale-msk && python3 -m scan_domclick_v2.main garage-sale-msk && python3 -m scan_domclick_v2.main comm-sale-msk


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