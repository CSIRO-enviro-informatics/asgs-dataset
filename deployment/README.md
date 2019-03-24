Just a note to say this deployment directory is used to deploy both the 2011 and 2016 ASGS Datasets.

The 2011 code is in a branch, and the 2016 is on master.

/usr/sbin/uwsgi --socket /var/run/uwsgi/asgs2011.sock --chmod-socket=776 --plugin python3  --virtualenv /app/venv --wsgi-file /app/asgs_dataset/app.py --callable app  --max-requests=5000 --processes=3 -L