from m import Application
from example.models import db
from example.handlers import router

app = Application()
app.register_extension(db)
app.add_router(router)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('127.0.0.1', 3000, app)
    try:
        db.metadata.create_all()
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
