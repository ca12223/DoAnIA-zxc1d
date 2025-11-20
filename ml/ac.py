#!/usr/bin/env python3
"""
ac.py — TRAINING PIPELINE (NEW VERSION WITH USERNAME RULE)
==========================================================
- Không dùng tốc độ gửi/behavior rate
- Chỉ tập trung vào hành vi authentication
- return_code và các fail window là tín hiệu chính
- Thêm logic: đếm số lần return_code = 4 theo từng username
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
import json

INPUT_CSV   = "mqtt_hr.csv"
MODEL_PATH  = "if_model.pkl"
SCALER_PATH = "if_scaler.pkl"
FEATURE_PATH = "if_features.json"
THRESHOLD_PATH = "if_threshold.json"

# =====================================
# LOAD DATA
# =====================================
df = pd.read_csv(INPUT_CSV, low_memory=False)
df["_time"] = pd.to_datetime(df["_time"], errors="coerce")
df = df.dropna(subset=["_time"]).sort_values("_time")
df = df[df["mqtt_type"] == "connect"]

id_col = "client_identifier" if "client_identifier" in df.columns else "client_id"

# =====================================
# BASIC FEATURES
# (Chỉ giữ những thứ không phụ thuộc tốc độ)
# =====================================
df["hour"] = df["_time"].dt.hour
df["dayofweek"] = df["_time"].dt.dayofweek

# Số message mỗi client (không đánh giá tốc độ)
df["client_msg_count"] = df.groupby(id_col).cumcount() + 1

# =====================================
# AUTHENTICATION FAIL FEATURES
# (trọng tâm chính của mô hình)
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

    # Lưu fail theo client (bất kỳ rc != 0)
    if rc != 0:
        fail_history[cid].append(now)

    # Giữ fail trong 5 phút
    fail_history[cid] = [
        t for t in fail_history[cid]
        if now - t <= pd.Timedelta(minutes=5)
    ]

    # Đếm fail theo client
    client_fail_5m.append(len(fail_history[cid]))
    client_fail_1m.append(
        sum(now - t <= pd.Timedelta(minutes=1) for t in fail_history[cid])
    )

    # ===== NEW: FAIL THEO USERNAME VỚI return_code == 4 =====
    if user not in user_fail_history:
        user_fail_history[user] = []

    if rc == 4:
        user_fail_history[user].append(now)

    # giữ trong 5 phút cho username này (optional, cho nhất quán)
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

# =====================================
# FEATURE LIST (KHÔNG CÓ SPEED)
# =====================================
raw_features = [
    "flag_clean_session", "flag_password",
    "protocol_version", "bytes_toserver", "pkts_toserver"
]

auth_features = [
    "return_code",
    "client_fail_1m",
    "client_fail_5m",
    "client_fail_ratio_5m",
    "user_fail_reason4",   # <== NEW
]

behavior_meta = [
    "hour",
    "dayofweek",
    "client_msg_count"
]

final_features = raw_features + behavior_meta + auth_features

# Convert bool → int
for col in df.columns:
    if df[col].dtype == bool:
        df[col] = df[col].astype(int)

df = df.fillna(0)
X = df[final_features]

# =====================================
# TRAIN MODEL
# =====================================
scaler = RobustScaler()
Xs = scaler.fit_transform(X)

model = IsolationForest(
    contamination=0.002,
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)
model.fit(Xs)
scores = model.decision_function(Xs)

# nhạy cao: 5 percentile
threshold = float(np.percentile(scores, 5))

# =====================================
# SAVE OUTPUT
# =====================================
pd.to_pickle(model, MODEL_PATH)
pd.to_pickle(scaler, SCALER_PATH)

with open(FEATURE_PATH, "w") as f:
    json.dump(final_features, f)

with open(THRESHOLD_PATH, "w") as f:
    json.dump({"threshold": threshold}, f)

print("Training complete (USERNAME RULE VERSION).")
print("Saved threshold:", threshold)
