from pykafka import KafkaClient
import time

client = KafkaClient("127.0.0.1:9092")
geostream = client.topics["predictions"]

with geostream.get_sync_producer() as producer:
    i = 0
    for _ in range(10):
        print(i)
        producer.produce(f"Kafka is not just an author {str(i)}".encode())
        i += 1
        time.sleep(1)
