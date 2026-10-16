#!/usr/bin/env python3
"""
Gmail Filters Setup Script
Automatically creates labels and filters for Gmail, and applies them retroactively.
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels', 'https://www.googleapis.com/auth/gmail.settings.basic']

# Labels to create
LABELS = [
    '.Jobs',
    '.finance',
    '.Social',
    '.Alert',
    '.Services',
    '.Promos'
]

# Filter definitions
FILTERS = [
    {
        'name': '.Jobs',
        'query': 'from:(computrabajo.com OR indeed.com OR occ.com.mx OR talenteca.com OR bumeran.com OR teamtailor-mail.com OR jobs2web.com OR myworkday.com OR successfactors.com OR greenhouse.io OR lever.co OR icims.com OR smartrecruiters.com OR workable.com OR grupoaxo.com OR jobscan.co OR zippia.com OR infojobs.com.mx OR payroll.com OR notch.io OR jobs-noreply@linkedin.com OR jobalerts-noreply@linkedin.com OR jobs-listings@linkedin.com OR inmail-hit-reply@linkedin.com) OR (from:linkedin.com (subject:"visual merchandising" OR subject:empleo OR subject:vacante OR subject:recruitment)) OR (from:notify-noreply@google.com subject:(vacante OR empleo OR job OR careers) -(subject:"Security alert" OR subject:"You shared some Google Account data" OR subject:Premium OR subject:Ads OR subject:"profile view" OR subject:connection OR subject:invite)) OR (subject:("visual merchandising" OR "retail merchandising") (from:recruiting OR from:recruiter OR from:headhunter OR from:talent))',
        'label': '.Jobs',
        'skip_inbox': False,
        'category': 'UPDATES'
    },
    {
        'name': '.finance',
        'query': 'from:(heybanco.com OR hey.inc OR conecta.hey.inc OR envio.santander.com.mx OR envios.santander.com.mx OR notificaciones.santander.com.mx OR notificacion@operaciones.santander.com.mx OR mercadopago.com OR mercadopago.com.mx OR invex.com OR paypal.com OR paypalmail.com OR wise.com OR stripe.com OR gbm.com OR masari.com.mx OR aktywum.com.mx)',
        'label': '.finance',
        'skip_inbox': True,
        'category': 'PERSONAL'
    },
    {
        'name': '.Social',
        'query': 'from:(linkedin.com OR instagram.com OR twitter.com OR threads.net OR telegram.org) -(from:jobs-noreply@linkedin.com OR from:jobalerts-noreply@linkedin.com OR from:jobs-listings@linkedin.com OR from:inmail-hit-reply@linkedin.com OR from:instagram-noreply@instagram.com) -(subject:"visual merchandising" OR subject:empleo OR subject:vacante OR subject:recruitment)',
        'label': '.Social',
        'skip_inbox': False,
        'category': 'SOCIAL'
    },
    {
        'name': '.Alert',
        'query': 'from:(accounts.google.com OR no-reply@google.com OR noreply-location-sharing@google.com OR workspace-noreply@google.com OR googledev-noreply@google.com OR facebookmail.com OR account.meta.com OR openai.com OR github.com OR mail.cursor.com OR qodo.ai OR mail.you.com OR perplexity.ai OR openrouter.ai OR reclaim.ai OR clickup.com OR figma.com OR samsung-mail.com OR noreply@notion.com OR noreply@slack.com OR notifications@slack.com OR zapier.com OR make.com) OR (from:notify-noreply@google.com subject:("Security alert" OR "You shared some Google Account data"))',
        'label': '.Alert',
        'skip_inbox': True,
        'category': 'UPDATES'
    },
    {
        'name': '.Services',
        'query': 'from:(cfe.mx OR gympass.com OR telcel.com OR att.com.mx OR infinitum.com.mx)',
        'label': '.Services',
        'skip_inbox': False,
        'category': 'UPDATES'
    },
    {
        'name': '.Promos',
        'query': 'from:(prixz.com OR mx-news.adidas.com OR dominosmx.com OR mkt-mx.didiglobal.com OR promocinepolis.com OR farmaciasguadalajara.com OR clicks.tech OR noreply@amazon.com.mx OR no-reply@price.com OR latinamerica.coca-cola.com OR ipsosisay.com OR rankia.com OR kajabimail.net OR promociones.costco.com.mx OR walmart.com.mx OR liverpool.com.mx OR zara.com OR hm.com OR urbanoutfitters.com)',
        'label': '.Promos',
        'skip_inbox': False,
        'category': 'PROMOTIONS'
    }
]


def authenticate():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    token_path = Path('token.json')
    credentials_path = Path('credentials.json')

    if not credentials_path.exists():
        raise FileNotFoundError(
            "credentials.json not found. Please download it from Google Cloud Console "
            "and place it in the current directory."
        )

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with token_path.open('w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def get_label_id(service, label_name):
    """Get the label ID for a given label name."""
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        for label in labels:
            if label['name'] == label_name:
                return label['id']
    except HttpError as error:
        print(f'Error listing labels: {error}')
    
    return None


def create_label(service, label_name):
    """Create a new label if it doesn't exist."""
    label_id = get_label_id(service, label_name)
    
    if label_id:
        print(f"  Label '{label_name}' already exists (ID: {label_id})")
        return label_id
    
    try:
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        result = service.users().labels().create(
            userId='me',
            body=label_body
        ).execute()
        print(f"  Created label '{label_name}' (ID: {result['id']})")
        return result['id']
    except HttpError as error:
        print(f"  Error creating label '{label_name}': {error}")
        return None


