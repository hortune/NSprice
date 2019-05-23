from nsprice.items import NspriceItem

import scrapy
import logging

class GameSaleSpider(scrapy.Spider):
    name = 'gamesale'
    allowed_domains = ['ptt.cc']
    _pages = 0
    MAX_PAGES = 4
    general_tag = None
    def start_requests(self):

        url = 'https://www.ptt.cc/bbs/Gamesale/'
        tag = getattr(self, 'tag', None)

        assert tag is not None
        url = url + 'search?q=' + tag
        self.general_tag = tag
        yield scrapy.Request(url, self.parse)

    def parse(self, response):
        self._pages += 1
        for href in response.css('.r-ent > div.title > a::attr(href)'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse_post)

        if self._pages < self.MAX_PAGES:
            next_page = response.xpath(
                '//div[@id="action-bar-container"]//a[contains(text(), "上頁")]/@href')
            if next_page:
                url = response.urljoin(next_page[0].extract())
                logging.warning('follow {}'.format(url))
                yield scrapy.Request(url, self.parse)
            else:
                logging.warning('no next page')
        else:
            logging.warning('max pages reached')

    def parse_post(self, response):
        item = NspriceItem()
        item['link'] = response.url
        item['source'] = 'ptt'
        content = response.xpath('//div[@id="main-content"]')[0]
        candidate_prices = content.xpath('text()').re('\d+')

        for ele in content.xpath('//div[@class="article-metaline"]'):
            if ele.xpath('./span[@class="article-meta-tag"]/text()')[0].get().strip() == "標題":
                item['title'] = ele.xpath('./span[@class="article-meta-value"]/text()')[0].get().strip()

        if candidate_prices:
            price_list = list(filter(lambda x: 100 < x < 5000, map(int, candidate_prices)))
            
            passage = "---".join(content.xpath('text()').getall())
            for price in price_list:
                index = passage.index(str(price))

                if "價" in passage[index-13:index] or (len(set(passage[index-13:index]) & set(self.general_tag))):
                    item['price'] = price
                    break

        item['sell'] = "徵" not in item['title']

        yield item
