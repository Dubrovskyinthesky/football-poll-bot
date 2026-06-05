"""Отправляет опрос по футболу в Телеграм-чат и закрепляет его."""
import os
import sys
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ====== Настройки игр ======
# Ключ — день недели, КОГДА БОТ ШЛЁТ ОПРОС:
# 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт, 5=Сб, 6=Вс
# days_ahead — через сколько дней игра
GAMES = {
    1: {  # Вторник шлём → игра в четверг
        "day_ru": "Чтв.",
        "location": "Антошка",
        "time": "21:00",
        "days_ahead": 2,
    },
    4: {  # Пятница шлём → игра в понедельник
        "day_ru": "Пнд.",
        "location": "Революционная",
        "time": "19:30",
        "days_ahead": 3,
    },
}
# ===========================

TZ = ZoneInfo("Europe/Samara")
API = f"https://api.telegram.org/bot{TOKEN}"

today = datetime.now(TZ)
game = GAMES.get(today.weekday())

if not game:
    print(f"Сегодня {today.strftime('%A')} — опрос не запланирован, выхожу")
    sys.exit(0)

game_date = today + timedelta(days=game["days_ahead"])
question = f"{game['day_ru']} {game_date.strftime('%d.%m')} {game['location']} {game['time']}"

# Отправляем опрос
poll_response = requests.post(
    f"{API}/sendPoll",
    json={
        "chat_id": CHAT_ID,
        "question": question,
        "options": ["✅", "❌", "❓"],
        "is_anonymous": False,
        "allows_multiple_answers": False,
    },
    timeout=30,
)
poll_response.raise_for_status()
message_id = poll_response.json()["result"]["message_id"]
print(f"Отправлен опрос: {question} (message_id={message_id})")

# Закрепляем опрос
pin_response = requests.post(
    f"{API}/pinChatMessage",
    json={
        "chat_id": CHAT_ID,
        "message_id": message_id,
        "disable_notification": False,
    },
    timeout=30,
)
if pin_response.ok:
    print("Опрос закреплён")
else:
    # Не валим всё, если закрепить не удалось — просто логируем
    print(f"Не удалось закрепить: {pin_response.text}")
