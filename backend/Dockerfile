FROM python:3.9 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.9
EXPOSE 8006
WORKDIR /backend
COPY --from=requirements-stage /tmp/requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt
COPY ./app /backend/app
COPY .env /backend/app

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8006"]