from waitress import serve
from pfu import create_app

app = create_app()

if __name__ == '__main__':
    serve(app, host=app.config['HOSTNAME'], port=app.config['PORT'])
