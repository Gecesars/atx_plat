from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    data = {
        "temperature": random.uniform(0, 500),
        "pressure": random.uniform(950, 1050),  # Example range for atmospheric pressure in hPa
        "humidity": random.uniform(0, 100),
        "thermal_sensation": random.uniform(0, 100)
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
