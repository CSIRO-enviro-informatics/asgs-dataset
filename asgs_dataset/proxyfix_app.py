from asgs_dataset.app import app

# Import the fixer
from werkzeug.middleware.proxy_fix import ProxyFix
# Use the fixer
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
application = app
__all__ = ('app', 'application')
