import logging
import asgs_dataset._config as conf
from flask import Flask
from asgs_dataset.controller import routes
import pyldapi

app = Flask(__name__, template_folder=conf.TEMPLATES_DIR, static_folder=conf.STATIC_DIR)
app.register_blueprint(routes.routes)


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=conf.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    #pyldapi.setup(app, conf.APP_DIR, str(conf.DATA_URI_PREFIX).rstrip('/'))

    # run the Flask app
    app.run(debug=conf.DEBUG, threaded=True, use_reloader=False)

