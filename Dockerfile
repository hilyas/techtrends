FROM python:3.9
MAINTAINER "Ilyas Hamdi"

WORKDIR /src/techtrends
COPY techtrends /src/techtrends

RUN pip install -r requirements.txt && python init_db.py

EXPOSE 3111

CMD ["python", "./app.py"]