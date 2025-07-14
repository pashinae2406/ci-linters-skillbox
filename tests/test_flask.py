import json
import pytest
import time
from datetime import datetime


@pytest.mark.parametrize("route",
                         ["/clients",
                          "/clients/1",
                          "/count/1",
                          "/client_parkings/1"])
def test_route_status(client, route):
    rv = client.get(route)
    assert rv.status_code == 200


def test_create_client(client):
    """Создание клиента"""

    client_data = {'name': 'name',
                   'surname': 'surname',
                   'credit_card': 'test_card',
                   'car_number': 1111111111}
    resp = client.post('/clients', json=client_data)
    assert resp.status_code == 201


def test_create_parking(client):
    """Создание парковки"""
  
    parking_data = {'address': 'address',
                    'opened': True,
                    'count_places': 200}
    resp = client.post('/parkings', json=parking_data)
    assert resp.status_code == 201


def test_parking_in(client):
    """Заезд на парковку"""

    client_data = {'name': 'name',
                   'surname': 'surname',
                   'credit_card': 'test_card',
                   'car_number': 1111111111}
    client_test = client.post('/clients', json=client_data)
    parking_data = {'address': 'test_address',
                    'opened': True,
                    'count_places': 150}
    parking_test = client.post('/parkings', json=parking_data)
    count_available_start = int(json.loads(
        parking_test.text)['count_available_places'])
    data_parking = {'client_id': json.loads(client_test.text)['id'],
                    'parking_id': json.loads(parking_test.text)['id']}
    resp = client.post('/client_parkings', json=data_parking)
    count_available_end = client.get(f'/count/{data_parking['parking_id']}')

    assert resp.status_code == 201
    assert json.loads(
      count_available_end.text)['count'] == count_available_start - 1


def test_parking_closed(client):
    """Проверка открыта/закрыта парковка"""

    client_data = {'name': 'name',
                   'surname': 'surname',
                   'credit_card': 'test_card',
                   'car_number': 1111111111}
    client_test = client.post('/clients', json=client_data)
    parking_data = {'address': 'test_address',
                    'opened': False,
                    'count_places': 150}
    parking_test = client.post('/parkings', json=parking_data)
    data_parking = {'client_id': json.loads(client_test.text)['id'],
                    'parking_id': json.loads(parking_test.text)['id']}
    resp = client.post('/client_parkings', json=data_parking)

    assert resp.text == (f'Парковка по адресу '
                         f'{parking_data['address']} закрыта.')


def test_parking_out(client):
    """Выезд с парковки"""

    client_data = {'name': 'name',
                   'surname': 'surname',
                   'credit_card': 'test_card',
                   'car_number': 1111111111}
    client_test = client.post('/clients', json=client_data)
    parking_data = {'address': 'test_address',
                    'opened': True,
                    'count_places': 150}
    parking_test = client.post('/parkings', json=parking_data)
    data_parking = {'client_id': json.loads(client_test.text)['id'],
                    'parking_id': json.loads(parking_test.text)['id']}
    client_parking = client.post('/client_parkings', json=data_parking)
    count_available = client.get(f'/count/{data_parking['parking_id']}')
    count_available_start = int(json.loads(count_available.text)['count'])

    client_parking_in = json.loads(client_parking.text)
    client_parking_in_date = datetime.strptime(
        client_parking_in['time_in'][5:-4], '%d %b %Y %H:%M:%S')
    time.sleep(3)

    resp = client.delete('/client_parkings', json=data_parking)
    client_parking_out = client.get(
      f'/client_parkings/{client_parking_in['id']}')
    client_parking_out_date = datetime.strptime(
        json.loads(client_parking_out.text)['time_out'][5:-4],
        '%d %b %Y %H:%M:%S')

    count_available_end = client.get(
        f'/count/{data_parking['parking_id']}')
    assert resp.status_code == 200
    assert resp.text == (f"Клиент {json.loads(client_test.text)['name']} "
                         f"{json.loads(client_test.text)['surname']} "
                         f"покинул парковку по адресу "
                         f"{json.loads(parking_test.text)['address']}")
    assert client_parking_out_date > client_parking_in_date
    assert json.loads(
      count_available_end.text)['count'] == count_available_start + 1


def test_card(client):
    """Проверка карты клиента"""
  
    client_data = {'name': 'name',
                   'surname': 'surname',
                   'credit_card': 'test_card'}
    client_test = client.post('/clients', json=client_data)
    parking_data = {'address': 'test_address',
                    'opened': True,
                    'count_places': 150}
    parking_test = client.post('/parkings', json=parking_data)
    data_parking = {'client_id': json.loads(client_test.text)['id'],
                    'parking_id': json.loads(parking_test.text)['id']}
    client_parking = client.post('/client_parkings', json=data_parking)
    time.sleep(3)
    if client_parking:
      resp = client.delete('/client_parkings', json=data_parking)
    assert resp.status_code == 404
    assert resp.text == (f'У клиента {client_data['name']} '
                         f'{client_data['surname']} не привязана '
                         f'карта или указаны неверные данные.')
