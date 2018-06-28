FROM python:3

COPY requirements.txt ./
COPY worker.py ./
COPY local_settings.py ./
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./worker.py" ]
