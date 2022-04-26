FROM python:3.9 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN cat requirements.txt

FROM python:3.9
EXPOSE 8001
RUN apt-get clean && apt-get update && apt-get install ffmpeg librdkafka-dev --assume-yes --no-install-recommends
WORKDIR /capture
COPY --from=requirements-stage /tmp/requirements.txt /capture/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /capture/requirements.txt
COPY . /capture

ENTRYPOINT ["python3","capture_parallel.py"]