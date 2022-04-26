FROM python:3.9 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml /tmp/
RUN sed -i '/tensorflow/d' /tmp/pyproject.toml
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM tensorflow/tensorflow:latest-gpu
WORKDIR /code
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
COPY .env /code/app

CMD ["python3","-m","app"]