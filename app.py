import threading
import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --------------- ПРОЦЕДУРЫ (категории, xpath, id, цена) ---------------------
PROCEDURES = [
    {'big_category': 'Laser Haarentfernung', 'name': 'BERATUNG (kostenlos)', 'price': '0', 'first_xpath': '//*[@id="root"]/section/div[2]/ul/li[1]', 'second_xpath': '//*[@id="root"]/section/div[2]/ul/li[1]/ul/li[1]', 'service_id': 'e5df07c6-c700-404b-93e1-1b5f3cc04970'},
    # Добавьте все другие процедуры сюда
]

# --------------------------------------------------------------------------

app = Flask(__name__)

def is_real_date(val):
    return val and isinstance(val, str) and not val.startswith('{{') and not val.endswith('}}')

@app.route('/free_slots', methods=['POST'])
def get_free_slots():
    try:
        data = request.json or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        service_id = data.get('service_id')
        if not is_real_date(date_from):
            date_from = datetime.now().strftime("%Y-%m-%d")
        if not is_real_date(date_to):
            date_to = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        if not service_id:
            return jsonify({"error": "service_id required"}), 400

        payload = {
            "required_capacity": "1",
            "search_weeks_range": 0,
            "merchant_id": "3c32f625-c162-4293-98c0-2551c920a5ed",
            "services_resources": [
                {"service_id": service_id}
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

        dates = dates[:3]
        return jsonify({
            "dates": dates,
            "slots_per_date": {d: slots_per_date[d] for d in dates}
        })

    except Exception as e:
        print(f"ERROR in /free_slots: {e}")
        return jsonify({"error": str(e)}), 500

def run_selenium_book(first_xpath, second_xpath, month_input, day_input, time_input, price):
    chrome_path = r"/usr/bin/google-chrome"
    driver_path = r"/opt/render/project/src/chromedriver"

    options = Options()
    options.binary_location = chrome_path
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    service = Service(executable_path=driver_path)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://connect.shore.com/bookings/laser-one-institut-dauerhafte-laser-haarentfernung-apparative-aesthetik/services?locale=de")
    wait = WebDriverWait(driver, 20)

    try:
        cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')))
        cookie_btn.click()

        first_level = wait.until(EC.element_to_be_clickable((By.XPATH, first_xpath)))
        first_level.click()

        second_level = wait.until(EC.element_to_be_clickable((By.XPATH, second_xpath)))
        second_level.click()

        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div[6]/div/div[2]')))
        next_btn.click()

        month_btn_xpath = '//*[@id="root"]/section/div[1]/div[2]/div/div[1]/div/div[1]/button[2]'
        next_month_btn_xpath = '//*[@id="root"]/section/div[1]/div[2]/div/div[1]/div/div[1]/button[3]'
        prev_month_btn_xpath = '//*[@id="root"]/section/div[1]/div[2]/div/div[1]/div/div[1]/button[1]'

        month_btn = wait.until(EC.visibility_of_element_located((By.XPATH, month_btn_xpath)))
        current_month_name = month_btn.text.strip()

        max_swipes = 12
        for i in range(max_swipes):
            if current_month_name != month_input:
                wait.until(EC.element_to_be_clickable((By.XPATH, next_month_btn_xpath))).click()
                month_btn = wait.until(EC.visibility_of_element_located((By.XPATH, month_btn_xpath)))
                current_month_name = month_btn.text.strip()
            else:
                break

        day_xpath = f'//*[@id="root"]/section/div[1]/div[2]/div/div[1]/div/div[2]/div/ul//button[span[text()="{day_input}"]]'
        day_btn = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
        day_btn.click()

        time_xpath = f'//button[.//div[text()="{time_input}"]]'
        time_btn = wait.until(EC.element_to_be_clickable((By.XPATH, time_xpath)))
        time_btn.click()

        final_next_btn_xpath = '//*[@id="root"]/section/div[2]/div/button'
        final_next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, final_next_btn_xpath)))
        final_next_btn.click()

        print(f"\nСумма к оплате: {price} €")

        print("Ждём поля ввода для контактов...")
        contact_fields = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="input-undefined"]'))
        )

        first_name = input("Имя: ").strip()
        last_name = input("Фамилия: ").strip()
        email = input("Email: ").strip()
        phone = input("Телефон: ").strip()

        contact_fields[0].send_keys(first_name)
        contact_fields[1].send_keys(last_name)
        contact_fields[2].send_keys(email)
        contact_fields[3].send_keys(phone)

        send_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/section/div[2]/div/button'))
        )
        send_btn.click()
        print("Форма отправлена!")

    except Exception as e:
        print(f"Ошибка Selenium: {e}")
    input("Нажми Enter для выхода...")
    driver.quit()

def run_flask():
    app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(1)
