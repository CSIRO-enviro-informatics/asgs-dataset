import logging
import asgs_dataset._config as conf
from flask import Flask
from asgs_dataset.controller import controller
import pyldapi
import argparse

app = Flask(__name__, template_folder=conf.TEMPLATES_DIR, static_folder=conf.STATIC_DIR)
app.register_blueprint(controller)


def run():
    parser = argparse.ArgumentParser(description='ASGS Dataset LDAPI')
    parser.add_argument('--init', action="store_true", default=False, help='Initialise the application then exit (rofr.ttl etc)')
    args, unknown = parser.parse_known_args()

    logging.basicConfig(filename=conf.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    #pyldapi.setup(app, conf.APP_DIR, conf.DATA_URI_PREFIX)

    # run the Flask app
    if not args.init:
        app.run(debug=conf.DEBUG, threaded=True, use_reloader=False)


# run the Flask app
if __name__ == '__main__':
    run()
