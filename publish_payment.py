"""В 18:00 в день игры забирает ответ от организатора и публикует расчёт в группу."""
import os
import sys
import math
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
MY_USER_ID = int(os.environ["MY_USER_ID"])

GAMES = {
       0: {"day_ru": "Пнд.", "cost": 6000},
       3: {"day_ru": "Чтв.", "cost": 5400},
       4: {"day_ru": "ТЕСТ", "cost": 6000},
   }

MIN_PLAYERS = 10
CANCEL_TEXT = "Ребят, на сегодня игра не собралась, отменяем"
PAYMENT_TEMPLATE = (
    "Ребят, с нас {cost} за 1.5 часа, нас {n}, переводим по {per} руб. "
    "СРАЗУ КАК УВИДЕЛИ СООБЩЕНИЕ ‼️‼️‼️\n\n"
    "+79631166077 ТОЛЬКО Т - БАНК ‼️‼️‼️ ПЕРЕВОДИМ ДЕНЬГИ СРАЗУ ПОЖАЛУЙСТА ‼️‼️‼️ "
    "НАЛИЧКУ НЕ ПРИНИМАЮ\n\n"
    "ОТМЕЧАЙТЕСЬ ОБЯЗАТЕЛЬНО 👍‼️‼️‼️"
)

TZ = ZoneInfo("Europe/Samara")
API = f"https://api.telegram.org/bot{TOKEN}"


def send_to_user(text):
    """Шлёт сообщение в личку организатору."""
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": MY_USER_ID, "text": text},
        timeout=30,
    )


def send_to_chat(text):
    """Шлёт сообщение в групповой чат."""
    r = requests.post(
        f"{API}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=30,
    )
    if not r.ok:
        print(f"Ошибка отправки в чат: {r.status_code} {r.text}")
        sys.exit(1)


today = datetime.now(TZ)
game = GAMES.get(today.weekday())

if not game:
    print(f"Сегодня {today.strftime('%A')} — не игровой день, выхожу")
    sys.exit(0)

# Забираем все обновления, ищем последнее сообщение от организатора
r = requests.get(f"{API}/getUpdates", timeout=30)
if not r.ok:
    print(f"Не удалось получить обновления: {r.status_code} {r.text}")
    sys.exit(1)

updates = r.json().get("result", [])
last_number = None
for u in updates:
    msg = u.get("message") or {}
    frm = msg.get("from") or {}
    if frm.get("id") != MY_USER_ID:
        continue
    text = (msg.get("text") or "").strip()
    if text.isdigit():
        last_number = int(text)
        # перебираем все, чтобы найти ПОСЛЕДНЕЕ число — не делаем break

if last_number is None:
    print("Числовой ответ от организатора не найден")
    send_to_user(
        f"Не нашёл твой ответ числом на вопрос про сегодняшнюю игру "
        f"({game['day_ru']}). Опубликуй расчёт в чат вручную."
    )
    sys.exit(0)

print(f"Получено число от организатора: {last_number}")

if last_number < MIN_PLAYERS:
    print(f"Меньше минимума ({MIN_PLAYERS}) — публикуем отмену")
    send_to_chat(CANCEL_TEXT)
    print("Сообщение об отмене опубликовано")
    sys.exit(0)

cost = game["cost"]
per_person = math.ceil(cost / last_number)
message = PAYMENT_TEMPLATE.format(cost=cost, n=last_number, per=per_person)
send_to_chat(message)
print(f"Расчёт опубликован: {cost} / {last_number} = {per_person} руб с человека")
