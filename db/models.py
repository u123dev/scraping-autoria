from sqlalchemy import Column, Integer, String, DateTime, BigInteger

from .db import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    price_usd = Column(Integer)
    odometer = Column(Integer)
    username = Column(String)
    phone_number = Column(BigInteger)
    image_url = Column(String)
    images_count = Column(Integer)
    car_number = Column(String)
    car_vin = Column(String)
    datetime_found = Column(DateTime)

    def __repr__(self):
        return (f"<Car(title='{self.title}' | price_usd={self.price_usd}, "
                f"url='{self.url}' | added_at='{self.datetime_found}')>")
