import pytest
from datetime import datetime
from flask import template_rendered
from main import create_my_app, db as _db
from models import Client, Parking, ClientParking


@pytest.fixture
def app():
    _app = create_my_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    with _app.app_context():
        _db.create_all()
        client_test = Client(
                    name="name",
                    surname="surname",
                    credit_card='credit_card',
                    car_number=1200336655)
        parking = Parking(
                          address="address",
                          opened=True,
                          count_places=200,
                          count_available_places=200)
        client_parking = ClientParking(
                                       client_id=1,
                                       parking_id=1,
                                       time_in=datetime.now())
        _db.session.add(client_test)
        _db.session.add(parking)
        _db.session.add(client_parking)
        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
