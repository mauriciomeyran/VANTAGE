#!/usr/bin/env python3
"""
VANTAGE Mail Metadata Analysis — v2
Analiza ~1669 correos via IMAP (igual que himalaya, mismo canal).
Volcado de metadata + clustering + propuesta de reglas.
NO toca contenido ni hace mutations. Solo lectura.
"""

import imaplib
import email
import json
import re
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path

GMAIL_USER = "mauricio.meyran@gmail.com"
GMAIL_APP_PASS = "rmgsxlojhbsvlxde"


def _decode_mime(s):
    if not s:
        return ""
    try:
        parts = decode_header(s)
        out = []
        for part, charset in parts:
            if isinstance(part, bytes):
                out.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                out.append(str(part))
        return "".join(out)
    except Exception:
        return s


def _first_email(s):
    """Extrae el email del header From."""
    if not s:
        return ""
    m = re.search(r"<([^>]+@[^>]+)>", s)
    if m:
        return m.group(1)
    parts = s.replace("(", " ").replace(")", " ").split()
    for p in reversed(parts):
        if "@" in p:
            return p.strip("<>")
    return s.strip().strip("<>")


def _domain(email_addr):
    if "@" in email_addr:
        return email_addr.split("@")[1].lower()
    return ""


def _parse_date(s):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except Exception:
        return None


def login():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASS)
    return mail


def fetch_envelopes(mail, quota=None):
    """Fetch envelopes from [Gmail]/All Mail con labels."""
    mail.select('"All Mail"')
    typ, data = mail.search(None, "ALL")
    ids = data[0].split()
    total = len(ids)
    print(f"📦 Total mensajes en All Mail: {total}")
    if quota and total > quota:
        print(f"⚠️  Limité a {quota} (quota) — usando los más recientes")
        ids = ids[:quota]
        total = quota

    envelopes = []
    BATCH = 50

    for i in range(0, total, BATCH):
        chunk = ids[i:i+BATCH]
        batch_str = b",".join(chunk)
        typ, data = mail.fetch(batch_str, "(RFC822 X-GM-LABELS)")
        if typ != "OK":
            continue

        for entry in data:
            if not entry or not entry[0]:
                continue
            raw = entry[0]
            if isinstance(raw, tuple):
                raw = raw[1]
            if not raw or not isinstance(raw, (bytes, bytearray)):
                continue
            try:
                msg = email.message_from_bytes(raw)
                from_h = _first_email(msg.get("From", ""))
                subj = _decode_mime(msg.get("Subject") or "")
                d = _parse_date(msg.get("Date", ""))
                mid = msg.get("Message-ID", "")

                # X-GM-LABELS viene como segunda parte del fetch
                labels = []
                if len(entry) > 1 and entry[1]:
                    lbls_raw = entry[1]
                    if isinstance(lbls_raw, bytes):
                        labels = [l.decode("utf-8") for l in lbls_raw.split()]
                    else:
                        labels = [str(lbls_raw)]

                envelopes.append({
                    "id": mid,
                    "from": from_h,
                    "subject": subj,
                    "date": d.isoformat() if d else None,
                    "date_dt": d,
                    "labels": labels,
                })
            except Exception:
                pass

        if i % 500 == 0 and i > 0:
            print(f"  ⏳ {i}/{total} envelopes procesados")

    print(f"✅ {len(envelopes)} envelopes capturados")
    return envelopes


def cluster_senders(envelopes):
    """Agrupa por dominio + rol del remitente."""
    groups = defaultdict(list)
    for e in envelopes:
        f = e["from"]
        d = _domain(f)
        clean = re.sub(r"[\\._\-]+", " ", f.split("@")[0]).lower() if "@" in f else f.lower()

        # Categorizar
        cat = None
        fl = f.lower()
        if any(k in fl for k in ["no-reply", "noreply"]):
            cat = f"no-reply.{d}"
        elif "notifications" in fl:
            cat = f"notif.{d}"
        elif "github" in d:
            cat = "github"
        elif "linkedin" in d:
            cat = "linkedin"
        elif "indeed" in d:
            cat = "indeed"
        elif "computrabajo" in d:
            cat = "computrabajo"
        elif "bumeran" in d:
            cat = "bumeran"
        elif "occ" in d:
            cat = "occ"
        elif "google" in d:
            cat = "google"
        elif "apple" in d:
            cat = "apple"
        elif "amazon" in d:
            cat = "amazon"
        elif "mailchimp" in d or "sendgrid" in d or "amazonses" in d:
            cat = f"esp.{d}"
        elif "mercadopago" in d or "mercado" in d:
            cat = "mercadopago"
        elif "bank" in d or "finance" in d or "banco" in d or "payment" in d or "pay" in d:
            cat = f"finance.{d}"
        elif "newsletter" in fl:
            cat = f"newsletter.{d}"
        elif "job" in fl or "trabajo" in fl or "empleo" in fl:
            cat = f"job.{d}"
        else:
            cat = f"other.{d}"

        groups[cat].append(e)
    return dict(groups)


