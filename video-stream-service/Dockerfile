FROM python:3.9
EXPOSE 8000

RUN apt-get clean && apt-get update && apt-get install ffmpeg nodejs npm --assume-yes --no-install-recommends

WORKDIR /video-stream-service

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install poetry

RUN npm install --global http-server

COPY poetry.lock pyproject.toml ./
RUN poetry install

COPY . .

RUN ["chmod", "+x", "./scripts/docker-entrypoint.sh"]

ENTRYPOINT ["./scripts/docker-entrypoint.sh"]