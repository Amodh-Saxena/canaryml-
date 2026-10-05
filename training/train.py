import json
import os

import joblib
import numpy as np
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

CATEGORIES = ["rec.autos", "sci.med"]
REMOVE = ("headers", "footers", "quotes")

def load_data(subset):
    data = fetch_20newsgroups(subset=subset, categories=CATEGORIES, remove=REMOVE, random_state=42)
    keep = [i for i, text in enumerate(data.data) if text.strip()]
    X = [data.data[i] for i in keep]
    y = data.target[keep]
    return X, y

def train_v1(X, y):
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))
    ])
    pipeline.fit(X, y)
    return pipeline

def train_v2_bad(X, y):
    # Degraded training: limited features and flipped labels
    rng = np.random.default_rng(42)
    y_bad = y.copy()
    flip_idx = rng.choice(len(y), int(0.4 * len(y)), replace=False)
    y_bad[flip_idx] = 1 - y_bad[flip_idx]
    
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=50)),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))
    ])
    pipeline.fit(X, y_bad)
    return pipeline

def train_v3_good(X, y):
    # Improved settings: n-grams and tuned C
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
        ("clf", LogisticRegression(C=10.0, max_iter=1000, random_state=42))
    ])
    pipeline.fit(X, y)
    return pipeline

def main():
    print("Loading data...")
    X_train, y_train = load_data("train")
    X_test, y_test = load_data("test")
    
    os.makedirs("models", exist_ok=True)
    report = {}
    
    versions = {
        "v1": train_v1,
        "v2-bad": train_v2_bad,
        "v3-good": train_v3_good
    }
    
    for version_name, train_fn in versions.items():
        print(f"Training {version_name}...")
        model = train_fn(X_train, y_train)
        
        accuracy = model.score(X_test, y_test)
        report[version_name] = round(accuracy, 4)
        print(f"{version_name} accuracy: {accuracy:.4f}")
        
        model_path = f"models/{version_name}.joblib"
        joblib.dump(model, model_path)
        print(f"Saved to {model_path}")
        
    report_path = "models/report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    main()
