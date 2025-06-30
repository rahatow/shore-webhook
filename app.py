import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

def is_real_date(val):
    return val and isinstance(val, str) and not val.startswith('{{') and not val.endswith('}}')

@app.route('/free_slots', methods=['POST'])
def get_free_slots():
    try:
        data = request.json or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if not is_real_date(date_from):
            date_from = datetime.now().strftime("%Y-%m-%d")
        if not is_real_date(date_to):
            date_to = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        # Составляем payload
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

        print("Sending to Shore API:", payload)
        response = requests.post(
            "https://api.shore.com/v2/availability/calculate_slots",
            json=payload, headers=headers, timeout=15
        )
        print("Shore API Response Status:", response.status_code)
        print("Shore API Response Text:", response.text)

        if response.status_code != 200:
            print(f"Shore API returned error code: {response.status_code}, body: {response.text}")
            return jsonify({"error": f"Shore API error: {response.status_code}"}), 500

        data = response.json()
        # Проверяем, что пришли слоты
        if 'slots' not in data or not isinstance(data['slots'], list):
            print(f"No 'slots' in Shore response: {data}")
            return jsonify({"error": "No slots found in Shore response"}), 500

        # Собираем даты и часы
        dates = []
        slots_per_date = {}
        for slot in data['slots']:
            if slot.get('times'):
                dates.append(slot.get('date'))
                slots_per_date[slot.get('date')] = ', '.join(slot.get('times'))

        print("DATES:", dates)
        print("SLOTS PER DATE:", slots_per_date)

        # Если дат нет вообще — сообщаем ManyChat-у
        if not dates:
            return jsonify({"dates": [], "slots_per_date": {}, "message": "Нет доступных дат"}), 200

        # Только 3 ближайшие даты
        dates = dates[:3]
        result = {
            "dates": dates,
            "slots_per_date": {d: slots_per_date[d] for d in dates}
        }
        print("RESULT:", result)
        return jsonify(result)

    except Exception as e:
        print(f"ERROR in /free_slots: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
