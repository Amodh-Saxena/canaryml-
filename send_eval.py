from sklearn.datasets import fetch_20newsgroups
import requests

URL = "http://localhost:8002/predict"

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
][:40]

print(f"Sending {len(samples)} evaluation samples...\n")

correct = 0

for i, (text, label) in enumerate(samples, 1):
    try:
        response = requests.post(
            URL,
            json={
                "text": text,
                "true_label": int(label)
            },
            timeout=5
        )

        result = response.json()
        predicted = result["label"]

        if predicted == label:
            correct += 1

        print(
            f"{i}/{len(samples)} | "
            f"predicted={predicted} | "
            f"actual={label} | "
            f"model={result['model_version']}"
        )

    except Exception as e:
        print(f"{i}/{len(samples)} | ERROR: {e}")

print(f"\nFinished.")
print(f"Local sample accuracy: {correct}/{len(samples)} = {correct/len(samples):.2%}")