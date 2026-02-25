BOT_NAME = "wildberries_scan_scrapy"
SPIDER_MODULES = ["wildberries_scan_scrapy.spiders"]
NEWSPIDER_MODULE = "wildberries_scan_scrapy.spiders"
ROBOTSTXT_ENABLED = False

# в данном случае мы не используем прокси, поэтому будем спрашивать осторожно с интервалом.
# для задачи - отсканировать данные один раз - это окей
DOWNLOAD_DELAY = 3
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
ITEM_PIPELINES = {
    "wildberries_scan_scrapy.pipelines.ItemValidationPipeline": 200,
    "wildberries_scan_scrapy.pipelines.ExcelExportPipeline": 300,
}
