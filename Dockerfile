FROM python:2

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /cah

RUN pip install --no-cache-dir -e /cah

WORKDIR /cah

CMD ["twistd", "-noy", "cah.tac"] 
