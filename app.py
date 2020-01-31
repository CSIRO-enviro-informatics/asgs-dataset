# Shortcut to asgs_dataset.app.app
# Useful for when you want to be in the project root directory when running, rather than the module root
from asgs_dataset.app import app, run
application = app
if __name__ == "__main__":
    run()
