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
    # TODO: Add configurable host and port to serve
    # serve(app, host=config.host, port=config.port)
    serve(app)
