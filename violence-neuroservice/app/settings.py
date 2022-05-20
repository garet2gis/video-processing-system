from pydantic import BaseSettings


class Settings(BaseSettings):
    server_host: str = "0.0.0.0"
    server_port: int = 8005
    is_debug: bool = False
    redis_queue_name: str = 'frames'
    timeout_server: float = 0.05
    redis_host: str = '0.0.0.0'
    redis_port: int = 6379
    client_max_tries: int = 1000
    model_type: str = 'cnn_lstm'


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
