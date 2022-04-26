import uvicorn
from .settings import settings
from .neural_networks.violence_recognition.model_structure import reload_model_for_current_system

reload_model_for_current_system()

uvicorn.run("app.app:app", host=settings.server_host, port=settings.server_port, reload=settings.is_debug)
