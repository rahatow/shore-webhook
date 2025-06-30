import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

def is_real_date(val):
    return val and isinstance(val, str) and not val.startswith('{{') and not val.endswith('}}')

# 1. Endpoint для выбора ближайших дат
@app.route('/free_slots', methods=['POST'])
def get_free_slots():
    try:
        data = request.json or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        # По-умолчанию: сегодня и +30 дней
        if not is_real_date(date_from):
            date_from = datetime.now().strftime("%Y-%m-%d")
        if not is_real_date(date_to):
            date_to = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

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

        response = requests.post(
            "https://api.shore.com/v2/availability/calculate_slots",
            json=payload, headers=headers, timeout=15
        )
        data = response.json()

        dates = []
        slots_per_date = {}
        for slot in data.get('slots', []):
            if slot.get('times'):
                dates.append(slot.get('date'))
                slots_per_date[slot.get('date')] = ', '.join(slot.get('times'))

        # Только ближайшие 3 даты
        dates = dates[:3]
        return jsonify({
            "dates": dates,
            "slots_per_date": {d: slots_per_date[d] for d in dates}
        })

    except Exception as e:
        print(f"ERROR in /free_slots: {e}")
        return jsonify({"error": str(e)}), 500

# 2. Endpoint для слотов на выбранную дату
@app.route('/slots_for_date', methods=['POST'])
def get_slots_for_date():
    try:
        data = request.json or {}
        # Можно использовать 'date', 'date_from', 'date_to' — главное, чтобы была одна дата
        date = data.get('date') or data.get('date_from')
        if not is_real_date(date):
            return jsonify({"slots": "Нет даты для поиска"}), 400

        payload = {
            "required_capacity": "1",
            "search_weeks_range": 0,
            "merchant_id": "3c32f625-c162-4293-98c0-2551c920a5ed",
            "services_resources": [
                {"service_id": "991deea0-4da5-487f-b1d0-2d78869525ab"}
            ],
            "starts_at": f"{date} 00:00:00",
            "ends_at": f"{date} 23:59:59",
            "timezone": "Europe/Berlin"
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://connect.shore.com",
            "Referer": "https://connect.shore.com/"
        }

        response = requests.post(
            "https://api.shore.com/v2/availability/calculate_slots",
            json=payload, headers=headers, timeout=15
        )
        data = response.json()

        slots = []
        for slot in data.get('slots', []):
            if slot.get('date') == date and slot.get('times'):
                slots = slot['times']
                break

        slots_str = ', '.join(slots) if slots else "Нет доступных времен"
        return jsonify({"slots": slots_str})

    except Exception as e:
        print(f"ERROR in /slots_for_date: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
