from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from datetime import datetime
from models import db, Client, Parking, ClientParking


def create_my_app():
    """Создание приложения"""

    app = Flask(__name__, instance_relative_config=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///parking.db'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    @app.before_request
    def before_request_func():
        db.create_all()
        db.session.commit()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    @app.route('/clients', methods=['GET', 'POST'])
    def get_clients():
        """Роут для полученя списка клиентов и создания нового клиента"""

        if request.method == 'GET':
            result = db.session.scalars(select(Client))
            clients: list = result.fetchall()
            list_clients: list = [client.to_json() for client in clients]
            db.session.close()
            return list_clients

        elif request.method == 'POST':
            data = request.json
            client = Client(
                name=data.get('name'),
                surname=data.get('surname'),
                credit_card=data.get('credit_card'),
                car_number=data.get('car_number')
            )
            db.session.add(client)
            db.session.commit()
            result = db.session.execute(select(Client).filter(
                Client.id == client.id))
            db.session.close()
            return result.fetchone()[0].to_json(), 201

        else:
            return "Нет данных"

    @app.route('/clients/<client_id>', methods=['GET'])
    def get_client_id(client_id) -> dict:
        """Роут для получения страницы клиента"""

        result = db.session.execute(select(Client).filter(
            Client.id == client_id))
        client = result.fetchone()[0].to_json()
        db.session.close()
        return client

    @app.route('/count/<parking_id>', methods=['GET'])
    def count_avail_places(parking_id):
        """Получение информации о количестве свободных мест на парковке"""

        res = db.session.execute(select(Parking.count_available_places).filter(
            Parking.id == parking_id
        ))
        return {'count': res.fetchone()[0]}

    @app.route('/parkings', methods=['POST'])
    def create_parking():
        data = request.json
        parking = Parking(address=data.get('address'),
                          opened=data.get('opened'),
                          count_places=data.get('count_places'),
                          count_available_places=data.get('count_places'),)
        db.session.add(parking)
        db.session.commit()
        result = db.session.execute(select(Parking).filter(
            Parking.id == parking.id))
        db.session.close()
        return result.fetchone()[0].to_json(), 201

    @app.route('/client_parkings', methods=['POST', 'DELETE'])
    def client_parkings():
        if request.method == 'POST':
            data = request.json
            parking = db.session.execute(select(Parking).filter(
                Parking.id == data.get('parking_id')))
            data_parking = parking.fetchone()[0].to_json()
            client = db.session.execute(select(Client).filter(
                Client.id == data.get('client_id')
            ))
            data_client = client.fetchone()[0].to_json()
            res = db.session.execute(select(ClientParking.parking_id).filter(
                ClientParking.client_id == data.get('client_id'),
                ClientParking.time_out is None))
            res_data = res.fetchone()
            if res_data is not None:
                parking_client = db.session.execute(select(
                    Parking.address).filter(Parking.id == res_data[0]))
                parking_client_address = parking_client.fetchone()[0]
                db.session.close()
                return (f'За клиентом {data_client.get('name')} '
                        f'{data_client.get('surname')} уже зарезервировано '
                        f'место на парковке по адресу '
                        f'{parking_client_address}')

            elif data_parking['opened'] == 0:
                return f'Парковка по адресу {data_parking['address']} закрыта.'

            elif ((data_parking['opened'] == 1)
                  and (data_parking['count_available_places'] > 0)):

                client_parking_new = ClientParking(
                    client_id=data.get('client_id'),
                    parking_id=data.get('parking_id'),
                    time_in=datetime.now())
                db.session.add(client_parking_new)
                db.session.commit()
                result = db.session.execute(select(ClientParking).filter(
                    ClientParking.id == client_parking_new.id
                ))
                db.session.query(Parking).filter(
                    Parking.id == data.get('parking_id')).update(
                    {
                        Parking.count_available_places:
                        Parking.count_available_places - 1
                    }
                )
                db.session.commit()
                db.session.close()
                return result.fetchone()[0].to_json(), 201
            else:
                return 'Нет свободных мест на парковке.'

        elif request.method == 'DELETE':
            data = request.json
            parking_client = db.session.execute(select(ClientParking).filter(
                ClientParking.client_id == data.get('client_id'),
                ClientParking.parking_id == data.get('parking_id')
            ))
            client = db.session.execute(select(Client).filter(
                Client.id == data.get('client_id')))
            client_data = client.fetchone()[0].to_json()
            if ((client_data['credit_card'] is None)
                    or (client_data['car_number'] is None)):
                return (f'У клиента {client_data['name']} '
                        f'{client_data['surname']} не привязана '
                        f'карта или указаны неверные данные.'), 404
            parking = db.session.execute(select(Parking).filter(
                Parking.id == data.get('parking_id')))
            parking_data = parking.fetchone()[0].to_json()
            parking_client_res = parking_client.fetchone()
            if parking_client_res:
                db.session.query(ClientParking).filter(
                    ClientParking.id == data.get('parking_id')).update(
                    {
                        ClientParking.time_out: datetime.now()
                    }
                )
                db.session.query(Parking).filter(
                    Parking.id == data.get('parking_id')).update(
                    {
                        Parking.count_available_places:
                        Parking.count_available_places + 1
                    }
                )
                db.session.commit()
                db.session.close()
                return (f"Клиент {client_data['name']} "
                        f"{client_data['surname']} покинул "
                        f"парковку по адресу {parking_data['address']}")
            else:
                return 'Переданы неверные данные', 404

        else:
            return 'Неверный запрос.', 404

    @app.route('/client_parkings/<id>', methods=['GET'])
    def get_client_parkings(id):
        result = db.session.execute(select(ClientParking).filter(
            ClientParking.id == id
        ))
        return result.fetchone()[0].to_json(), 200

    return app
