"""Sunshine Conversations (WhatsApp / chat de Zendesk) para Nova.
Credenciales del entorno: SUNCO_APP_ID, SUNCO_KEY_ID, SUNCO_KEY_SECRET (+ CX_ZENDESK_*).
CLI:
  python3 -I sunco.py last <ticket> [n]          # últimos n mensajes
  python3 -I sunco.py send <ticket> "<texto>"    # envía texto (o template si WhatsApp >24 h)
"""
import os, sys, json, datetime, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zd import get as zget

H = f"https://{os.environ['CX_ZENDESK_SUBDOMAIN']}.zendesk.com/sc/v2/apps/{os.environ['SUNCO_APP_ID']}"
S = (os.environ["SUNCO_KEY_ID"], os.environ["SUNCO_KEY_SECRET"])
WA_INTEGRATION = "65d7c6897da3f1e6aaa17aa0"   # WhatsApp real
FORBIDDEN_INTEGRATION = "663b9636d2bd090b34b10e2b"  # Prueba CS: nunca
AUTHOR = {"type": "business", "displayName": "Ontop Support"}


def conversation_id(ticket_id):
    for a in zget(f"/tickets/{ticket_id}/audits.json")["audits"]:
        for e in a["events"]:
            if e.get("type") == "ChatStartedEvent":
                return e["value"].get("conversation_id")
    return None


def messages(conv):
    return requests.get(f"{H}/conversations/{conv}/messages?page%5Bsize%5D=100", auth=S).json().get("messages", [])


def last_user_at(msgs):
    us = [m["received"] for m in msgs if m["author"]["type"] == "user"]
    return datetime.datetime.fromisoformat(us[-1].replace("Z", "+00:00")) if us else None


def is_whatsapp(msgs):
    return any((m.get("source") or {}).get("type") == "whatsapp" for m in msgs if m["author"]["type"] == "user")


def send_text(conv, text):
    return requests.post(f"{H}/conversations/{conv}/messages", auth=S,
                         json={"author": AUTHOR, "content": {"type": "text", "text": text}}).status_code


def send_template(conv, lang="es"):
    body = {"author": AUTHOR, "content": {"type": "text", "text": "reactivar_conversacion"},
            "destination": {"integrationId": WA_INTEGRATION},
            "override": {"whatsapp": {"payload": {"type": "template", "template": {
                "name": "reactivar_conversacion", "language": {"policy": "deterministic", "code": lang}}}}}}
    return requests.post(f"{H}/conversations/{conv}/messages", auth=S, json=body).status_code


def send_file(conv, path, alt):
    up = requests.post(f"{H}/attachments", params={"access": "public", "for": "message", "conversationId": conv},
                       auth=S, files={"source": (os.path.basename(path), open(path, "rb"))}).json()
    url = up["attachment"]["mediaUrl"]
    return requests.post(f"{H}/conversations/{conv}/messages", auth=S,
                         json={"author": AUTHOR, "content": {"type": "file", "mediaUrl": url, "altText": alt}}).status_code


def smart_send(ticket_id, text, lang="es"):
    """Envía texto; si es WhatsApp y el último mensaje del usuario tiene >24 h, manda template.
    Devuelve ('text'|'template'|'no_conv', status)."""
    conv = conversation_id(ticket_id)
    if not conv:
        return "no_conv", None
    msgs = messages(conv)
    lu = last_user_at(msgs)
    if is_whatsapp(msgs) and (lu is None or datetime.datetime.now(datetime.timezone.utc) - lu > datetime.timedelta(hours=24)):
        return "template", send_template(conv, lang)
    return "text", send_text(conv, text)


if __name__ == "__main__":
    cmd, tid = sys.argv[1], sys.argv[2]
    if cmd == "last":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 6
        for m in messages(conversation_id(tid))[-n:]:
            c = m["content"]
            print(m["received"][:16], m["author"]["type"][:4], (c.get("text") or c["type"])[:220].replace("\n", " "))
    elif cmd == "send":
        print(smart_send(tid, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "es"))
