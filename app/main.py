from flask import Flask
from app.configuration import BOOK_FILE
from app.diagnostics import RampError
from app.http import routes
from app.ledger.sqlite_book import ShiftBook
from app.worktop import display


def create_app(db_file=BOOK_FILE):
    server = Flask(__name__)
    server.config['MAX_CONTENT_LENGTH'] = 2*1024*1024
    server.json.ensure_ascii = False
    server.book = ShiftBook(db_file)
    server.register_blueprint(routes)
    server.register_blueprint(display)

    @server.errorhandler(RampError)
    def errors(error):
        return {'error':error.code,'message':str(error)},error.status

    @server.get('/healthz')
    def ready():
        return {'status':'ok'}

    return server
