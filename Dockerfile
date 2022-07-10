FROM python:3.9-slim

ADD requirements.txt /app/
RUN cd /app/ && pip install -r requirements.txt

ENV FLASK_RUN_PORT=9000
ENV FLASK_APP=/app/app.py

ADD .env /app/

CMD ["flask", "run", "--host=0.0.0.0"]