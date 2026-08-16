#!/usr/bin/env python3
"""
VANTAGE L3 - Reset Recent Emails
Marca los últimos N emails del label .Jobs como no leídos para reprocesar con fixes
"""

import imaplib
import email
from email.header import decode_header
from pathlib import Path
from dotenv import load_dotenv

# ──────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────
_LAYER_3_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_3_ROOT / "config" / "layer_3.env", override=True)

GMAIL_USER     = os.environ["GMAIL_USER"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
GMAIL_LABEL    = os.environ.get("GMAIL_LABEL", ".Jobs")
RECENT_COUNT   = 20  # Cantidad de emails a marcar como no leídos

def _connect_gmail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASS)
    mail.select(f'"{GMAIL_LABEL}"')
    return mail

def _set_seen(mail, eid, seen: bool):
    flag = "+FLAGS" if seen else "-FLAGS"
    mail.store(eid, flag, "\\Seen")

def _decode_subject(msg):
    raw_subject = decode_header(msg.get("Subject") or "")[0]
    try:
        if isinstance(raw_subject[0], bytes):
            return raw_subject[0].decode(raw_subject[1] or "utf-8")
        return raw_subject[0] or ""
    except (LookupError, UnicodeDecodeError, IndexError):
        if isinstance(raw_subject[0], bytes):
            return raw_subject[0].decode("utf-8", errors="replace")
        return str(raw_subject[0]) if raw_element else ""

def main():
    print(f"🔄 Reset L3 - Marcando últimos {RECENT_COUNT} emails como no leídos...")
    print(f"Label: {GMAIL_LABEL}")
    
    mail = _connect_gmail()
    
    # Buscar todos los emails no leídos
    _, data = mail.search(None, "UNSEEN")
    email_ids = data[0].split()
    
    if not email_ids:
        print("✅ No hay emails no leídos en .Jobs")
        mail.logout()
        return
    
    total_unseen = len(email_ids)
    print(f"📨 Emails no leídos encontrados: {total_unseen}")
    
    # Si hay más que RECENT_COUNT, tomar los más recientes (últimos de la lista)
    if total_unseen > RECENT_COUNT:
        emails_to_reset = email_ids[-RECENT_COUNT:]  # Los últimos N
        print(f"⚠️  Resetando últimos {RECENT_COUNT} de {total_unseen} emails no leídos")
    else:
        emails_to_reset = email_ids
        print(f"ℹ️  Resetando todos los {total_unseen} emails no leídos")
    
    print("\nProcesando emails:")
    reset_count = 0
    
    for eid in emails_to_reset:
        try:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = _decode_subject(msg)
            sender = msg.get("From", "")
            
            # Marcar como no leído
            _set_seen(mail, eid, False)
            reset_count += 1
            
            print(f"  ✅ Marcado como no leído: {subject[:50]}... ({sender[:30]})")
            
        except Exception as e:
            print(f"  ❌ Error procesando email {eid}: {e}")
    
    mail.logout()
    
    print(f"\n{'─'*40}")
    print(f"✅ Completado: {reset_count} emails marcados como no leídos")
    print(f"📌 Próximo paso: Ejecutar layer_3_mail.py para reprocesar estos emails")
    print(f"{'─'*40}")

if __name__ == "__main__":
    import os
    main()
