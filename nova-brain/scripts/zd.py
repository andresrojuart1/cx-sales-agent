"""Helpers de Zendesk para Nova. Credenciales SOLO desde el entorno:
CX_ZENDESK_EMAIL, CX_ZENDESK_TOKEN, CX_ZENDESK_SUBDOMAIN. Nunca imprimir el token.
Uso: from zd import *   (correr con python3 -I desde esta carpeta, o sys.path.insert)
"""
import os, time, re, requests

SUB = os.environ["CX_ZENDESK_SUBDOMAIN"]
ZD = f"https://{SUB}.zendesk.com/api/v2"
AUTH = (os.environ["CX_ZENDESK_EMAIL"] + "/token", os.environ["CX_ZENDESK_TOKEN"])

WS, CS = 22616861202452, 23897889259668
ST_OPEN, ST_WAITING, ST_IR = 22614166894100, 25685916283028, 31769974642836
MISCLASSIFIED = 35555524967060  # NUNCA tocar
ONTOP_SUPPORT = 26024622590356
CX_TEAM = {54788295418644: "Justin", 24567978777492: "Sudu", 47071350698516: "Brisa",
           48493524357268: "Cristian", 55350915332244: "Jaime", 32288140085012: "Carolina",
           40230868739348: "Samuel", 28269839522452: "Miguel", 42677627758740: "Mike"}
UKRAINE = {254530, 255396, 256436, 256169, 256638, 256637, 256966, 256886, 256992}


def _req(method, url, **kw):
    for _ in range(6):
        r = requests.request(method, url, auth=AUTH, timeout=60, **kw)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10)))
            continue
        return r
    return r


def get(path, **params):
    return _req("GET", ZD + path, params=params).json()


def put(path, body):
    assert str(MISCLASSIFIED) not in str(body), "Nunca tocar Misclassified Ticket"
    return _req("PUT", ZD + path, json=body)


def count(query):
    return get("/search/count.json", query=query)["count"]


def search_export(query):
    """Todos los tickets de una búsqueda (sin límite de 1000)."""
    out, url, p = [], ZD + "/search/export.json", {"query": query, "filter[type]": "ticket", "page[size]": 1000}
    while url:
        d = _req("GET", url, params=p).json()
        out += d["results"]; p = None
        url = d["links"]["next"] if d["meta"]["has_more"] else None
    return out


def show_many(ids):
    out = []
    ids = [str(i) for i in ids]
    for k in range(0, len(ids), 100):
        out += get("/tickets/show_many.json", ids=",".join(ids[k:k + 100]))["tickets"]
    return out


def users(ids):
    ids = [str(i) for i in set(ids) if i]
    out = {}
    for k in range(0, len(ids), 100):
        for u in get("/users/show_many.json", ids=",".join(ids[k:k + 100]))["users"]:
            out[u["id"]] = u["name"]
    return out


def update_many(ids, ticket):
    """PUT update_many en lotes de 100 y espera el job. ticket = dict del cuerpo 'ticket'."""
    ids = [str(i) for i in ids if int(i) not in UKRAINE]
    res = []
    for k in range(0, len(ids), 100):
        j = put("/tickets/update_many.json?ids=" + ",".join(ids[k:k + 100]), {"ticket": ticket}).json()["job_status"]["url"]
        for _ in range(40):
            s = _req("GET", j).json()["job_status"]
            if s["status"] in ("completed", "failed", "killed"):
                break
            time.sleep(3)
        res.append(s["status"])
    return res


def note(ticket_id, body, **fields):
    t = {"comment": {"public": False, "body": body}}; t.update(fields)
    return put(f"/tickets/{ticket_id}.json", {"ticket": t}).status_code


def add_tags(ticket_id, tags):
    """Agrega etiquetas SIN perder las existentes y verifica. NO usar additional_tags:
    PUT /tickets devuelve 200 pero lo ignora en silencio. Devuelve True solo si quedaron."""
    tags = set(tags)
    cur = get(f"/tickets/{ticket_id}.json")["ticket"]["tags"]
    r = put(f"/tickets/{ticket_id}.json", {"ticket": {"tags": sorted(set(cur) | tags)}})
    return r.status_code == 200 and tags <= set(get(f"/tickets/{ticket_id}.json")["ticket"]["tags"])


def csat_score(ticket_id):
    """'unoffered' | 'offered' | 'good' | 'bad'... Leer ≥30 s después de resolver."""
    sr = get(f"/tickets/{ticket_id}.json")["ticket"].get("satisfaction_rating") or {}
    return sr.get("score", "unoffered")


def public_reply(ticket_id, body, author_id=ONTOP_SUPPORT, **fields):
    """Solo para tickets de correo/web/api. En mensajería usar sunco.py."""
    t = {"comment": {"public": True, "body": body, "author_id": author_id}}; t.update(fields)
    return put(f"/tickets/{ticket_id}.json", {"ticket": t}).status_code


def comments(ticket_id):
    return get(f"/tickets/{ticket_id}/comments.json", per_page=100)["comments"]


def nova_note(ticket_id):
    """Devuelve dict con Ask/Onsight/Suggested action de la última nota de Nova, o {}."""
    cs = [c["body"] for c in comments(ticket_id) if not c["public"] and "Nova · Domain routing" in c["body"]]
    if not cs:
        return {}
    b = cs[-1]; out = {}
    for k in ["Ask", "Onsight", "Side conversations", "Duplicates", "Suggested action"]:
        m = re.search(r"• " + k + r":(.*?)(?=\n• |\nRouting|\n📱|$)", b, re.S)
        if m:
            out[k] = re.sub(r"\s+", " ", m.group(1)).strip()
    return out


def category_labels():
    f = get("/ticket_fields/22865771347348.json")["ticket_field"]
    return {o["value"]: o["name"] for o in f.get("custom_field_options", [])}
