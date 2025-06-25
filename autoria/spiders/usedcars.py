import json

import scrapy
import re
from datetime import datetime

from db import db
from ..items import AutoRiaItem


class UsedcarsSpider(scrapy.Spider):
    name = "usedcars"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/car/used/"]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        spider.max_pages_to_crawl = crawler.settings.getint('SCRAPY_MAX_PAGES_TO_CRAWL', 99999)
        spider.max_car_detail_pages = crawler.settings.getint('SCRAPY_MAX_CAR_DETAIL_PAGES', 99999)

        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._current_page_number = 1  # start_urls is first page
        self._car_detail_pages_crawled = 0

    def parse(self, response: scrapy.http.Response) -> scrapy.http.Response:
        car_listing_links = response.css("div.content-bar a.m-link-ticket::attr(href)").getall()

        for car_url in car_listing_links:
            if self._car_detail_pages_crawled >= self.max_car_detail_pages:
                raise scrapy.exceptions.CloseSpider("car_detail_limit_reached_early")
            yield response.follow(car_url, callback=self.parse_car_details)

        if self._current_page_number < self.max_pages_to_crawl:
            # url to "Next page"
            next_page_link = response.css("span.page-item.next a:not(.disabled)::attr(href)").get()

            if next_page_link:
                self._current_page_number += 1
                self.logger.info(f"Next page URL: {next_page_link}. Page: {self._current_page_number}...")
                yield response.follow(next_page_link, callback=self.parse)

    def parse_car_details(self, response):
        title = response.css("h1.head::text").get()
        if not title or title.strip() == '':
            return

        self.logger.info(f"Parse auto url: {response.url}")
        self._car_detail_pages_crawled += 1

        item = AutoRiaItem()

        item["url"] = response.url
        item["title"] = title.strip()

        price_usd = response.css("div.price_value strong::text").get()
        item["price_usd"] = None
        if price_usd:
            item["price_usd"]: int = int(re.sub(r'[^\d]', '', price_usd))

        item["odometer"] = None
        odometer_str = response.css("div.base-information span.size18::text").get()
        if odometer_str:
            odometer = re.sub(r'[^\d]', '', odometer_str)
            try:
                item["odometer"]: int = int(odometer) * 1000
            except ValueError:
                pass

        item["username"] = (
                response.css("div.seller_info_name a::text").get() or
                response.css("div.seller_info_name::text").get() or
                response.css("h4.seller_info_name a::text").get()
        )
        if item["username"]:
            item["username"] = item["username"].strip()

        item["image_url"] = response.css("div#photosBlock picture img::attr(src)").get()
        item["images_count"]: int = len(response.css("div.photo-620x465")) - 1

        item["car_number"] = None
        if car_number_element := response.css("div.t-check span.state-num.ua::text").get():
            item["car_number"] = car_number_element.strip()

        item["car_vin"] = (
                response.css("div.t-check span.label-vin::text").get() or
                response.css("div.t-check span.vin-code::text").get()
        )
        if item["car_vin"]:
            item["car_vin"] = item["car_vin"].strip()

        item["datetime_found"] = datetime.now().isoformat()

        # Extract: data-hash , data-expires , data_auto_id for api phone
        script_element = response.css('script[class^="js-user-secure-"]')
        data_hash = None
        data_expires = None
        if script_element:
            data_hash = script_element.attrib.get("data-hash")
            data_expires = script_element.attrib.get("data-expires")

        data_auto_id = response.css("body::attr(data-auto-id)").get()

        if data_auto_id and data_hash and data_expires:
            api_phone = f"https://auto.ria.com/users/phones/{data_auto_id}?hash={data_hash}&expires={data_expires}"
            yield scrapy.Request(
                api_phone,
                callback=self.parse_phone_number,
                meta={"item": item, "download_delay": 2.5,}
            )
        else:
            item["phone_number"] = None
            yield item

        if self._car_detail_pages_crawled >= self.max_car_detail_pages:
            raise scrapy.exceptions.CloseSpider("car_detail_limit_reached")

    def parse_phone_number(self, response):
        item = response.meta["item"]

        item["phone_number"] = None
        try:
            phone_data = response.json().get("formattedPhoneNumber")
            if phone_data:
                item["phone_number"]: int = int('38' + re.sub(r'\D', '', phone_data))
        except (json.JSONDecodeError, AttributeError, TypeError, ValueError) as e:
            pass

        self.logger.info(item)
        yield item
