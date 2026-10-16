#!/usr/bin/env python3
"""
iCloud Mail Organizer Script
Organizes iCloud mail by moving messages to folders based on sender/subject.
Uses IMAP to connect to iCloud mail.
"""

import imaplib
import email
from email.header import decode_header
import getpass
import re
from typing import List, Dict, Tuple

# iCloud IMAP settings
IMAP_SERVER = 'imap.mail.me.com'
IMAP_PORT = 993

# Folders to create (similar to Gmail labels)
FOLDERS = [
    'Jobs',
    'Finance',
    'Social',
    'Alert',
    'Services',
    'Promos'
]

# Search criteria for each folder (IMAP SEARCH syntax)
# Note: IMAP search is more limited than Gmail queries
FOLDER_RULES = {
    'Jobs': {
        'from_domains': [
            'computrabajo.com', 'indeed.com', 'occ.com.mx', 'talenteca.com',
            'bumeran.com', 'teamtailor-mail.com', 'jobs2web.com', 'myworkday.com',
            'successfactors.com', 'greenhouse.io', 'lever.co', 'icims.com',
            'smartrecruiters.com', 'workable.com', 'grupoaxo.com', 'jobscan.co',
            'zippia.com', 'infojobs.com.mx', 'payroll.com', 'notch.io'
        ],
        'from_emails': [
            'jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com',
            'jobs-listings@linkedin.com', 'inmail-hit-reply@linkedin.com'
        ],
        'subject_keywords': ['visual merchandising', 'empleo', 'vacante', 'recruitment']
    },
    'Finance': {
        'from_domains': [
            'heybanco.com', 'hey.inc', 'conecta.hey.inc', 'santander.com.mx',
            'mercadopago.com', 'invex.com', 'paypal.com', 'wise.com',
            'stripe.com', 'gbm.com', 'masari.com.mx', 'aktywum.com.mx'
        ]
    },
    'Social': {
        'from_domains': [
            'linkedin.com', 'instagram.com', 'twitter.com', 'threads.net', 'telegram.org'
        ],
        'exclude_from_emails': [
            'jobs-noreply@linkedin.com', 'jobalerts-noreply@linkedin.com',
            'jobs-listings@linkedin.com', 'inmail-hit-reply@linkedin.com',
            'instagram-noreply@instagram.com'
        ],
        'exclude_subject_keywords': ['visual merchandising', 'empleo', 'vacante', 'recruitment']
    },
    'Alert': {
        'from_domains': [
            'accounts.google.com', 'google.com', 'facebookmail.com', 'meta.com',
            'openai.com', 'github.com', 'cursor.com', 'qodo.ai', 'you.com',
            'perplexity.ai', 'openrouter.ai', 'reclaim.ai', 'clickup.com',
            'figma.com', 'samsung-mail.com', 'notion.com', 'slack.com',
            'zapier.com', 'make.com'
        ]
    },
    'Services': {
        'from_domains': [
            'cfe.mx', 'gympass.com', 'telcel.com', 'att.com.mx', 'infinitum.com.mx'
        ]
    },
    'Promos': {
        'from_domains': [
            'prixz.com', 'adidas.com', 'dominosmx.com', 'didiglobal.com',
            'promocinepolis.com', 'farmaciasguadalajara.com', 'clicks.tech',
            'amazon.com.mx', 'price.com', 'coca-cola.com', 'ipsosisay.com',
            'rankia.com', 'kajabimail.net', 'costco.com.mx', 'walmart.com.mx',
            'liverpool.com.mx', 'zara.com', 'hm.com', 'urbanoutfitters.com'
        ]
    }
}


def decode_imap_header(header_value):
    """Decode IMAP header value."""
    if not header_value:
        return ""
    
    decoded_parts = []
    for part, encoding in decode_header(header_value):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            except:
                decoded_parts.append(part.decode('utf-8', errors='ignore'))
        else:
            decoded_parts.append(str(part))
    
    return ''.join(decoded_parts)


def connect_to_icloud(apple_id: str, app_password: str) -> imaplib.IMAP4_SSL:
    """Connect to iCloud IMAP server."""
    print(f"Connecting to iCloud IMAP server...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    
    try:
        mail.login(apple_id, app_password)
        print("Successfully authenticated with iCloud")
        return mail
    except imaplib.IMAP4.error as e:
        print(f"Authentication failed: {e}")
        print("\nNote: You need to use an App-Specific Password for iCloud.")
        print("Generate one at: https://appleid.apple.com/account/manage")
        raise


def create_folder(mail: imaplib.IMAP4_SSL, folder_name: str) -> bool:
    """Create a folder if it doesn't exist."""
    try:
        # Check if folder exists
        mail.select('INBOX')
        status, folders = mail.list()
        
        folder_exists = False
        for response in folders:
            if isinstance(response, bytes):
                response = response.decode('utf-8')
            if isinstance(response, list):
                response = ' '.join(response).decode('utf-8')
            
            if folder_name in response:
                folder_exists = True
                break
        
        if folder_exists:
            print(f"  Folder '{folder_name}' already exists")
            return True
        
        # Create folder
        mail.create(folder_name)
        print(f"  Created folder '{folder_name}'")
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"  Error creating folder '{folder_name}': {e}")
        return False


def setup_folders(mail: imaplib.IMAP4_SSL) -> Dict[str, str]:
    """Create all required folders."""
    print("\n=== Setting up folders ===")
    created_folders = {}
    
    for folder_name in FOLDERS:
        if create_folder(mail, folder_name):
            created_folders[folder_name] = folder_name
    
    return created_folders


