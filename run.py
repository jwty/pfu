import logging
from waitress import serve
from pfu import create_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

waitress_logger = logging.getLogger('waitress')
waitress_logger.setLevel(logging.INFO)

app = create_app()

if __name__ == '__main__':
    logging.info("Starting pfu server...")
    serve(app, host=app.config['HOSTNAME'], port=app.config['PORT'])
