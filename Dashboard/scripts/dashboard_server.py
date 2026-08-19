#!/usr/bin/env python3

from flask import Flask
from flask_cors import CORS

from dashboard_config import HOST
from dashboard_config import PORT
from dashboard_config import DEBUG

from dashboard_db import init_db
from dashboard_routes import register_routes


app = Flask(__name__)

CORS(app)

register_routes(app)


if __name__ == '__main__':
    init_db()

    print('VANTAGE DASHBOARD Backend v1.0')
    print('Corriendo en http://127.0.0.1:8000')

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )
