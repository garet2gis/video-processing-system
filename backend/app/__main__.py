import uvicorn

uvicorn.run("app.app:app", host="localhost", port=8006, reload=True)
