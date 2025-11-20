#!/usr/bin/env python3
"""
as.py — AUTHENTICATION ATTACK DETECTION (WITH USERNAME RULE)
============================================================
- KHÔNG dùng speed
- Chỉ dùng authentication features do ac.py tạo ra
- Thêm rule: chỉ flag nếu cùng username bị return_code = 4 nhiều hơn 1 lần
"""

import pandas as pd
import numpy as np
import joblib
import json

TEST_FILE = "mqtt_hr_attk.csv"

MODEL_PATH = "if_model.pkl"
SCALER_PATH = "if_scaler.pkl"
FEATURE_PATH = "if_features.json"
THRESHOLD_PATH = "if_threshold.json"

OUTPUT = "mqtt_scored.csv"

# =====================================
# LOAD ARTIFACTS
# =====================================
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

features = json.load(open(FEATURE_PATH))
threshold = json.load(open(THRESHOLD_PATH))["threshold"]

# =====================================
# LOAD DATA
# =====================================
df = pd.read_csv(TEST_FILE, low_memory=False)
df["_time"] = pd.to_datetime(df["_time"], errors="coerce")
df = df.dropna(subset=["_time"]).sort_values("_time")
df = df[df["mqtt_type"] == "connect"]

id_col = "client_identifier" if "client_identifier" in df.columns else "client_id"

# =====================================
# BASIC FEATURES (KHÔNG speed)
# =====================================
df["hour"] = df["_time"].dt.hour
df["dayofweek"] = df["_time"].dt.dayofweek
df["client_msg_count"] = df.groupby(id_col).cumcount() + 1

# =====================================
# AUTHENTICATION FAIL FEATURES
# =====================================
df["return_code"] = df["return_code"].fillna(0)

client_fail_1m = []
client_fail_5m = []
fail_history = {}

# NEW: per-username fail count for return_code == 4
user_fail_history = {}
user_fail_reason4 = []

for _, row in df.iterrows():
    cid = row[id_col]
    now = row["_time"]
    rc = row["return_code"]
    user = str(row.get("username", ""))

    if cid not in fail_history:
        fail_history[cid] = []

    if rc != 0:
        fail_history[cid].append(now)

    fail_history[cid] = [
        t for t in fail_history[cid]
        if now - t <= pd.Timedelta(minutes=5)
    ]

    client_fail_5m.append(len(fail_history[cid]))
    client_fail_1m.append(
        sum(now - t <= pd.Timedelta(minutes=1) for t in fail_history[cid])
    )

    # ===== NEW: FAIL THEO USERNAME VỚI return_code == 4 =====
    if user not in user_fail_history:
        user_fail_history[user] = []

    if rc == 4:
        user_fail_history[user].append(now)

    user_fail_history[user] = [
        t for t in user_fail_history[user]
        if now - t <= pd.Timedelta(minutes=5)
    ]

    user_fail_reason4.append(len(user_fail_history[user]))

df["client_fail_1m"] = client_fail_1m
df["client_fail_5m"] = client_fail_5m
df["client_fail_ratio_5m"] = df["client_fail_5m"] / (df["client_msg_count"] + 1e-6)

# NEW FEATURE: số lần rc=4 theo username trong 5 phút gần nhất
df["user_fail_reason4"] = user_fail_reason4

df = df.fillna(0)

# =====================================
# MODEL INFERENCE
# =====================================
X = df[features]   # <== Không lỗi nếu đã chạy lại ac.py mới
Xs = scaler.transform(X)

scores = model.decision_function(Xs)
df["score"] = scores
df["model_anomaly"] = np.where(scores <= threshold, -1, 1)

# =====================================
# AUTH RULE OVERRIDE (MỚI)
# =====================================
# Chỉ flag attack nếu cùng username có return_code=4 nhiều hơn một lần
df["rule_attack"] = np.where(
    df["user_fail_reason4"] > 1,
    -1,   # attack
    1     # normal
)

# FINAL DECISION = RULE
df["final_anomaly"] = df["rule_attack"]

df.to_csv(OUTPUT, index=False)
print("Saved:", OUTPUT)
