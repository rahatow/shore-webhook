import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/free_slots', methods=['POST'])
def get_free_slots():
    try:
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
        # Основной запрос
        response = requests.post(
            "https://api.shore.com/v2/availability/calculate_slots",
            json=payload, headers=headers, timeout=15
        )
        if response.status_code != 200:
            print(f"Shore API returned error code: {response.status_code}, body: {response.text}")
            return jsonify({"error": f"Shore API error: {response.status_code}"}), 500

        data = response.json()
        # Проверяем наличие слотов
        if 'slots' not in data or not isinstance(data['slots'], list):
            print(f"No 'slots' in Shore response: {data}")
            return jsonify({"error": "No slots found in Shore response"}), 500

        dates = []
        slots_per_date = {}
        for slot in data['slots']:
            if slot.get('times'):
                dates.append(slot.get('date'))
                slots_per_date[slot.get('date')] = ', '.join(slot.get('times'))

        # Если дат нет вообще
        if not dates:
            return jsonify({"dates": [], "slots_per_date": {}, "message": "Нет доступных дат"}), 200

        # Берем только ближайшие 3 даты
        dates = dates[:3]
        result = {
            "dates": dates,
            "slots_per_date": {d: slots_per_date[d] for d in dates}
        }
        return jsonify(result)

    except Exception as e:
        # Печатаем ошибку в логах Render
        print(f"ERROR in /free_slots: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