def cluster_subjects(envelopes):
    """Agrupa asuntos por patrón."""
    patterns = {
        "job_new_offers": re.compile(r"nuevas?\s+(ofertas|oportunidades|vacantes)", re.I),
        "job_offers": re.compile(r"(ofertas|vacantes)\s+(de|en|para)", re.I),
        "job_matching": re.compile(r"(coinciden|encuentras|destacadas|relevantes)", re.I),
        "job_digest": re.compile(r"(resumen|bulletin|newsletter|digest|resumen)", re.I),
        "job_welcome": re.compile(r"(bienvenid|welcome|te damos)", re.I),
        "job_verification": re.compile(r"(verifica|confirm|validate|activate)", re.I),
        "job_thanks": re.compile(r"(agradecimiento|gracias por|thank you)", re.I),
        "job_reminder": re.compile(r"(recordatorio|alerta|aviso|reminder)", re.I),
        "job_tips": re.compile(r"(consejos|tips|guia|recurso|aprende|mejora|impulsa)", re.I),
        "job_application": re.compile(r"(aplica|postula|inscribi|completa|finaliza|apply|submit)", re.I),
        "finance_transfer": re.compile(r"(transferencia|envio|envío|payment|transferencia)", re.I),
        "finance_invoice": re.compile(r"(factura|invoice|cargo|cobro)", re.I),
        "finance_receipt": re.compile(r"(recibo|gift|compra|order|pedido|compra)", re.I),
        "finance_statement": re.compile(r"(state|extracto|balance|statement|account)", re.I),
        "digital_notify": re.compile(r"(likes?|comments?|shares?|followers?|new.*message|new.*connection|following|unfollow)", re.I),
        "tech_notify": re.compile(r"(deploy|build|push|commit|pull.*request|pr|issues?|pipeline|review|approved|merged)", re.I),
        "subscription": re.compile(r"(opt.*in|subscribe|unsubscribe|suscr|baja|baja|baja)", re.I),
        "security": re.compile(r"(security|seguridad|alert|alerta|suspicious|cuida|protect)", re.I),
        "password": re.compile(r"(contrasena|password|reset|restablecer|change.*password)", re.I),
        "unread_reminder": re.compile(r"(unread|no.*le[ií]do|pendiente|has.*not.*read)", re.I),
    }
    buckets = defaultdict(list)
    for e in envelopes:
        s = e["subject"]
        matched = False
        for name, pat in patterns.items():
            if pat.search(s):
                buckets[name].append(e)
                matched = True
                break
        if not matched:
            buckets["other"].append(e)
    return dict(buckets)


def time_buckets(envelopes):
    """Distribución temporal."""
    now = datetime.now(timezone.utc)
    by = defaultdict(list)
    for e in envelopes:
        d = e.get("date_dt")
        if not d:
            by["sin_fecha"].append(e)
            continue
        mo = d.strftime("%Y-%m")
        by[mo].append(e)
        if d < now.replace(day=1):
            by["antiguo"].append(e)
        else:
            by["reciente"].append(e)
    return dict(by)


def label_stats(envelopes):
    """Stats de labels."""
    counter = Counter()
    labeled = 0
    for e in envelopes:
        if e["labels"]:
            labeled += 1
        for l in e["labels"]:
            counter[l] += 1
    return counter, labeled


