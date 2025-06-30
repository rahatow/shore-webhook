from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Webhook работает!'

@app.route('/free_slots', methods=['POST'])
def get_free_slots():
    data = request.json
    date_from = data.get('date_from', "2025-07-02")
    date_to = data.get('date_to', "2025-07-31")

    payload = {
        "required_capacity": "1",
        "search_weeks_range": 0,
        "merchant_id": "3c32f625-c162-4293-98c0-2551c920a5ed",
        "services_resources": [
            {"service_id": "991deea0-4da5-487f-b1d0-2d78869525ab"}
        ],
        "starts_at": f"{date_from} 00:00:00",
        "ends_at": f"{date_to} 23:59:59",
        "timezone": "Europe/Berlin"
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://connect.shore.com",
        "Referer": "https://connect.shore.com/"
    }
    response = requests.post("https://api.shore.com/v2/availability/calculate_slots", json=payload, headers=headers)
    data = response.json()
    slots_str = ""
    for slot in data['slots']:
        if slot['times']:
            slots_str += f"{slot['date']}: {', '.join(slot['times'])}\n"
    return jsonify({"slots": slots_str})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
