import scrapy
import json


class AlkotekaSpider(scrapy.Spider):
    name = "scan_alkoteka"
    allowed_domains = ["alkoteka.com"]

    # Список разделов которые будем сканировать
    facets = ["krepkiy-alkogol", "produkty-1", "slaboalkogolnye-napitki-2"]

    # Настройки для сохранения данных в output.json
    custom_settings = {
        "FEEDS": {
            "output.json": {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,  # перезаписываем итоговый файл при каждом запуске
                "indent": 4,  # форматирование JSON
            }
        },
        "FEED_EXPORT_ENCODING": "utf-8",
        "DOWNLOAD_DELAY": 0.5,  # интервал между запросами
        "ROBOTSTXT_OBEY": False,  # Отключаем проверку robots.txt для API, так как это не веб-страница
    }

    async def start(self):
        city_url = "https://alkoteka.com/web-api/v1/city"
        self.logger.info(f"Получим актуальный список городов по ссылке: {city_url}")
        yield scrapy.Request(url=city_url, callback=self.make_params)

    def make_params(self, response):
        """
        Подготовим параметры для формирования ссылки на продукты
        """
        try:
            data = response.json()
            city = data.get("meta", {}).get("accented", [])
            self.logger.info(
                f"Получили список основных городов: {city}"
            )  # полный список всех городов в узле data.results

            if not city:
                self.logger.warning("Не удалось получить список регионов")
                return

            self.logger.info(f"================================")
            self.logger.info(
                f"Список всех разделов по городам, которые мы собираемся сканировать:"
            )
            for item in city:
                city_uuid = item.get("uuid")
                city_name = item.get("name")
                if city_uuid:
                    for facet_slug in self.facets:
                        # начинаем с первой страницы для каждой комбинации город-фасет
                        self.logger.info(f"city: {city_name}, facet: {facet_slug}")
                        yield self.make_product_request(
                            city_uuid, facet_slug, page=1, city_name=city_name
                        )
                else:
                    self.logger.warning(f"Не удалось получить UUID для города: {item}")
            self.logger.info(f"================================")

        except json.JSONDecodeError:
            self.logger.error(
                f"Не удалось декодировать JSON из response city: {response.url}"
            )
        except Exception as e:
            self.logger.error(
                f"Упс! Что-то пошло не так при выполнении make_params {response.url}: {e}"
            )

    def make_product_request(self, city_uuid, facet_slug, page, city_name):
        """
        Выполняем запрос на получение продуктов
        """
        product_url = f"https://alkoteka.com/web-api/v1/product?city_uuid={city_uuid}&page={page}&per_page=20&root_category_slug={facet_slug}"

        return scrapy.Request(
            url=product_url,
            callback=self.parse_product,
            meta={
                "city_name": city_name,
                "city_uuid": city_uuid,
                "facet_slug": facet_slug,
                "current_page": page,
            },
        )

    def parse_product(self, response):
        """
        Обработка JSON'а с продуктами
        """
        city_name = response.meta["city_name"]
        city_uuid = response.meta["city_uuid"]
        facet_slug = response.meta["facet_slug"]
        current_page = response.meta["current_page"]

        try:
            data = response.json()
            product = data.get("results", [])
            meta_info = data.get("meta", {})
            has_more_pages = meta_info.get("has_more_pages", False)

            self.logger.info(
                f"city_uuid={city_uuid}, facet={facet_slug}, page={current_page}"
            )

            for item in product:
                # добавим город к каждому SKU (Для разных городов может быть разное кол-во и/или цена)
                item["city_name"] = city_name
                item["city_uuid"] = city_uuid
                yield item

            # переходим на следующую страницу
            if has_more_pages:
                next_page = current_page + 1
                self.logger.debug(
                    f"city_uuid={city_uuid}, facet={facet_slug}, next_page: {next_page}"
                )
                yield self.make_product_request(
                    city_uuid, facet_slug, next_page, city_name
                )

        except json.JSONDecodeError:
            self.logger.error(
                f"Не удалось декодировать JSON из response product: {response.url}"
            )
        except Exception as e:
            self.logger.error(
                f"Упс! Что-то пошло не так при выполнении parse_product {response.url}: {e}"
            )
