import asyncio
import typing
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI
from fastapi import WebSocket
from starlette.endpoints import WebSocketEndpoint
from starlette.middleware.cors import CORSMiddleware
import json

PROJECT_NAME = "ws_test"
TOPIC_NAME = "prediction"
KAFKA_INSTANCE = "0.0.0.0:9092"

app = FastAPI(title=PROJECT_NAME)
app.add_middleware(CORSMiddleware, allow_origins=["*"])


class PredictionResponse(BaseModel):
    prediction: float
    cam_id: int
    timestamp: int
    timestamp_delay: float


async def consume(consumer):
    async for msg in consumer:
        print("consumed", msg.value)
        return [msg.value.decode(), msg.timestamp]


@app.websocket_route("/predictions")
class WebsocketConsumer(WebSocketEndpoint):
    """
    Consume messages from <topicname>
    This will start a Kafka Consumer from a topic
    And this path operation will:
    * return ConsumerResponse
    """

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({"Message: ": "connected"})

        loop = asyncio.get_event_loop()
        self.consumer = AIOKafkaConsumer(
            TOPIC_NAME,
            loop=loop,
            client_id=PROJECT_NAME,
            bootstrap_servers=KAFKA_INSTANCE,
            enable_auto_commit=False,
        )

        await self.consumer.start()

        self.consumer_task = asyncio.create_task(
            self.send_consumer_message(websocket=websocket, topic_name=TOPIC_NAME)
        )

        print('connect')

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.consumer_task.cancel()
        await self.consumer.stop()
        print('disconnect')

    async def on_receive(self, websocket: WebSocket, data: typing.Any) -> None:
        await websocket.send_json({"Message: ": data})

    async def send_consumer_message(self, websocket: WebSocket, topic_name: str) -> None:
        while True:
            [data, timestamp] = await consume(self.consumer)
            response = PredictionResponse(topic=topic_name,
                                          timestamp=timestamp,
                                          **json.loads(data))
            await websocket.send_text(f"{response.json()}")
