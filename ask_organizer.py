"""В день игры в 17:30 спрашивает у организатора, сколько в итоге идёт."""
import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
MY_USER_ID = os.environ["MY_USER_ID"]

# Игры по дню недели (0=Пн, 1=Вт ... 6=Вс)
GAMES = {
    0: {"day_ru": "Пнд.", "location": "Революционная", "time": "19:30", "cost": 6000},
    3: {"day_ru": "Чтв.", "location": "Антошка",       "time": "21:00", "cost": 5400},
}

TZ = ZoneInfo("Europe/Samara")
API = f"https://api.telegram.org/bot{TOKEN}"

today = datetime.now(TZ)
game = GAMES.get(today.weekday())

if not game:
    print(f"Сегодня {today.strftime('%A')} — не игровой день, выхожу")
    sys.exit(0)

game_label = f"{game['day_ru']} {today.strftime('%d.%m')} {game['location']} {game['time']}"
message = (
    f"Сегодня игра: {game_label}\n"
    f"Стоимость: {game['cost']} руб.\n\n"
    f"Сколько в итоге идёт людей (с учётом «плюсов»)?\n"
    f"Ответь мне числом в этот чат до 18:00 — опубликую расчёт в группу."
)

response = requests.post(
    f"{API}/sendMessage",
    json={"chat_id": MY_USER_ID, "text": message},
    timeout=30,
)

if not response.ok:
    print(f"Telegram ответил ошибкой: {response.status_code}")
    print(f"Текст ответа: {response.text}")
    sys.exit(1)

print(f"Вопрос отправлен организатору про игру: {game_label}")
