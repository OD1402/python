import scrapy
import json
import math

from urllib.parse import urlencode
from scrapy.exceptions import CloseSpider

from ..items import (
    SourceDataItem,
    ResultDataItem,
)

SOURCE_FILE = "source.json"
RESULT_FILE = "result.json"


class AlkotekaSpider(scrapy.Spider):
    name = "scan_alkoteka"

    CITY_URL = "https://alkoteka.com/web-api/v1/city"
    BASE_PRODUCT_URL = "https://alkoteka.com/web-api/v1/product"
    FACETS = [
        "krepkiy-alkogol",
        "produkty-1",
        "slaboalkogolnye-napitki-2",
    ]  # "krepkiy-alkogol", "produkty-1", "slaboalkogolnye-napitki-2"
    PER_PAGE = 20
    # PER_PAGE - Количество товаров на странице по умолчанию 20,
    # API выдает и больше за 1 запрос, но будем запрашивать по 20, чтобы это выглядело максимально "человечно"

    # Настройки для сохранения данных в файлы
    custom_settings = {
        "FEEDS": {
            SOURCE_FILE: {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,
                "store_empty": False,
                "item_export_kwargs": {
                    "ensure_ascii": False,  # Важно для кириллицы
                },
                "indent": 4,  # форматирование JSON для удобства чтения глазами
                # Указываем, какие Item классы должны идти в этот файл
                "item_classes": [SourceDataItem],
            },
            RESULT_FILE: {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,
                "store_empty": False,
                "item_export_kwargs": {
                    "ensure_ascii": False,  # Важно для кириллицы
                },
                "indent": 4,  # форматирование JSON для удобства чтения глазами
                # Указываем, какие Item классы должны идти в этот файл
                "item_classes": [ResultDataItem],
            },
        },
        "DOWNLOAD_DELAY": 0.5,  # Задержка между запросами для вежливости
        "CONCURRENT_REQUESTS": 8,  # Количество одновременных запросов
        "LOG_LEVEL": "INFO",  # Уровень логирования
    }

    def __init__(self, city_name=None, *args, **kwargs):
        super(AlkotekaSpider, self).__init__(*args, **kwargs)
        if not city_name:
            raise ValueError(
                'Укажите название города с помощью аргумента --city_name. Написание города должно быть как на сайте https://alkoteka.com/ \nНапример: \nscrapy crawl scan_alkoteka -a --city_name="Ленинградская ст-ца"'
            )
        self.target_city_name = city_name
        self.city_uuid = None
        self.logger.info(f"Запускаем сбор данных для города: {self.target_city_name}")

    # Начальная точка для запросов - поиск города
    async def start(self):
        self.logger.info(f"Начинаем поиск UUID для города '{self.target_city_name}'...")
        params = {"page": 1}
        yield scrapy.Request(
            url=f"{self.CITY_URL}?{urlencode(params)}",
            callback=self.parse_city_pages,
            meta={"page": 1},
        )

    # Парсинг страниц со списком городов
    def parse_city_pages(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Не удалось декодировать JSON для {response.url}")
            return

        results = data.get("results", [])
        for city in results:
            if city.get("name") == self.target_city_name:
                self.city_uuid = city.get("uuid")
                self.logger.info(
                    f"Найден город '{self.target_city_name}' с UUID: {self.city_uuid}"
                )
                # Город нашли, начинаем сканить листы
                yield from self.get_product_list()

        # Если город не найден на текущей странице, проверяем наличие следующей
        if data.get("meta").get("has_more_pages"):
            current_page = response.meta["page"]
            next_page = current_page + 1
            params = {"page": next_page}
            yield scrapy.Request(
                url=f"{self.CITY_URL}?{urlencode(params)}",
                callback=self.parse_city_pages,
                meta={"page": next_page},
            )
        else:
            self.logger.error(
                f"Город '{self.target_city_name}' не найден после проверки всех страниц городов. Проверьте правильность написания города на сайте https://alkoteka.com/"
            )

    def get_product_list(self):
        """
        Инициируем запросы к листам продуктов для каждого раздела facet.
        """
        if not self.city_uuid:
            self.logger.error(
                "UUID города не найден, невозможно продолжить сбор данных о продуктах."
            )
            return

        self.logger.info(
            f"Начинаем сбор данных о продуктах для UUID города: {self.city_uuid}"
        )
        for facet in self.FACETS:
            # Начинаем с первой страницы для каждого раздела
            params = {
                "city_uuid": self.city_uuid,
                "page": 1,
                "per_page": self.PER_PAGE,
                "root_category_slug": facet,
            }
            product_url = f"{self.BASE_PRODUCT_URL}?{urlencode(params)}"
            self.logger.info(
                f"Запрашиваем первую страницу продуктов для раздела '{facet}': {product_url}"
            )
            yield scrapy.Request(
                url=product_url,
                callback=self.parse_product_list,
                meta={"facet": facet, "page": 1},
            )

    def parse_product_list(self, response):
        """
        Парсим листы со списком продуктов - переходим в карточки, перебираем страницы листов 
        """
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(
                f"Не удалось декодировать JSON со списком продуктов URL: {response.url}"
            )
            return

        results = data.get("results", [])
        current_page = data.get("meta").get("current_page")
        facet = response.meta["facet"]

        self.logger.info(
            f"page: {current_page}, facet: '{facet}'. Найдено {len(results)} продуктов.\n"
        )

        for product_preview in results:
            slug = product_preview.get("slug")
            product_url = product_preview.get("product_url")
            if slug is None:
                raise ValueError(
                    "Не удалось получить slug карточки из листа, не можем сформировать ссылку на карточку"
                )
            else:
                card_url = (
                    f"https://alkoteka.com/web-api/v1/product/{slug}?"
                    f"city_uuid={self.city_uuid}"
                )
                self.logger.info(  # возможно стоит заменить на debug
                    f"Карточка: {card_url}"
                )
                yield scrapy.Request(
                    url=card_url,
                    callback=self.parse_product_card,
                    meta={  # product_url - ссылка на карточку на сайте. пробросим ее дальше, так как в выдаче карточек нет этой ссылки
                        "product_url": product_url
                    },
                )

        # Если есть следующая страница, запрашиваем ее
        if data.get("meta").get("has_more_pages"):
            next_params = {
                "city_uuid": self.city_uuid,
                "page": current_page + 1,
                "per_page": self.PER_PAGE,
                "root_category_slug": facet,
            }
            next_page_url = f"{self.BASE_PRODUCT_URL}?{urlencode(next_params)}"
            self.logger.info(
                f"Переходим на следующую страницу продуктов {current_page + 1} для раздела '{facet}': {next_page_url}"
            )
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_product_list,
                meta={"facet": facet, "page": current_page + 1},
            )

    def parse_product_card(self, response):
        """
        Парсим карточки, сохраняем в исходном и преобразованном виде.
        """

        try:
            original_data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(
                f"Не удалось декодировать JSON с деталями продукта URL: {response.url}"
            )
            return

        # сохраним сорсы
        source_item = SourceDataItem()
        source_item["source_item"] = original_data
        yield source_item

        # product_url = response.meta["product_url"]

        # Преобразуем данные
        transformed_data_dict = self.transform_product_card(
            response.meta["product_url"], response.url, original_data
        )

        # Создаем экземпляр ResultDataItem и заполняем его
        result_item = ResultDataItem()
        # Заполняем поля ResultDataItem из преобразованного словаря
        for key, value in transformed_data_dict.items():
            if key in result_item.fields:  # Проверяем, есть ли такое поле в Item
                result_item[key] = value

        yield result_item

    def transform_product_card(self, product_url, response_url, data):
        """
        Преобразует исходный JSON товара в новый формат (словарь).
        Этот словарь используем для заполнения ResultDataItem.
        """
        data_results = data.get("results")

        obem = next(
            (
                item
                for item in data_results.get("filter_labels")
                if item.get("filter") == "obem"
            ),
            None,
        )

        # ######################## Маркетинг таг "Скидка" отсутствует в самой карточке, но присутствует в плитке этой карточки в листе, поэтому добавим
        marketing_tags = []
        target_filters = {"tovary-so-skidkoi", "dopolnitelno"}
        marketing_tags.extend(
            item.get("title")
            for item in data_results.get("filter_labels")
            if item.get("filter") in target_filters
        )

        # ######################## Бренды
        brend_list = None
        brend = next(
            (
                item
                for item in data_results.get("description_blocks")
                if item.get("title") == "Бренд"
            ),
            None,
        )
        if brend is not None:
            # в исходном json у элемента brend есть values - это массив, при точечной проверке я не нашла ни одного товара более чем с одним брендом, однако массив предполагает наличие более одного элемента
            brend_values = brend.get("values")
            enabled_names = [
                str(item["name"]) for item in brend_values if item["enabled"]
            ]
            brend_list = ", ".join(enabled_names)

        ########################
        metadata = {}
        for block in data_results.get("description_blocks"):
            # возьмем code в качестве ключа, но вообще это дурной тон использовать в рамках одной сущности (результирующего объекта) одновременно и английские наименовая и транслит.
            code = block["code"]
            block_type = block["type"]

            unit = block.get(
                "unit", ""
            ).strip()  # обрежем пробелы, так как для литров они есть, а для процентов и градусов - нет

            if block_type == "select":
                # Проверяем, что values существует, не пуст и содержит name
                if (
                    "values" in block
                    and block["values"]
                    and "name" in block["values"][0]
                ):
                    metadata[code] = (f"{block['values'][0]['name']} {unit}").strip()
            elif block_type == "range":
                if block.get("min") and block.get("max"):
                    if block.get("min") == block.get("max"):
                        metadata[f"{code}"] = f"{block['min']} {unit}"
                    else:
                        metadata[f"{code}_min"] = f"{block['min']} {unit}"
                        metadata[f"{code}_max"] = f"{block['max']} {unit}"
        metadata["__description"] = next(
            (
                block.get("content")
                for block in data_results.get("text_blocks")
                if block.get("title") == "Описание"
            ),
            None,
        )
        metadata["article"] = data_results.get("vendor_code")
        metadata["uuid"] = data_results.get("uuid")
        metadata["new"] = data_results.get("new")

        ########################
        transformed = {
            # RPC по описанию формата "Уникальный код товара."
            # В исходных данных есть артикул и uuid, возьмем артикул (vendor_code)
            "RPC": data_results.get(
                "vendor_code"
            ),
            # "url": f"https://alkoteka.com/product/{category_slug}/{card_slug}",
            "url": product_url,
            "title": (
                f"{data_results.get('category').get('name')}, "
                f"{data_results.get('name')}"
                f"{', ' + obem.get('title') if obem and obem.get('title') else ''}"
            ),
            "marketing_tags": marketing_tags,
            "brand": brend_list,
            "section": [
                "Главная",
                data_results.get("category").get("parent").get("name"),
                data_results.get("name"),
            ],
            "price_data": {
                "current": data_results.get(
                    "price"
                ),  # Цена со скидкой, если скидки нет то = original.
                "original": data_results.get("prev_price")
                or data_results.get(
                    "price"
                ),  # в prev_price находится основная цена для товаров со скидкой, для товаров без скидки основная цена в поле price
                "sale_tag": (
                    f"Скидка {math.ceil(100 - ((data_results.get('price') / data_results.get('prev_price')) * 100))}%"
                    if data_results.get("prev_price")
                    else None
                ),
            },
            "stock": {
                "in_stock": (
                    True if data_results.get("quantity_total") else False
                ),  # Есть товар в наличии в магазине или нет.
                "count": data_results.get(
                    "quantity_total", 0
                ),  # Если есть возможность получить информацию о количестве оставшегося товара в наличии, иначе 0.
            },
            "assets": {
                "main_image": data_results.get("image_url"),
                "set_images": [
                    data_results.get("image_url")
                ],  # в данном случае фотка всегда одна
                "view360": [],
                "video": [],
            },
            "metadata": metadata,
            "variants": None,
        }

        try:
            # Проверяем заполненность обязательных полей на случай изменения формата выдачи АПИ Алкотеки (пополнить список при необходимости)
            required_fields = {
                "url": transformed.get("url"),
                "title": transformed.get("title"),
                "section": transformed.get("section"),
                "price_data_current": transformed.get("price_data", {}).get("current"),
            }

            for field_name, field_value in required_fields.items():
                if not field_value:
                    raise ValueError(
                        f"Поле '{field_name}' не заполнено в карточке response_url: {response_url}"
                    )
                else:
                    return transformed

        except ValueError as e:
            self.logger.error(str(e))
            # стоп кравлер
            raise CloseSpider(f"Критическая ошибка: {str(e)}")