# A system for capturing and processing video streams by neural networks

![Интеграция_модулей - Page 5](https://user-images.githubusercontent.com/42912280/172907912-0315a6a1-6391-40dc-a78d-03a9aa70be8a.png)

## Frontend demo

https://user-images.githubusercontent.com/42912280/168871565-6ac20985-02f3-4e47-908b-06d3410a618a.mp4

## [Integration custom neuroservice](video-capture-service/README.md)

## Launching with docker (for x86 platforms)

Need pre-installed docker-compose

If you don't have cuda support replace the base image of the violence neuroservice (in the Dockerfile) from tensorflow/tensorflow:latest-gpu to tensorflow/tensorflow:latest

Command to launch the system:
docker-compose up --build -d

## Launching manually

Need pre-installed docker-compose, python v3.9 and NodeJS v16

1. Launch apache kafka: docker-compose -f kafka-setup/single-kafka-cluster.yml up --build -d
2. From frontend directory: yarn install
3. From frontend directory: yarn run start
4. In all service directories except frontend, enter: poetry install
5. From violence-neuroservice directory: python -m app
6. From backend directory: python -m app
7. From video-capture-service directory: python capture_parallel.py
8. From video-capture-service directory: http-server . --cors -c-1 -p 8000
