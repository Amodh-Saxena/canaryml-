from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    # Using default buckets
)

model_predictions_total = Counter(
    "model_predictions_total",
    "Total number of model predictions",
    ["model_version", "correct"]
)
