"""Общие функции для всех скриптов бота."""
import time
import requests


def is_cancelled(api_url, my_user_id, window_hours=6):
    """Проверяет, отправил ли организатор /stop за последние window_hours часов."""
    r = requests.get(
        f"{api_url}/getUpdates",
        params={
            "allowed_updates": '["message"]',
            "limit": 100,
        },
        timeout=30,
    )
    if not r.ok:
        print(f"Не удалось проверить стоп-команду: {r.status_code} {r.text}")
        return False

    cutoff = time.time() - window_hours * 3600
    for u in r.json().get("result", []):
        msg = u.get("message") or {}
        chat = msg.get("chat") or {}
        if chat.get("type") != "private":
            continue
        if (msg.get("from") or {}).get("id") != my_user_id:
            continue
        if msg.get("date", 0) < cutoff:
            continue
        text = (msg.get("text") or "").strip().lower()
        if text == "/stop":
            return True
    return False


def notify_cancelled(api_url, my_user_id, what):
    """Уведомляет организатора, что действие отменено."""
    requests.post(
        f"{api_url}/sendMessage",
        json={
            "chat_id": my_user_id,
            "text": f"Отменено по твоей команде /stop: {what}",
        },
        timeout=30,
    )