def setup_labels(service):
    """Create all required labels."""
    print("\n=== Setting up labels ===")
    label_ids = {}
    
    for label_name in LABELS:
        label_id = create_label(service, label_name)
        if label_id:
            label_ids[label_name] = label_id
    
    return label_ids


def filter_exists(service, query):
    """Check if a filter with the given query already exists and return its ID."""
    try:
        results = service.users().settings().filters().list(userId='me').execute()
        filters = results.get('filter', [])
        
        for existing_filter in filters:
            if existing_filter.get('criteria', {}).get('query') == query:
                return existing_filter.get('id')
    except HttpError as error:
        print(f"  Error checking existing filters: {error}")
    
    return None


def delete_filter(service, filter_id):
    """Delete a filter by ID."""
    try:
        service.users().settings().filters().delete(
            userId='me',
            id=filter_id
        ).execute()
        return True
    except HttpError as error:
        print(f"  Error deleting filter: {error}")
        return False


def create_filter(service, filter_def, label_id):
    """Create a Gmail filter."""
    existing_filter_id = filter_exists(service, filter_def['query'])
    
    if existing_filter_id:
        # Delete existing filter to recreate with correct configuration
        print(f"  Deleting existing filter '{filter_def['name']}' to recreate")
        if delete_filter(service, existing_filter_id):
            print(f"  Deleted existing filter")
    
    try:
        filter_body = {
            'criteria': {
                'query': filter_def['query']
            },
            'action': {
                'addLabelIds': [label_id],
                'removeLabelIds': ['INBOX'] if filter_def['skip_inbox'] else []
            }
        }
        
        if filter_def['category']:
            filter_body['action']['addLabelIds'].append(
                f'CATEGORY_{filter_def["category"]}'
            )
        
        service.users().settings().filters().create(
            userId='me',
            body=filter_body
        ).execute()
        print(f"  Created filter '{filter_def['name']}'")
        return True
    except HttpError as error:
        print(f"  Error creating filter '{filter_def['name']}': {error}")
        return False


def setup_filters(service, label_ids):
    """Create all required filters."""
    print("\n=== Setting up filters ===")
    created_count = 0
    
    for filter_def in FILTERS:
        label_id = label_ids.get(filter_def['label'])
        if not label_id:
            print(f"  Skipping filter '{filter_def['name']}' - label not found")
            continue
        
        if create_filter(service, filter_def, label_id):
            created_count += 1
    
    return created_count


def apply_label_retroactively(service, filter_def, label_id):
    """Apply label to existing messages that match the filter query."""
    try:
        messages = []
        page_token = None
        
        while True:
            results = service.users().messages().list(
                userId='me',
                q=filter_def['query'],
                pageToken=page_token
            ).execute()
            
            messages.extend(results.get('messages', []))
            page_token = results.get('nextPageToken')
            
            if not page_token:
                break
        
        if not messages:
            print(f"  No existing messages found for '{filter_def['name']}'")
            return 0
        
        # Apply label in batches (Gmail allows up to 1000 message IDs per request)
        batch_size = 1000
        labeled_count = 0
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            message_ids = [msg['id'] for msg in batch]
            
            try:
                service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': message_ids,
                        'addLabelIds': [label_id]
                    }
                ).execute()
                labeled_count += len(batch)
            except HttpError as error:
                print(f"  Error applying label to batch: {error}")
        
        print(f"  Applied label to {labeled_count} existing messages for '{filter_def['name']}'")
        return labeled_count
        
    except HttpError as error:
        print(f"  Error searching messages for '{filter_def['name']}': {error}")
        return 0


def apply_retroactive_labels(service, label_ids):
    """Apply labels to all existing messages."""
    print("\n=== Applying labels retroactively ===")
    total_labeled = 0
    
    for filter_def in FILTERS:
        label_id = label_ids.get(filter_def['label'])
        if not label_id:
            continue
        
        count = apply_label_retroactively(service, filter_def, label_id)
        total_labeled += count
    
    return total_labeled


def main():
    """Main execution function."""
    print("Gmail Filters Setup Script")
    print("=" * 50)
    
    try:
        service = authenticate()
        print("Successfully authenticated with Gmail API")
        
        label_ids = setup_labels(service)
        print(f"\nLabels configured: {len(label_ids)}/{len(LABELS)}")
        
        created_filters = setup_filters(service, label_ids)
        print(f"\nFilters created: {created_filters}/{len(FILTERS)}")
        
        total_labeled = apply_retroactive_labels(service, label_ids)
        print(f"\nTotal messages labeled retroactively: {total_labeled}")
        
        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
