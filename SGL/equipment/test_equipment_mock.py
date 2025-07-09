# test_equipment_mock.py
from flask import Flask, jsonify, request
import random
import threading
import time

app = Flask(__name__)


@app.route('/api/request', methods=['POST'])
def receive_request():
    sample_id = request.json.get('sample_id')
    test_code = request.json.get('test_code')

    # Simulate processing delay (2-5 seconds)
    processing_time = random.uniform(2, 5)
    time.sleep(processing_time)

    return jsonify({
        "status": "accepted",
        "request_id": f"REQ-{random.randint(1000, 9999)}",
        "processing_time": processing_time
    })


@app.route('/api/results', methods=['GET'])
def get_results():
    # Generate realistic mock results
    return jsonify([{
        "sample_id": f"SMP-{random.randint(1000, 9999)}",
        "test_code": random.choice(["CBC", "LFT", "UFR", "LIPID"]),
        "values": {
            "WBC": random.uniform(4.0, 11.0),
            "RBC": random.uniform(4.2, 6.1),
            "HGB": random.uniform(12.0, 18.0)
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }])


def run_mock_server():
    app.run(port=5001, host='0.0.0.0')


if __name__ == '__main__':
    server_thread = threading.Thread(target=run_mock_server)
    server_thread.start()