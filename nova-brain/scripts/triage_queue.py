"""Triage de la cola WS new+open (SOLO LECTURA). workflows.md §A2.
  python3 -I triage_queue.py [--out /ruta/ws_triage.json]
Qué hace: baja los tickets, lee el último mensaje del worker por Sunshine (en mensajería el contenido NO está
en los comentarios de Zendesk), clasifica por tema y agrupa duplicados por nombre del worker.
Imprime resumen por bloques (CX fácil / área / revisar) con IDs, y los grupos de duplicados de alta confianza.
No envía ni modifica nada. La clasificación es por regex: úsala como primer corte, no como verdad."""
import os, sys, re, json, argparse, collections, unicodedata
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zd import search_export, category_labels, nova_note, comments, WS
import sunco

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="ws_triage.json")
a = ap.parse_args()

RULES = [  # el primero que coincide gana
    ("Token dinámico / cuenta bloqueada", r"token|dynamic|bloque|blocked|desbloq|restring|no puedo (entrar|acceder|operar|transferir|retir)"),
    ("Contraseña / acceso / OTP", r"contrase|password|olvid|iniciar sesi|log ?in|\botp\b|c[oó]digo de (verif|seg)|no me llega el c[oó]digo"),
    ("Transferencia pendiente / no llega", r"pendiente|pending|no (me )?(ha )?lleg|no he recibido|still processing|en proceso|demora|tarda|retir|withdraw|transfer.*(no|pend|demor)|d[oó]nde.*(dinero|plata|transfer)"),
    ("Transferencia rechazada / devuelta / recall", r"rechaz|reject|devuel|returned|recall|revers|bounce|regresaron"),
    ("Compra no reconocida / tarjeta", r"tarjeta|\bcard\b|cobro|charge|compra no|unrecognized|no reconoz|reembols|refund|chargeback|declin|thredd|virtual|f[ií]sica"),
    ("Compensación / salario no recibido", r"compensa|salario|salary|no me (pag|deposit)|payment not|didn.?t (get|receive)|cliente no (pag|deposit)|employer"),
    ("Paycheck Advance / adelanto", r"paycheck|adelanto|advance|anticip"),
    ("KYC / verificación / face match", r"\bkyc\b|verif|face ?match|selfie|identidad|identity|documento|document|id number|tax id|c[eé]dula|pasaporte|validar"),
    ("Eliminar / cerrar cuenta", r"elimin|borrar.*cuenta|delete|close.*account|cerrar.*cuenta|dar de baja"),
    ("Certificado / extracto / comprobante", r"certific|extracto|statement|comprobante|constancia|proof of payment|carta (laboral|de)"),
    ("Future Fund / Boost / Reserve", r"future ?fund|boost|reserve|wanderlust|recompens"),
    ("Stablecoin / USDC", r"stablecoin|usdc|usdt|cripto|crypto"),
    ("Onboarding / crear-activar cuenta", r"crear cuenta|sign ?up|registr|activar|onboarding|invitaci|no me deja crear"),
    ("Datos cuenta / banco / edición", r"cambiar.*(banco|cuenta|correo|email|n[uú]mero)|actualizar.*dato|editar|wrong.*account|datos banc|beneficiar|cuenta banc"),
    ("Saludo / sin contexto", r"^\W*(hola|hi|hello|buenas|gracias|thanks|ok|s[ií]|no)\W*$|^.{0,12}$|asesor|agente|humano|representante|soporte|when.*(support|agent)"),
]
EASY = {"Token dinámico / cuenta bloqueada", "Contraseña / acceso / OTP", "Eliminar / cerrar cuenta", "Certificado / extracto / comprobante",
        "Paycheck Advance / adelanto", "Future Fund / Boost / Reserve", "Onboarding / crear-activar cuenta"}
FIRST_TOUCH = {"Saludo / sin contexto"}   # fácil de despachar, pero necesita primer toque humano (macro + identificar)
AREA = {"Transferencia pendiente / no llega": "Payouts (Camila)", "Transferencia rechazada / devuelta / recall": "Payouts (Camila)",
        "Compra no reconocida / tarjeta": "Card Ops", "Compensación / salario no recibido": "Account Mgmt (cliente no pagó)",
        "KYC / verificación / face match": "Compliance (Jorge) / Tech (Lucho)", "Stablecoin / USDC": "Payouts / Tech",
        "Datos cuenta / banco / edición": "Payouts / Tech"}
MSG = {"whatsapp", "native_messaging", "sunshine_conversations_api"}


def norm_name(s):
    m = re.search(r"conversation with\s+(.*)$", s or "", re.I)
    n = unicodedata.normalize("NFKD", (m.group(1) if m else "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", n)).strip()


def content(t):
    """Último mensaje del worker. Mensajería → Sunshine; otros → primeros comentarios públicos."""
    try:
        if t.get("via", {}).get("channel") in MSG:
            conv = sunco.conversation_id(t["id"])
            if conv:
                us = [m["content"].get("text", "") for m in sunco.messages(conv) if m["author"]["type"] == "user" and m["content"].get("text")]
                if us:
                    return t["id"], us[-1][:500]
        pub = [c["body"] for c in comments(t["id"]) if c.get("public") and c.get("body")]
        return t["id"], " ".join(pub[:2])[:500]
    except Exception:
        return t["id"], ""


T = search_export(f"type:ticket group:{WS} status:new status:open")
cats = category_labels()
with ThreadPoolExecutor(12) as ex:
    txt = dict(ex.map(content, T))
rows = []
for t in T:
    s = (txt.get(t["id"]) or "").lower()
    topic = "Sin texto (abrir manual)" if not s.strip() else next((n for n, p in RULES if re.search(p, s)), "Otro / general")
    rows.append({"id": t["id"], "status": t["status"], "via": t.get("via", {}).get("channel"), "created": t["created_at"][:10],
                 "assignee_id": t.get("assignee_id"), "name": norm_name(t.get("subject")), "topic": topic, "txt": txt.get(t["id"], "")})
json.dump(rows, open(a.out, "w"), ensure_ascii=False)

print(f"WS new+open: {len(rows)} | sin dueño: {sum(1 for r in rows if not r['assignee_id'])} | mensajería: {sum(1 for r in rows if r['via'] in MSG)}")
c = collections.Counter(r["topic"] for r in rows)
tot = collections.Counter()
for topic, n in c.most_common():
    kind = "CX fácil" if topic in EASY else ("primer toque" if topic in FIRST_TOUCH else (f"área: {AREA[topic]}" if topic in AREA else "revisar"))
    tot[kind.split(":")[0]] += n
    ids = " ".join(f"#{r['id']}" for r in rows if r["topic"] == topic)[:160]
    print(f"{n:4}  {topic:44} [{kind}]  {ids if topic in EASY else ''}")
print("Totales:", dict(tot))

by = collections.defaultdict(list)
for r in rows:
    if len(r["name"].split()) >= 2 and not r["name"].startswith("user "):
        by[r["name"]].append(r["id"])
dups = {n: sorted(v) for n, v in by.items() if len(v) > 1}
print(f"\nDuplicados por nombre completo (alta confianza): {len(dups)} grupos, {sum(len(v) - 1 for v in dups.values())} tickets colapsables")
for n, v in sorted(dups.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(v)}x " + " ".join(f"#{i}" for i in v))
print(f"\nDetalle guardado en {a.out}. Siguiente paso para duplicados: dedup_consolidate.py (dry-run) y OK de Mike.")
