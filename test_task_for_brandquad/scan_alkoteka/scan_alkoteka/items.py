import scrapy
import datetime


class SourceDataItem(scrapy.Item):
    """
    исходный JSON
    """

    source_item = scrapy.Field()


class ResultDataItem(scrapy.Item):
    """
    итоговый JSON
    """

    timestamp = scrapy.Field()
    RPC = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    marketing_tags = scrapy.Field()
    brand = scrapy.Field()
    section = scrapy.Field()
    price_data = scrapy.Field()
    stock = scrapy.Field()
    assets = scrapy.Field()
    metadata = scrapy.Field()
    variants = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # вызываем конструктор родительского класса

        # Устанавливаем значение timestamp, если оно не было передано явно
        if "timestamp" not in self:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            self["timestamp"] = int(now_utc.timestamp() * 1000)
