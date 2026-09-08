from flask import Flask
from config import Config
from extension import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from models import Event, Seat, SeatHold, Booking
    from routes import api

    app.register_blueprint(api)

    return app