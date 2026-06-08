"""В 18:00 в день игры забирает ответ от организатора и публикует расчёт в группу."""
import os
import re
import sys
import math
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from common import is_cancelled, notify_cancelled

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
MY_USER_ID = int(os.environ["MY_USER_ID"])

GAMES = {
    0: {"day_ru": "Пнд.", "cost": 6000},
    3: {"day_ru": "Чтв.", "cost": 5400},
}

MIN_PLAYERS = 10
CANCEL_TEXT = "Ребят, на сегодня игра не собралась, отменяем"
PAYMENT_TEMPLATE = (
    "Ребят, с нас {cost} за 1.5 часа, нас {n}, переводим по {per} руб. "
    "СРАЗУ КАК УВИДЕЛИ СООБЩЕНИЕ ‼️‼️‼️\n\n"
    "{phone} ТОЛЬКО Т - БАНК ‼️‼️‼️ ПЕРЕВОДИМ ДЕНЬГИ СРАЗУ ПОЖАЛУЙСТА ‼️‼️‼️ "
    "НАЛИЧКУ НЕ ПРИНИМАЮ\n\n"
    "ОТМЕЧАЙТЕСЬ ОБЯЗАТЕЛЬНО 👍‼️‼️‼️"
)

PHONE_RE = re.compile(r"^\+?[78]?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$")

TZ = ZoneInfo("Europe/Samara")
API = f"https://api.telegram.org/bot{TOKEN}"


def send_to_user(text):
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": MY_USER_ID, "text": text},
        timeout=30,
    )


def send_to_chat(text):
    r = requests.post(
        f"{API}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=30,
    )
    if not r.ok:
        print(f"Ошибка отправки в чат: {r.status_code} {r.text}")
        sys.exit(1)


def normalize_phone(raw):
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return "+" + digits


today = datetime.now(TZ)
game = GAMES.get(today.weekday())

if not game:
    print(f"Сегодня {today.strftime('%A')} — не игровой день, выхожу")
    sys.exit(0)

if is_cancelled(API, MY_USER_ID):
    notify_cancelled(API, MY_USER_ID, "публикация расчёта")
    print("Найдена стоп-команда — публикация расчёта отменена")
    sys.exit(0)

r = requests.get(f"{API}/getUpdates", timeout=30)
if not r.ok:
    print(f"Не удалось получить обновления: {r.status_code} {r.text}")
    sys.exit(1)

updates = r.json().get("result", [])
last_number = None
last_phone = None

for u in updates:
    msg = u.get("message") or {}
    frm = msg.get("from") or {}
    if frm.get("id") != MY_USER_ID:
        continue
    text = (msg.get("text") or "").strip()
    if not text:
        continue
    if text.isdigit():
        last_number = int(text)
        continue
    if PHONE_RE.match(text.replace(" ", "")):
        last_phone = normalize_phone(text)

print(f"Получено: число={last_number}, номер={last_phone}")

missing = []
if last_number is None:
    missing.append("число игроков")
if last_phone is None:
    missing.append("номер телефона")

if missing:
    send_to_user(
        f"Не нашёл: {', '.join(missing)}.\n"
        f"Опубликуй расчёт в чат вручную."
    )
    print(f"Не хватает данных: {missing}")
    sys.exit(0)

if last_number < MIN_PLAYERS:
    print(f"Меньше минимума ({MIN_PLAYERS}) — публикуем отмену")
    send_to_chat(CANCEL_TEXT)
    sys.exit(0)

cost = game["cost"]
per_person = math.ceil(cost / last_number)
message = PAYMENT_TEMPLATE.format(
    cost=cost, n=last_number, per=per_person, phone=last_phone
)
send_to_chat(message)
print(f"Расчёт опубликован: {cost} / {last_number} = {per_person} руб, номер {last_phone}")
