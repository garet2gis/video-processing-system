FROM python:3.9 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml /tmp/
RUN sed -i '/tensorflow/d' /tmp/pyproject.toml
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
WORKDIR /code
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
COPY .env /code/app
EXPOSE 8005

CMD ["python3","-m","app"]
