from fastapi import FastAPI
import socket

app = FastAPI(
    title="Local Container Platform Demo",
    description="Sample application used to demonstrate container deployment and load balancing.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Hello from Local Container Platform",
        "hostname": socket.gethostname(),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "hostname": socket.gethostname(),
    }
