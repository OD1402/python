import scrapy
from scrapy import Request
import json

from ..constants.wildberries import *


"""
браузер
https://www.wildberries.ru/catalog/0/search.aspx?page=1&sort=rate&search=%D0%BF%D0%B0%D0%BB%D1%8C%D1%82%D0%BE+%D0%B8%D0%B7+%D0%BD%D0%B0%D1%82%D1%83%D1%80%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D0%B9+%D1%88%D0%B5%D1%80%D1%81%D1%82%D0%B8&priceU=60400%3B1000000&f14177451=15000203

api
https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1257786&f14177451=15000203&hide_vflags=4294967296&inheritFilters=false&lang=ru&page=1&priceU=60400%3B1000000&query=%D0%BF%D0%B0%D0%BB%D1%8C%D1%82%D0%BE+%D0%B8%D0%B7+%D0%BD%D0%B0%D1%82%D1%83%D1%80%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D0%B9+%D1%88%D0%B5%D1%80%D1%81%D1%82%D0%B8&resultset=catalog&sort=rate&spp=30&suppressSpellcheck=false

на одной странице 100 товаров
"""



class WildberriesParser():

    def get_item_id(self, resp_json):
        item_id = resp_json.get('id')
        if item_id:
            return item_id

    def get_item_url(self, resp_json):
        item_id = resp_json.get('id')
        if item_id:
            item_url = ITEM_URL.format(item_id=item_id)
            return item_url 
    
    def get_item_price(self, resp_json):
        # у разных вариантов цветов и размеров может быть разная цена, 
        # но так как по ТЗ нет задачи парсить варианты товаров, возьмем пока цену первого варианта в списке 
        price = resp_json.get('sizes', [])[0].get('price', {}).get('product')
        if price:
            price = price / 100
            return price
       

    def get_item_seller_url(self, resp_json):
        seller_id = resp_json.get('supplierId')
        if seller_id:
            seller_url = SELLER_URL.format(seller_id=seller_id)
            return seller_url
                                           

    def get_item_sizes(self, resp_json):
        # name: "46-48",
        # origName: "L",

        # требуется более детальная нормализация, так как иногда обозначения перекликаются в name и origName, например "44-46" и "44"
        result = []
        sizes = resp_json.get('sizes', [])
        
        if not sizes:
            self.logger.error(f"Не смогли получить sizes")
        
        for size in sizes:
            size_num = size.get('name')
            size_text = size.get('origName')
            if not size_num and not size_text:
                self.logger.error(f"Не нашли размеры")
                continue
            if size_num and size_text and size_num == size_text:
                size_all = size_num
            else:
                size_all = ' '.join(x for x in [size_num, size_text] if x)
            result.append(size_all)

        result = ', '.join(result)
        return result
    

    def get_item_options(self, resp_json):
        result = {}
        options = resp_json.get('options', [])
        for option in options:
            name = option.get('name')
            value = option.get('value')
            if name and value:
                result[name] = value
        return result
    

    def _get_basket_number(self, last_5):
        # !!!!!!!!!!!!!!!!!!!
        # это заглушка
        # номер баскета необходимо вычислить по определенному алгоритму
        basket = 66666
        return basket


    def get_item_api_url_params(self, item_id):
        item_id = str(item_id)
        last_5 = item_id[:-5] # 34439760 -> 344
        last_3 = item_id[:-3] # 34439760 -> 34439
        basket = self._get_basket_number(last_5)
        return basket, last_5, last_3


    def get_item_api_url(self, item_id):
        basket, last_5, last_3 = self.get_item_api_url_params(item_id)
        api_url = API_ITEM_URL.format(basket_num=basket, vol_num=last_5, part_num=last_3, item_id=item_id)
        return api_url


    def get_item_photo(self, resp_json, item_id):
        result = []

        item_id = str(item_id)
        photo_counts = resp_json.get('media', {}).get('photo_count')

        last_5 = item_id[:-5]
        last_3 = item_id[:-3]
        basket = self._get_basket_number(last_5)

        if photo_counts:
            for photo_num in range(1, photo_counts + 1):
                photo_url = PHOTO_URL.format(basket_num=basket, vol_num=last_5, part_num=last_3, item_id=item_id, photo_num=photo_num)
                result.append(photo_url)
        else:
            photo_url = PHOTO_URL.format(basket_num=basket, vol_num=last_5, part_num=last_3, item_id=item_id, photo_num=1)
            result.append(photo_url)

        result = ', '.join(result)
        return result
    


class WildberriesSpider(scrapy.Spider, WildberriesParser):
    name = "wildberries"

    def start_requests(self):
        for term in SEARCH_TERMS:
            url = API_SEARCH_URL.format(page=1, query=term)
            yield Request(url=url, headers=HEADERS, cookies=COOKIES, 
                          callback=self.parse_list, meta={"page": 1, "term": term})


    def parse_list(self, response):
        next_meta = response.meta
        try:
            resp_json = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Не удалось декодировать JSON для листа {response.url}")
            return

        items = resp_json.get('products')

        items_count = len(items)
        if not items_count:
            self.logger.debug("Дошли доконца выборки")
            return
        else:
            self.logger.debug(f"Получено карточек: {items_count}")

            next_page = response.meta['page'] + 1
            next_url = API_SEARCH_URL.format(page=next_page, query=response.meta['term'])

            next_meta['page'] = next_page
            yield Request(url=next_url, headers=HEADERS, cookies=COOKIES, 
                        callback=self.parse_list, meta=next_meta)

        for item in items:
            item_res = {}

            item_id = self.get_item_id(item)
            item_res['url'] = self.get_item_url(item)
            item_res['article'] = item_id
            item_res['name'] = item.get('name')
            item_res['price'] = self.get_item_price(item)
            item_res['seller_name'] = item.get('supplier')
            item_res['seller_url'] = self.get_item_seller_url(item)
            item_res['sizes'] = self.get_item_sizes(item)
            item_res['stock'] = item.get('totalQuantity')
            item_res['rating'] = item.get('reviewRating')
            item_res['review_count'] = item.get('feedbacks')

            next_meta['item'] = item_res

            item_api_url = self.get_item_api_url(item_id)
            if "66666" not in item_api_url: # !!!!!!!!!!!!!!!!!!! 66666 - это заглушка
                yield Request(url=item_api_url, headers=HEADERS, cookies=COOKIES, 
                          callback=self.parse_card, meta=next_meta)
            else:
                yield item_res

    
    def parse_card(self, response):
        try:
            resp_json = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Не удалось декодировать JSON для карточки {response.url}")
            return
        
        item = response.meta['item']
        item['description'] = resp_json.get('description')
        item['options'] = self.get_item_options(resp_json)
        item['photo'] = self.get_item_photo(resp_json, item['article'])

        yield item

