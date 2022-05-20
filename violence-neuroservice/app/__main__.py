import uvicorn
from .settings import settings

uvicorn.run("app.app:app", host=settings.server_host, port=settings.server_port, reload=settings.is_debug)
# uvicorn.run("app.app_redis:app", host=settings.server_host, port=settings.server_port, reload=settings.is_debug)
