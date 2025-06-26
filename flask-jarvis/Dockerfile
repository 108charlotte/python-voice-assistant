FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 10000

CMD ["waitress-serve", "--host=0.0.0.0", "--port=10000", "run:app"]