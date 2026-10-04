import time
import json
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score
)
import lightgbm as lgb

def run_benchmark():
    dataset_path = os.path.expanduser("~/ml-benchmark/creditcard.csv")
    if not os.path.exists(dataset_path):
        # Fallback to local directory if running locally
        if os.path.exists("creditcard.csv"):
            dataset_path = "creditcard.csv"
        else:
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    print(f"[*] Loading dataset from: {dataset_path}")
    t0 = time.time()
    df = pd.read_csv(dataset_path)
    data_load_time = round(time.time() - t0, 4)
    print(f"    Loaded {df.shape[0]} rows, {df.shape[1]} columns in {data_load_time}s")

    X = df.drop(columns=["Class"])
    y = df["Class"]

    # 80/20 train/test split with stratification due to class imbalance
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[*] Training LightGBM Classifier...")
    model = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )

    t1 = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
    )
    training_time = round(time.time() - t1, 4)
    best_iteration = int(model.best_iteration_ if hasattr(model, "best_iteration_") and model.best_iteration_ else 100)
    print(f"    Training completed in {training_time}s (Best iteration: {best_iteration})")

    print("[*] Evaluating model metrics...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc_roc = round(float(roc_auc_score(y_test, y_prob)), 4)
    accuracy = round(float(accuracy_score(y_test, y_pred)), 4)
    f1 = round(float(f1_score(y_test, y_pred)), 4)
    precision = round(float(precision_score(y_test, y_pred)), 4)
    recall = round(float(recall_score(y_test, y_pred)), 4)

    print("[*] Measuring inference latency (1 row)...")
    single_sample = X_test.iloc[:1]
    # Warm up
    _ = model.predict(single_sample)
    t_start = time.perf_counter()
    for _ in range(100):
        _ = model.predict(single_sample)
    single_latency_ms = round(((time.perf_counter() - t_start) / 100) * 1000, 4)

    print("[*] Measuring inference throughput (1000 rows)...")
    batch_sample = X_test.iloc[:1000]
    t_start = time.perf_counter()
    _ = model.predict(batch_sample)
    batch_time = time.perf_counter() - t_start
    throughput = round(1000 / batch_time, 2) if batch_time > 0 else 0

    results = {
        "data_load_time_sec": data_load_time,
        "training_time_sec": training_time,
        "best_iteration": best_iteration,
        "auc_roc": auc_roc,
        "accuracy": accuracy,
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "single_row_inference_latency_ms": single_latency_ms,
        "inference_throughput_rows_per_sec": throughput
    }

    output_path = os.path.expanduser("~/ml-benchmark/benchmark_result.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)

    print("\n" + "="*50)
    print("           BENCHMARK RESULTS SUMMARY")
    print("="*50)
    for k, v in results.items():
        print(f" {k:<35}: {v}")
    print("="*50)
    print(f"\n[+] Results successfully saved to: {output_path}")

if __name__ == "__main__":
    run_benchmark()
