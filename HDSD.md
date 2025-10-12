**ko cần phải tạo lại certs**

1. setup emqx
   docker compose up -d
   **Sau đó vào dash board set up tiếp**
   **1.1 set up authenticate**
   vào phần authentication(hình cái khiên), chọn cái built in database
   Bấm cái user management, chọn import rồi chọn cái file EMQX*Users_Import**sha256**prefix_salt*.csv
   **1.2 set up authorization**
   vào phần authorize(hình cái khiên), enable cái option file lên rồi qua mục setting copy hết mọi thứ cái file pastcl.txt
   bấm update
   **1.3 set up listener(hình cái bánh răng cưa)**
   bấm vào cái 8883,
   kéo xuống phần TLS cert, key  
    bấm reset, select file, rồi chọn **TLS cert = server-cert.pem**
   **TLS key = server-key.pem**
   **CA cert = ca-cert.pem**
   bấm update để lưu
2. lệnh chạy mô phỏng
   python replayer_office.py --indir datasets --broker emqx --port 8883 --min-interval 0
3. sau đó chạy docker compose up telegraf, influxdb để check log
