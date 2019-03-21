FROM tiangolo/uwsgi-nginx-flask:python3.7

COPY . /app
RUN touch __init.py__
RUN pip install -r /app/requirements.txt
ENV STATIC_PATH /app/asgs_dataset/view/static
