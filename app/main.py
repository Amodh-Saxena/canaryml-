import os
import random
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.metrics import (
    http_request_duration_seconds,
    http_requests_total,
    model_predictions_total,
)
from app.model_loader import load_model

# Global model state
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model = load_model()
    yield
    model = None

app = FastAPI(lifespan=lifespan)

class PredictionRequest(BaseModel):
    text: str
    true_label: int | None = None

class PredictionResponse(BaseModel):
    label: int
    model_version: str

@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    start_time = time.time()
    
    # Fault injection logic
    fault_latency_ms = float(os.getenv("FAULT_LATENCY_MS", "0.0"))
    fault_error_rate = float(os.getenv("FAULT_ERROR_RATE", "0.0"))
    
    if fault_error_rate > 0 and random.random() < fault_error_rate:
        http_requests_total.labels(status=500).inc()
        duration = time.time() - start_time
        http_request_duration_seconds.observe(duration)
        return Response("Injected Error", status_code=500)

    if fault_latency_ms > 0:
        import asyncio
        await asyncio.sleep(fault_latency_ms / 1000.0)

    response = await call_next(request)
    
    # Don't record metrics for /metrics to avoid noise
    if request.url.path != "/metrics":
        http_requests_total.labels(status=response.status_code).inc()
        duration = time.time() - start_time
        http_request_duration_seconds.observe(duration)
        
    return response

@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    model_version = os.getenv("MODEL_VERSION", "unknown")
    
    # In a real setup, we might predict probabilities. Here we just predict the label.
    pred_label = int(model.predict([req.text])[0])
    
    if req.true_label is not None:
        correct = str(pred_label == req.true_label).lower()
        model_predictions_total.labels(
            model_version=model_version, 
            correct=correct
        ).inc()
        
    return PredictionResponse(label=pred_label, model_version=model_version)

@app.get("/healthz")
def healthz():
    if model is not None:
        return {"status": "ok"}
    return Response("Model not loaded", status_code=503)

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
