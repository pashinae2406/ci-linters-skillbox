import factory
import factory.fuzzy as fuzzy
import random

from main import db
from models import Client, Parking


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker('first_name')
    surname = factory.Faker('last_name')
    credit_card = fuzzy.FuzzyChoice(["Есть карта", None])
    car_number = fuzzy.FuzzyText(length=10)


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = factory.Faker('address')
    opened = fuzzy.FuzzyChoice([True, False])
    count_places = fuzzy.FuzzyInteger(low=100, high=500)
    count_available_places = factory.LazyAttribute(
        lambda x: random.randrange(100, 500))
