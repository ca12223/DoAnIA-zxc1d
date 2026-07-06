# TraceMQ: Hệ thống Giám sát và Phát hiện Tấn công cho Mạng IoT sử dụng MQTT Flow Filtering

**Đồ án Capstone Project** | IAP491 | Đại học FPT Đà Nẵng | 12/2025

---

## 📋 Tóm tắt (Abstract)

Sự bùng nổ của Internet of Things (IoT) đã mang lại tự động hóa mạnh mẽ nhưng cũng mở rộng đáng kể bề mặt tấn công, đặc biệt tại các doanh nghiệp nhỏ và vừa (SME) thiếu nguồn lực an ninh mạng.

**MQTT** là giao thức phổ biến nhất nhờ tính nhẹ, nhưng tồn tại nhiều lỗ hổng nghiêm trọng (default configuration, weak authentication, unencrypted traffic, wildcard abuse, brute-force, publish flooding...).

Các nghiên cứu hiện tại chủ yếu dựa vào **Machine Learning / Deep Learning** — hiệu quả trong lab nhưng **khó triển khai thực tế** do yêu cầu tài nguyên lớn, dataset labeled khan hiếm, và thiếu khả năng diễn giải (black-box).

**TraceMQ** là framework **nhẹ, hybrid, có thể diễn giải được** kết hợp **Rule-based IDS** (chính) và **Machine Learning** (hỗ trợ) nhằm cung cấp giải pháp thực tiễn, dễ triển khai cho SME và môi trường công nghiệp.

---

## 🔍 Vấn đề nghiên cứu & Khoảng trống (Research Gap & Problem Statement)

### Vấn đề tồn tại
- MQTT brokers thường được triển khai với cấu hình mặc định, không mã hóa, ACL yếu.
- SME thiếu nhân sự và hạ tầng để chạy các mô hình ML/DL nặng.
- Các giải pháp học thuật hiện tại: 
  - Phụ thuộc dataset lớn, training liên tục.
  - Black-box → khó tin tưởng và debug trong môi trường sản xuất.
  - Tập trung hẹp vào vài loại tấn công (chủ yếu DoS, Brute-force).
  - Khó tái tạo và triển khai thực tế.

### Cải tiến của TraceMQ so với nghiên cứu có sẵn
| Tiêu chí                        | Các nghiên cứu trước (ML/DL) | TraceMQ (Hybrid Rule-based)          | Cải tiến |
|--------------------------------|------------------------------|--------------------------------------|---------|
| Tài nguyên tính toán           | Cao (GPU, retraining)        | Thấp (CPU < 30%, RAM < 400MB)       | Rất cao |
| Khả năng diễn giải            | Thấp (black-box)             | Cao (rule rõ ràng + evidence)       | Rất cao |
| Dễ triển khai (SME)            | Khó                          | Docker Compose → dễ dàng            | Cao     |
| Số loại tấn công hỗ trợ        | Hạn chế                      | 9+ loại (protocol-aware)            | Cao     |
| Dataset                        | Phụ thuộc một dataset        | Chuẩn hóa nhiều dataset             | Cao     |
| Thời gian phản ứng             | Chậm (inference)             | Nhanh (rule-based)                  | Cao     |

**TraceMQ giải quyết triệt để khoảng trống**: Kết hợp ưu điểm của rule-based (nhanh, rõ ràng, nhẹ) với ML (phát hiện tấn công lén lút), đồng thời cung cấp hệ thống containerized hoàn chỉnh và dataset chuẩn hóa.

---

## ✨ Đóng góp của đồ án

1. **Framework hybrid** Rule-based + ML dành riêng cho MQTT
2. **Rule engine** phát hiện 9 loại tấn công protocol-specific
3. **Chuẩn hóa dataset** từ nhiều nguồn công khai
4. **Mô phỏng thực tế** 300 thiết bị IoT chia 5 zone (Smart Factory)
5. **Kiến trúc containerized** hoàn chỉnh, dễ tái tạo
6. **Hiệu suất xuất sắc**: Accuracy **99.93%**, FPR rất thấp, tài nguyên thấp
7. **Mã nguồn mở** và tài liệu đầy đủ

---

## 🏗 Kiến trúc hệ thống

### Sơ đồ tổng quan (Architecture Diagram)
<img width="1094" height="881" alt="image" src="https://github.com/user-attachments/assets/2cf9b5d2-5632-4903-b59d-535da2bb5d31" />
[300 IoT Devices (5 zones)]
↓ (Publish/Subscribe)
EMQX Broker (TLS 8883 + ACL)
↓
Suricata IDS (Deep Packet Inspection)
↓
Python Traffic Forwarder (Enrich metadata)
↓
InfluxDB (Time-series)
↓
Rule Engine + Random Forest
↓
Grafana + Prometheus (Dashboard & Alerting)
text

**Các thành phần chính:**
- **EMQX**: MQTT Broker
- **Suricata**: Network sensor
- **Python Replayer**: Mô phỏng traffic theo zone
- **Rule Engine + ML**: Phát hiện tấn công
- **InfluxDB + Grafana**: Lưu trữ & trực quan hóa

---

## 📊 Kết quả thực nghiệm

**Bảng tóm tắt hiệu suất (trích Chương 4):**

| Attack Type                  | Phương pháp      | Accuracy | FPR    |
|-----------------------------|------------------|----------|--------|
| Brute Force / Rotating      | Rule + ML        | 99.99%+  | ~0%    |
| Publish Flood               | Rule             | 99.99%   | 0.01%  |
| Reconnect Storm             | Rule             | 100%     | 0%     |
| SlowITe                     | Random Forest    | 91%      | 5.93%  |
| **Tổng thể Hybrid**         | **Hybrid**       | **99.93%** | Rất thấp |

Đầy đủ kết quả, confusion matrix, và phân tích nằm trong file Capstone Project Document.

---

## 🚀 Hướng dẫn Triển khai

Xem file **`HDSD.md`** trong repository.

**Tóm tắt nhanh:**
```bash
docker compose up -d
python replayer_office.py --broker emqx --port 8883
# Chạy các zone khác tương tự
