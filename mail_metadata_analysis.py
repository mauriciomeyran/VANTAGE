#!/usr/bin/env python3
"""
VANTAGE Mail Metadata Analysis
Volcado completo de metadata de ~1669 correos + análisis de patrones.
NO toca contenido ni realiza mutations. Solo lectura.
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

# Credenciales del config de himalaya (misma cuenta que L3)
GMAIL_USER = "mauricio.meyran@gmail.com"
GMAIL_APP_PASS = "rmgsxlojhbsvlxde"


def login():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASS)
    print(f"✅ Conectado como {GMAIL_USER}")
    return mail


def decode_mime(s):
    """Decodifica un string MIME codificado (ej. =?UTF-8?B?...?=)."""
    if not s:
        return ""
    try:
        parts = decode_header(s)
        decoded = []
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                decoded.append(str(part))
        return "".join(decoded)
    except Exception:
        return s


def get_labels(mail, msg_id):
    """Obtiene los labels de un mensaje usando X-GM-LABELS (Gmail extension)."""
    try:
        typ, data = mail.xgmlabels(msg_id)
        if typ == "OK" and data and data[0]:
            return [label.decode("utf-8") if isinstance(label, bytes) else label
                    for label in data[0].split()]
    except Exception:
        pass
    return []


def _first_email_address(addr_spec: str) -> str:
    """Extrae el email más limpio de un header From/Rfc822.Address."""
    if not addr_spec:
        return ""
    # Formato: "Name <email@domain>" o solo "email@domain" o "Name <>"
    m = re.search(r"<([^>]+@[^>]+)>", addr_spec)
    if m:
        return m.group(1)
    # fallback: última palabra que parece email
    parts = addr_spec.replace("(", " ").replace(")", " ").split()
    for p in reversed(parts):
        if "@" in p:
            return p.strip("<>")
    return addr_spec.strip().strip("<>")


def _parse_envelope_date(date_str: str):
    """Parsea un header Date de email a datetime con tz."""
    if not date_str:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            import time as _time
            t = _time.mktime(_time.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z"))
            return datetime.fromtimestamp(t, tz=timezone.utc)
        except Exception:
            return None


def fetch_all_metadata(mail, mailbox="[Gmail]/All Mail"):
    """Fetch all messages from a mailbox with metadata."""
    mailbox_quoted = f'"{mailbox}"'
    print(f"📬 Seleccionando mailbox: {mailbox}...")
    typ, data = mail.select(mailbox_quoted)
    if typ != "OK":
        print(f"❌ No se pudo seleccionar {mailbox}: {data}")
        return []

    print(f"🔍 Buscando todos los mensajes...")
    typ, data = mail.search(None, "ALL")
    if typ != "OK":
        print(f"❌ Error buscando mensajes: {data}")
        return []

    email_ids = data[0].split()
    total = len(email_ids)
    print(f"📦 Encontrados {total} mensajes en {mailbox}")

    if total == 0:
        return []

    messages = []
    batch_size = 50  # Fetch in batches to avoid timeouts

    for i in range(0, total, batch_size):
        batch_ids = email_ids[i:i+batch_size]
        batch_str = b",".join(batch_ids)

        print(f"  ⏳ Procesando {i+1}-{min(i+batch_size, total)}/{total}...")

        typ, data = mail.fetch(batch_str, "(RFC822 X-GM-LABELS)")
        if typ != "OK":
            print(f"  ⚠️  Error en batch: {data}")
            continue

        for msg_data in data:
            if not msg_data or not msg_data[0]:
                continue

            raw = msg_data[0]
            # Puede venir como (id, bytes) o solo bytes
            if isinstance(raw, tuple):
                raw = raw[1]
            if not raw or not isinstance(raw, (bytes, bytearray)):
                continue

            try:
                msg = email.message_from_bytes(raw)

                # Headers
                from_header = msg.get("From", "")
                subject = decode_mime(msg.get("Subject") or "")
                date_str = msg.get("Date", "")
                msg_id = msg.get("Message-ID", "")

                from_email = _first_email_address(from_header)

                # Fecha
                dt = _parse_envelope_date(date_str)

                # Labels (X-GM-LABELS) — fetch aparte, pero intentamos parsear
                # del mismo RFC822 si está presente (raro); sino, vacío
                labels = []

                messages.append({
                    "id": msg_id,
                    "date": dt.isoformat() if dt else None,
                    "from_email": from_email,
                    "subject": subject,
                    "labels": labels,
                    "date_dt": dt,  # para análisis interno, no exportar
                })
            except Exception as e:
                pass

    # Segunda pasada: obtención de labels X-GM-LABELS por batch (más lento,
    # pero necesario porque X-GM-LABELS no viene en RFC822)
    print("\n🏷️  Obteniendo labels (X-GM-LABELS) por batch...")
    typ, data = mail.select(mailbox)
    email_ids = [m["id"] for m in messages if m["id"]]
    for i in range(0, len(email_ids), batch_size):
        batch_ids = email_ids[i:i+batch_size]
        batch_str = b",".join(batch_ids)
        try:
            typ, lbl_data = mail.xgmlabels(batch_str)
            if typ == "OK" and lbl_data:
                # lbl_data es una lista de (msg_id_bytes, labels_bytes) por mensaje
                for entry in lbl_data:
                    if isinstance(entry, tuple) and len(entry) >= 2:
                        mid = entry[0].decode("utf-8", errors="replace")
                        lbls_raw = entry[1]
                        if isinstance(lbls_raw, bytes):
                            lbls = [l.decode("utf-8", errors="replace")
                                    for l in lbls_raw.split()]
                        else:
                            lbls = [str(lbls_raw)]
                        for m in messages:
                            if m["id"] == mid:
                                m["labels"] = lbls
                                break
        except Exception as e:
            print(f"  ⚠️  Batch de labels {i//batch_size + 1}: {e}")
        if i % 500 == 0 and i > 0:
            print(f"    → {i}/{len(email_ids)} labels resueltos")

    # Limpiar campo interno
    for m in messages:
        m.pop("date_dt", None)

    return messages


def extract_domain(email_addr):
    """Extrae el dominio del email."""
    if "@" in email_addr:
        return email_addr.split("@")[1].lower()
    return ""


def extract_sender_clean(from_email):
    """Extrae un nombre de remitente limpio para agrupar."""
    if "@" in from_email:
        local = from_email.split("@")[0]
        # Quita cosas como "no-reply", "noreply", "trabajos_mx", etc.
        local_clean = re.sub(r"[\\._-]", " ", local)
        return local_clean.lower()
    return from_email.lower()


def cluster_senders(messages):
    """Agrupa remitentes por patrón."""
    sender_groups = defaultdict(list)

    for msg in messages:
        from_email = msg["from_email"]
        domain = extract_domain(from_email)
        sender_clean = extract_sender_clean(from_email)
        subject = msg["subject"]

        # Detectar patrones de remitente
        if "noreply" in from_email.lower() or "no-reply" in from_email.lower():
            group = f"no-reply@{domain}"
        elif "notifications" in from_email.lower():
            group = f"notifications@{domain}"
        elif "trabajos" in from_email.lower() or "computrabajo" in domain:
            group = "computrabajo"
        elif "linkedin" in domain:
            group = "linkedin"
        elif "indeed" in domain:
            group = "indeed"
        elif "bumeran" in domain:
            group = "bumeran"
        elif "occ" in domain:
            group = "occ"
        elif "github" in domain:
            group = "github"
        elif "google" in domain:
            group = "google"
        elif "amazon" in domain:
            group = "amazon"
        elif "apple" in domain:
            group = "apple"
        elif "mailchimp" in domain or "sendgrid" in domain or "amazonses" in domain:
            # Email service provider - extract real sender from name
            group = f"esp-{domain}"
        elif "newsletter" in from_email.lower():
            group = f"newsletter-{domain}"
        else:
            # Usar el nombre de remitente
            group = f"{sender_clean}@{domain}"

        sender_groups[group].append(msg)

    return sender_groups


def cluster_subjects(messages):
    """Agrupa por patrones de asunto."""
    subject_patterns = defaultdict(list)

    # Patrones de asunto
    patterns = {
        "job_alert_new_offers": re.compile(r"nuevas?\s+(ofertas?|oportunidades?|vacantes?)", re.I),
        "job_alert_offers": re.compile(r"(ofertas?|vacantes?)\s+(de|en|para)", re.I),
        "job_alert_matching": re.compile(r"(coinciden|encuentras?|destacadas?|relevantes?)", re.I),
        "job_confirmation": re.compile(r"(confirmaci[oó]n|registro|verificaci[oó]n|bienvenid)", re.I),
        "job_reminder": re.compile(r"(recordatorio|alerta|aviso)", re.I),
        "job_digest": re.compile(r"(resumen|bulletein|newsletter|digest)", re.I),
        "job_actions": re.compile(r"(aplica|postula|inscribi|completa|finaliza)", re.I),
        "welcome_onboarding": re.compile(r"(bienvenido|welcome|te damos la bienvenida)", re.I),
        "verification": re.compile(r"(verifica|confirm|validate|activate)", re.I),
        "password_reset": re.compile(r"(contrase.?a|password|reset|restablecer)", re.I),
        "security_alert": re.compile(r"(security|seguridad|alert|alerta|suspicious)", re.I),
        "invoice_payment": re.compile(r"(factura|invoice|cargo|payment|pedido|pedidos)", re.I),
        "receipt": re.compile(r"(recibo|gift|compra|order|pedido)", re.I),
        "notification_social": re.compile(r"(likes?|comments?|shares?|followers?|new.*message|new.*connection)", re.I),
        "notification_tech": re.compile(r"(deploy|build|push|commit|pull.*request|pr|issues?|pipeline)", re.I),
        "notification_opt": re.compile(r"(opt.*in|subscribe|unsubscribe|suscr|baja|baja)", re.I),
        "job_tips": re.compile(r"(consejos?|tips?|gu[ií]a|recurso|aprende|mejora|impulsa)", re.I),
    }

    for msg in messages:
        subject = msg["subject"]
        matched = False
        for pattern_name, pattern in patterns.items():
            if pattern.search(subject):
                subject_patterns[pattern_name].append(msg)
                matched = True
                break
        if not matched:
            subject_patterns["other"].append(msg)

    return subject_patterns


def cluster_by_label(messages):
    """Agrupa mensajes por label."""
    label_groups = defaultdict(list)

    for msg in messages:
        labels = msg["labels"]
        if not labels:
            label_groups["(sin label)"] = msg
        else:
            for label in labels:
                label_groups[label].append(msg)

    return label_groups


def analyze_domains(messages):
    """Análisis de dominios de remitentes."""
    domain_counter = Counter()
    no_reply_domains = set()
    notification_domains = set()

    for msg in messages:
        from_email = msg["from_email"]
        domain = extract_domain(from_email)
        if domain:
            domain_counter[domain] += 1
            if "noreply" in from_email.lower() or "no-reply" in from_email.lower():
                no_reply_domains.add(domain)
            if "notification" in from_email.lower():
                notification_domains.add(domain)

    return domain_counter, no_reply_domains, notification_domains


def analyze_date_distribution(messages):
    """Analiza la distribución por fecha."""
    now = datetime.now(timezone.utc)
    six_months_ago = now.replace(month=now.month - 6 if now.month > 6 else now.month + 6,
                                   year=now.year - 1 if now.month <= 6 else now.year)

    by_period = defaultdict(list)
    for msg in messages:
        dt_str = msg["date"]
        if not dt_str:
            by_period["sin_fecha"].append(msg)
            continue

        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            by_period["sin_fecha"].append(msg)
            continue

        # Agrupar por mes
        month_key = dt.strftime("%Y-%m")
        by_period[month_key].append(msg)

        # S AUDITORÍA por antigüedad
        if dt < six_months_ago:
            by_period[">6meses"].append(msg)
        elif dt < now.replace(month=now.month - 3 if now.month > 3 else now.month + 9,
                               year=now.year - 1 if now.month <= 3 else now.year):
            by_period["3-6meses"].append(msg)
        elif dt < now.replace(day=1):
            by_period["mes_actual"].append(msg)
        else:
            by_period["ultimas_2semanas"].append(msg)

    return dict(by_period)


def analyze_label_presence(messages):
    """Analiza qué labels aparecen y con qué frecuencia."""
    label_counter = Counter()
    messages_with_labels = 0

    for msg in messages:
        labels = msg["labels"]
        if labels:
            messages_with_labels += 1
        for label in labels:
            label_counter[label] += 1

    return label_counter, messages_with_labels


def print_analysis(messages, sender_groups, subject_patterns, label_groups,
                   domain_counter, no_reply_domains, notification_domains,
                   date_dist, label_counter, messages_with_labels):
    """Imprime el análisis completo."""
    total = len(messages)
    print("\n" + "="*70)
    print("ANÁLISIS DE CORREOS — MAURICIO MEYRÁN")
    print("="*70)
    print(f"\nTotal de correos analizados: {total}")

    # 1. Analytics por label
    print("\n" + "-"*70)
    print("1. DISTRIBUCIÓN POR LABELS")
    print("-"*70)
    print(f"Mensajes con al menos un label: {messages_with_labels} ({100*messages_with_labels/total:.1f}%)")
    print(f"Mensajes sin label: {total - messages_with_labels} ({100*(total-messages_with_labels)/total:.1f}%)")

    print("\nTop 20 labels por frecuencia:")
    for label, count in label_counter.most_common(20):
        pct = 100 * count / total
        print(f"  {label:<30} {count:>5} ({pct:>5.1f}%)")

    # 2. Analytics por dominio
    print("\n" + "-"*70)
    print("2. TOP 25 DOMINIOS DE REMITENTE")
    print("-"*70)
    for domain, count in domain_counter.most_common(25):
        pct = 100 * count / total
        mark = ""
        if domain in no_reply_domains:
            mark = " [no-reply]"
        if domain in notification_domains:
            mark += " [notifications]"
        print(f"  {domain:<35} {count:>5} ({pct:>5.1f}%){mark}")

    # 3. Cluster de remitentes (patrones detectados)
    print("\n" + "-"*70)
    print("3. CLUSTERS DE REMITENTES (patrones detectados)")
    print("-"*70)
    for group, msgs in sorted(sender_groups.items(), key=lambda x: -len(x[1]))[:25]:
        domains = set(extract_domain(m["from_email"]) for m in msgs)
        subjects = list(set(m["subject"][:60] for m in msgs[:5]))
        print(f"\n  [{len(msgs):>4} msgs] {group}")
        print(f"    Dominios: {', '.join(domains)}")
        print(f"    Muestras de asuntos:")
        for s in subjects:
            print(f"      - {s}")

    # 4. Patrones de asunto
    print("\n" + "-"*70)
    print("4. PATRONES DE ASUNTO (clusters temáticos)")
    print("-"*70)
    for pattern_name, msgs in sorted(subject_patterns.items(), key=lambda x: -len(x[1])):
        if pattern_name == "other":
            continue
        samples = list(set(m["subject"][:80] for m in msgs[:3]))
        print(f"\n  [{len(msgs):>4} msgs] {pattern_name}")
        for s in samples:
            print(f"    - {s}")

    # 5. Distribución temporal
    print("\n" + "-"*70)
    print("5. DISTRIBUCIÓN TEMPORAL (por mes)")
    print("-"*70)
    for period in sorted(date_dist.keys()):
        count = len(date_dist[period])
        if count == 0:
            continue
        pct = 100 * count / total
        print(f"  {period:<12} {count:>5} msgs ({pct:>5.1f}%)")

    # 6. Notificaciones y newsletters (borrador de reglas)
    print("\n" + "-"*70)
    print("6. BORRADOR DE REGLAS PARA FILTRADO/LABELING PROPUESTO")
    print("-"*70)

    # Jobs (mantener como insumo VANTAGE)
    jobs_count = len(label_groups.get(".Jobs", []))
    print(f"\n  🏷️  .Jobs: {jobs_count} correos (RESERVADO — insumo L3 VANTAGE, NO borrar)")
    print(f"      → Sugerencia: mantener label .Jobs intacto; el pipeline L3 lo procesa.")

    # Finance
    finance_count = len(label_groups.get(".Finance", []))
    print(f"\n  🏷️  .Finance: {finance_count} correos")
    print(f"      → Sugerencia: evaluar cuáles merecen atención vs archivo.")

    # Notificaciones digitales genéricas (sin label)
    unlabeled_count = total - messages_with_labels
    print(f"\n  📧 Sin label: {unlabeled_count} correos")
    print(f"      → Sugerencia: revisar manualmente las últimas 2 semanas.")

    # Newsletters potenciales
    newsletter_domains = {d for d, c in domain_counter.items()
                          if any(kw in d.lower() for kw in ["newsletter", "mailchimp", "sendgrid", "mail", "list"])}
    newsletter_count = sum(domain_counter[d] for d in newsletter_domains if d in domain_counter)
    print(f"\n  📋 Newsletters potenciales (por dominio): {len(newsletter_domains)} dominios, ~{newsletter_count} msgs")
    for d in sorted(newsletter_domains):
        print(f"      - {d}: {domain_counter[d]} msgs")

    # Job alerts masivos
    job_alert_senders = [g for g in sender_groups if any(kw in g.lower()
                        for kw in ["computrabajo", "indeed", "linkedin", "bumeran", "occ", "job", "trabajo"])]
    job_alert_count = sum(len(sender_groups[g]) for g in job_alert_senders)
    print(f"\n  💼 Job notifications (no .Jobs): {job_alert_count} correos en {len(job_alert_senders)} clusters")
    for g in sorted(job_alert_senders, key=lambda x: -len(sender_groups[x])):
        print(f"      - {g}: {len(sender_groups[g])} msgs")

    # Google, GitHub, etc.
    platform_senders = [g for g in sender_groups if any(kw in g.lower()
                     for kw in ["google", "github", "apple", "amazon", "microsoft"])]
    platform_count = sum(len(sender_groups[g]) for g in platform_senders)
    print(f"\n  🔍 Notificaciones de plataformas (Google, GitHub, etc.): {platform_count} msgs")
    for g in sorted(platform_senders, key=lambda x: -len(sender_groups[x])):
        print(f"      - {g}: {len(sender_groups[g])} msgs")

    print("\n" + "="*70)
    print("END OF ANALYSIS")
    print("="*70)


def main():
    mail = login()
    try:
        messages = fetch_all_metadata(mail, "[Gmail]/All Mail")
    finally:
        mail.logout()

    if not messages:
        print("❌ No se obtuvieron mensajes. Revisa credenciales.")
        sys.exit(1)

    print(f"\n📊 Analizando {len(messages)} mensajes...")

    # Clusters
    sender_groups = cluster_senders(messages)
    subject_patterns = cluster_subjects(messages)
    label_groups = cluster_by_label(messages)
    domain_counter, no_reply_domains, notification_domains = analyze_domains(messages)
    date_dist = analyze_date_distribution(messages)
    label_counter, messages_with_labels = analyze_label_presence(messages)

    # Imprimir análisis
    print_analysis(messages, sender_groups, subject_patterns, label_groups,
                   domain_counter, no_reply_domains, notification_domains,
                   date_dist, label_counter, messages_with_labels)

    # Exportar metadata cruda para análisis adicional
    export_path = Path.home() / "mail_metadata_export.json"
    with open(export_path, "w") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Metadata exportada a: {export_path}")


if __name__ == "__main__":
    main()
