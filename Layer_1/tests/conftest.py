"""Env mínimo para importar feed_processor / backfill_class_a en tests locales."""

import os

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DB_OPPORTUNITIES", "test-db")
os.environ.setdefault("NOTION_ARCHIVE_PAGE_ID", "test-archive")
