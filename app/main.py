from fastapi import FastAPI
import os
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
        "container": os.getenv("CONTAINER_NAME", "unknown"),
        "hostname": socket.gethostname(),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "container": os.getenv("CONTAINER_NAME", "unknown"),
        "hostname": socket.gethostname(),
    }