def build_search_query(rule: Dict) -> str:
    """Build IMAP SEARCH query from rule definition."""
    criteria = []
    
    # FROM domains
    if 'from_domains' in rule['from_domains']:
        domains = rule['from_domains']
        if len(domains) == 1:
            criteria.append(f'FROM "{domains[0]}"')
        else:
            # IMAP doesn't support OR for multiple domains efficiently
            # We'll search one at a time
            pass
    
    # FROM specific emails
    if 'from_emails' in rule:
        for email_addr in rule['from_emails']:
            criteria.append(f'FROM "{email_addr}"')
    
    # SUBJECT keywords
    if 'subject_keywords' in rule:
        for keyword in rule['subject_keywords']:
            criteria.append(f'SUBJECT "{keyword}"')
    
    return criteria


def search_messages(mail: imaplib.IMAP4_SSL, folder: str, criteria: List[str]) -> List[str]:
    """Search for messages matching criteria."""
    mail.select(folder)
    message_ids = []
    
    for criterion in criteria:
        try:
            status, messages = mail.search(None, criterion)
            if status == 'OK':
                for msg_id in messages[0].split():
                    if msg_id not in message_ids:
                        message_ids.append(msg_id)
        except imaplib.IMAP4.error as e:
            print(f"  Search error for '{criterion}': {e}")
    
    return message_ids


def get_message_headers(mail: imaplib.IMAP4_SSL, msg_id: str) -> Dict:
    """Get message headers for filtering."""
    try:
        status, msg_data = mail.fetch(msg_id, '(RFC822.HEADER)')
        if status != 'OK':
            return None
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                return {
                    'from': decode_imap_header(msg.get('From', '')),
                    'subject': decode_imap_header(msg.get('Subject', '')),
                    'to': decode_imap_header(msg.get('To', '')),
                    'cc': decode_imap_header(msg.get('Cc', ''))
                }
    except Exception as e:
        print(f"  Error fetching headers for message {msg_id}: {e}")
    
    return None


def matches_rule(headers: Dict, rule: Dict) -> bool:
    """Check if message headers match the rule."""
    if not headers:
        return False
    
    from_lower = headers['from'].lower()
    subject_lower = headers['subject'].lower()
    
    # Check exclusions first
    if 'exclude_from_emails' in rule:
        for email_addr in rule['exclude_from_emails']:
            if email_addr.lower() in from_lower:
                return False
    
    if 'exclude_subject_keywords' in rule:
        for keyword in rule['exclude_subject_keywords']:
            if keyword.lower() in subject_lower:
                return False
    
    # Check inclusions
    if 'from_domains' in rule:
        for domain in rule['from_domains']:
            if domain.lower() in from_lower:
                return True
    
    if 'from_emails' in rule:
        for email_addr in rule['from_emails']:
            if email_addr.lower() in from_lower:
                return True
    
    if 'subject_keywords' in rule:
        for keyword in rule['subject_keywords']:
            if keyword.lower() in subject_lower:
                return True
    
    return False


def move_messages(mail: imaplib.IMAP4_SSL, msg_ids: List[str], target_folder: str) -> int:
    """Move messages to target folder."""
    if not msg_ids:
        return 0
    
    moved_count = 0
    for msg_id in msg_ids:
        try:
            # Copy to target folder
            mail.copy(msg_id, target_folder)
            # Mark as deleted in current folder
            mail.store(msg_id, '+FLAGS', '\\Deleted')
            moved_count += 1
        except imaplib.IMAP4.error as e:
            print(f"  Error moving message {msg_id}: {e}")
    
    # Expunge to actually delete messages from source
    try:
        mail.expunge()
    except imaplib.IMAP4.error as e:
        print(f"  Error expunging: {e}")
    
    return moved_count


def organize_mail(mail: imaplib.IMAP4_SSL, folders: Dict[str, str]):
    """Organize mail by moving messages to appropriate folders."""
    print("\n=== Organizing mail ===")
    total_moved = 0
    
    # Select INBOX
    mail.select('INBOX')
    
    # Get all message IDs in INBOX
    status, messages = mail.search(None, 'ALL')
    if status != 'OK':
        print("  Error getting messages from INBOX")
        return
    
    msg_ids = messages[0].split()
    print(f"  Found {len(msg_ids)} messages in INBOX")
    
    # Process each message
    processed_count = 0
    for msg_id in msg_ids:
        headers = get_message_headers(mail, msg_id)
        if not headers:
            continue
        
        # Check each rule
        for folder_name, rule in FOLDER_RULES.items():
            if matches_rule(headers, rule):
                target_folder = folders.get(folder_name)
                if target_folder:
                    try:
                        mail.copy(msg_id, target_folder)
                        mail.store(msg_id, '+FLAGS', '\\Deleted')
                        total_moved += 1
                        print(f"  Moved message to {folder_name}: {headers['subject'][:50]}...")
                        break  # Only move to first matching folder
                    except imaplib.IMAP4.error as e:
                        print(f"  Error moving message: {e}")
        
        processed_count += 1
        if processed_count % 100 == 0:
            print(f"  Processed {processed_count}/{len(msg_ids)} messages...")
    
    # Expunge to finalize moves
    try:
        mail.expunge()
    except imaplib.IMAP4.error as e:
        print(f"  Error expunging: {e}")
    
    print(f"\nTotal messages moved: {total_moved}")


def main():
    """Main execution function."""
    print("iCloud Mail Organizer")
    print("=" * 50)
    
    # Get credentials
    apple_id = input("Enter your Apple ID (email): ").strip()
    app_password = getpass.getpass("Enter your iCloud App-Specific Password: ")
    
    try:
        mail = connect_to_icloud(apple_id, app_password)
        
        folders = setup_folders(mail)
        print(f"\nFolders configured: {len(folders)}/{len(FOLDERS)}")
        
        organize_mail(mail, folders)
        
        mail.logout()
        
        print("\n" + "=" * 50)
        print("Organization completed!")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
