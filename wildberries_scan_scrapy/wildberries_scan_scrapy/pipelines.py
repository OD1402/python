import os
# from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
import pandas as pd


class ItemValidationPipeline:
    """
    Валидация полей в item - проверяем наличие обязательных полей 
    Выкидывать карточки не будем, так как лучше иметь хоть какие-то данные, чем никаких
    """
    
    FIELDS = [
        'url',
        'article',
        'name',
        'price',
        'seller_name',
        'seller_url',
        'sizes',
        'stock',
        'photo',

        # остальных полей в теории может быть 
        #'rating',
        #'review_count',
        #'description',
        #'options',
    ]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def __init__(self, crawler):
        self.crawler = crawler
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)
        
        missing_fields = []
        for field in self.FIELDS:
            value = item_dict.get(field)
            if not value:
                missing_fields.append(field)
        
        if missing_fields:
            spider.logger.warning(
                f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
            )
        
        return item



class ExcelExportPipeline:
    def __init__(self):
        self.items = []
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.excel_file = os.path.join(self.project_root, 'wb_result.xlsx')

    def process_item(self, item):
        # Преобразуем item в словарь
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)
        
        processed_dict = {}
        for key, value in item_dict.items():
            # поле option тоже можно развернуть, но не знаю нужно ли, пока не будем
            # if isinstance(value, dict):
            #     processed_dict[key] = str(value)
            processed_dict[key] = value
        
        self.items.append(processed_dict)
        return item

    def close_spider(self, spider):
        if self.items:
            df = pd.DataFrame(self.items)
            df.to_excel(self.excel_file, index=False, engine='openpyxl')
            spider.logger.info(f'Сохранено {len(self.items)} записей в {self.excel_file}')
        else:
            spider.logger.warning('Нет данных для сохранения')