def main():
    mail = login()
    try:
        envs = fetch_envelopes(mail)
    finally:
        mail.logout()

    if not envs:
        print("❌ No se capturaron envelopes")
        sys.exit(1)

    total = len(envs)
    print(f"\n📊 ANÁLISIS DE {total} CORREOS")
    print("=" * 70)

    # 1. Labels
    lc, labeled = label_stats(envs)
    print(f"\n1. LABELS")
    print(f"   Mensajes con label: {labeled} ({100*labeled/total:.1f}%)")
    print(f"   Mensajes sin label: {total-labeled} ({100*(total-labeled)/total:.1f}%)")
    print("   Top labels:")
    for lbl, n in lc.most_common(15):
        print(f"     {lbl:<25} {n:>5} ({100*n/total:>5.1f}%)")

    # 2. Dominios
    doms = Counter()
    for e in envs:
        d = _domain(e["from"])
        if d:
            doms[d] += 1
    print(f"\n2. TOP 20 DOMINIOS")
    for d, n in doms.most_common(20):
        print(f"     {d:<35} {n:>5} ({100*n/total:>5.1f}%)")

    # 3. Clusters de remitente
    cs = cluster_senders(envs)
    print(f"\n3. CLUSTERS DE REMITENTE (top 25)")
    for cat, lst in sorted(cs.items(), key=lambda x: -len(x[1]))[:25]:
        doms_in = set(_domain(e["from"]) for e in lst)
        subs = list(dict.fromkeys(e["subject"][:60] for e in lst[:4]))
        print(f"\n  [{len(lst):>4}] {cat}")
        print(f"    Dominios: {', '.join(doms_in)}")
        print(f"    Asuntos muestra:")
        for s in subs:
            print(f"      - {s}")

    # 4. Patrones de asunto
    csub = cluster_subjects(envs)
    print(f"\n4. PATRONES DE ASUNTO (top)")
    for pat, lst in sorted(csub.items(), key=lambda x: -len(x[1])):
        if pat == "other":
            continue
        print(f"\n  [{len(lst):>4}] {pat}")
        for e in lst[:3]:
            print(f"    - {e['subject'][:80]}")

    # 5. Tiempo
    tb = time_buckets(envs)
    print(f"\n5. DISTRIBUCIÓN TEMPORAL (mes)")
    for mo, lst in sorted(tb.items()):
        if mo in ("sin_fecha", "antiguo", "reciente"):
            continue
        print(f"     {mo}  {len(lst):>5} ({100*len(lst)/total:>5.1f}%)")
    for k in ("sin_fecha", "antiguo", "reciente"):
        if k in tb:
            print(f"     {k:<10} {len(tb[k]):>5} ({100*len(tb[k])/total:>5.1f}%)")

    # 6. PROPUESTA DE REGLAS
    print(f"\n{'='*70}")
    print("6. PROPUESTA DE REGLAS / LABELS SUGERIDOS")
    print("=" * 70)

    jobs_n = lc.get(".Jobs", 0)
    finance_n = lc.get(".Finance", 0)
    print(f"\n  🏷️  .Jobs: {jobs_n} msgs — INGRESO L3 (no tocar)")
    print(f"  🏷️  .Finance: {finance_n} msgs — evaluar manualmente")

    # Clusters identificables
    proposals = {
        "Newsletters": re.compile(r"newsletter|newsletter|bulletin|resumen.*semanal|resumen.*diario", re.I),
        "Job alerts externos (no .Jobs)": re.compile(
            r"nuevas?\s+(ofertas|oportunidades|vacantes)|"
            r"(ofertas|vacantes)\s+(de|en|para)|"
            r"empleos?\s+recomendados|"
            r"tienes\s+\d+\s+(nuevas|ofertas)",
            re.I),
        "Notificaciones digitales (social/tech)": re.compile(
            r"(likes?|comments?|shares?|followers?|new.*message|"
            r"new.*connection|deploy|build|push|commit|pull.*request|"
            r"pr.*|issues?|pipeline|review|approved|merged)", re.I),
        "Finance / transferencia": re.compile(
            r"(transferencia|envio|env[oó]o|payment|cargo|factura|"
            r"invoice|recibo|extracto|balance|statement)", re.I),
        "Seguridad / cuenta": re.compile(
            r"(security|seguridad|alert|alerta|suspicious|"
            r"cuida|protect|verifica|confirm|validate|activate|"
            r"contrasena|password|reset)", re.I),
        "Bienvenida / onboard": re.compile(
            r"(bienvenid|welcome|te damos|confirmaci[oó]n.*registro|"
            r"postulaciones pendientes|reci[:e]niste|te registraste)", re.I),
        "Agradece / thanks": re.compile(
            r"(agradecimiento|gracias por|thank you|thanks)", re.I),
        "Unread / pendiente": re.compile(
            r"(unread|no.*le[ií]do|pendiente|has.*not.*read|recordatorio)", re.I),
    }

    for name, pat in proposals.items():
        matches = [e for e in envs if pat.search(e["subject"])]
        without_label = [e for e in matches if not e["labels"]]
        print(f"\n  📋 {name}: {len(matches)} msgs ({100*len(matches)/total:.1f}%)")
        print(f"     Sin label actual: {len(without_label)} ({100*len(without_label)/max(1,total):.1f}%)")
        for e in matches[:2]:
            print(f"     - [{','.join(e['labels']) or 'SIN LABEL'}] {e['subject'][:70]}")

    # Exportar para análisis adicional
    out = Path.home() / ".vantage" / "mail_metadata.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    clean = []
    for e in envs:
        clean.append({
            "id": e["id"],
            "from": e["from"],
            "subject": e["subject"],
            "date": e["date"],
            "labels": e["labels"],
        })
    out.write_text(json.dumps(clean, ensure_ascii=False, indent=2))
    print(f"\n💾 Metadata exportada: {out}")


if __name__ == "__main__":
    main()
