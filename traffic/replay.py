from sklearn.datasets import fetch_20newsgroups
import requests
import time

URL = "http://localhost/predict"
INTERVAL = 0.5

data = fetch_20newsgroups(
    subset="test",
    categories=["rec.autos", "sci.med"],
    remove=("headers", "footers", "quotes"),
    random_state=42
)

samples = [
    (text, label)
    for text, label in zip(data.data, data.target)
    if text.strip()
]

print(f"Loaded {len(samples)} labeled samples.")
print("Sending traffic through NGINX...")
print("Press Ctrl+C to stop.\n")

index = 0
success = 0
errors = 0

try:
    while True:
        text, label = samples[index % len(samples)]
        index += 1

        try:
            response = requests.post(
                URL,
                json={
                    "text": text,
                    "true_label": int(label)
                },
                timeout=5
            )

            response.raise_for_status()
            result = response.json()

            success += 1

            print(
                f"request={index} | "
                f"model={result['model_version']} | "
                f"predicted={result['label']} | "
                f"actual={label}"
            )

        except Exception as e:
            errors += 1
            print(f"request={index} | ERROR={e}")

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nStopped.")
    print(f"Successful requests: {success}")
    print(f"Errors: {errors}")
