from sqlalchemy import exists
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime

from db.db import create_db_engine, create_tables
from db.models import Car


class AutoRiaPipeline:
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.Session = sessionmaker(bind=self.db_engine)
        self.session = None

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create pipeline instance with db settings from Scrapy settings.
        Returns db engine to __init__ pipeline instance.
        """
        db_type = crawler.settings.get("DB_TYPE", "pgsql")

        engine = create_db_engine(db_type)
        create_tables(engine)
        return cls(engine)

    def open_spider(self, spider):
        spider.logger.info("Open db connection Pipeline.")
        self.session = self.Session()

    def close_spider(self, spider):
        if self.session:
            spider.logger.info("Close db connection Pipeline.")
            self.session.close()

    def process_item(self, item, spider):
        try:
            datetime_found_obj = datetime.fromisoformat(item["datetime_found"])

            is_existing = self.session.scalar(exists().where(Car.url == item["url"]).select())
            spider.logger.info(f"DEBUG_DB: Checking existence for {item['url']}. Is existing: {is_existing}")

            if not is_existing:
                new_car = Car(
                    url=item["url"],
                    title=item["title"],
                    price_usd=item["price_usd"],
                    odometer=item["odometer"],
                    username=item["username"],
                    phone_number=item["phone_number"],
                    image_url=item["image_url"],
                    images_count=item["images_count"],
                    car_number=item["car_number"],
                    car_vin=item["car_vin"],
                    datetime_found=datetime_found_obj
                )
                self.session.add(new_car)
                self.session.commit()
                spider.logger.info(f"Car item: {item['url']} saved into db.")

        except IntegrityError:
            self.session.rollback()
            spider.logger.warning(f"Duplication db error. Skipped: {item['url']}")
        except SQLAlchemyError  as e:
            self.session.rollback()
            spider.logger.error(f"Database error for URL: {item['url']}: {e}", exc_info=True)

        return item
