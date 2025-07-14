from .factories import ClientFactory, ParkingFactory
from models import Client, Parking


def test_create_client(app, db):
    client_test = ClientFactory()
    db.session.commit()
    assert client_test.id is not None
    assert len(db.session.query(Client).all()) == 2


def test_create_parking(client, db):
    parking = ParkingFactory()
    db.session.commit()
    assert parking.id is not None
    assert len(db.session.query(Parking).all()) == 2
