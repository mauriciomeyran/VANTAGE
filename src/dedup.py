"""Deduplication system for VANTAGE Scout, integrated with Layer_1 patterns."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class ScoutDedup:
    """Hash-based deduplication system following Layer_1 patterns."""
    
    def __init__(self, output_dir: Path, history_window_days: int = 30):
        self.output_dir = output_dir
        self.history_window_days = history_window_days
        self.history = self._load_history()
    
    def _load_history(self) -> dict[str, dict[str, Any]]:
        """Load historical items from previous Scout outputs."""
        history = {}
        cutoff_date = datetime.now() - timedelta(days=self.history_window_days)
        
        if not self.output_dir.exists():
            return history
        
        for json_file in self.output_dir.glob("vantage_scout_*.json"):
            try:
                # Check file age against history window
                file_mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    continue
                
                data = json.loads(json_file.read_text())
                for item in data.get("items", []):
                    hash_key = self._generate_hash(item)
                    history[hash_key] = item
            except (json.JSONDecodeError, IOError):
                # Skip corrupted files
                continue
        
        return history
    
    def _generate_hash(self, item: dict[str, Any]) -> str:
        """Generate hash based on Layer_1 patterns: apply_url > brand|title|location > job_id."""
        url = item.get("apply_url", "")
        
        # Primary hash: apply_url (normalized)
        if url:
            return hashlib.sha256(url.lower().strip().encode()).hexdigest()
        
        # Secondary hash: brand|title|location
        brand = item.get("brand", "")
        title = item.get("title", "")
        location = item.get("location", "")
        
        combined = f"{brand}|{title}|{location}".lower().strip()
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def is_duplicate(self, item: dict[str, Any]) -> bool:
        """Check if item is a duplicate based on hash comparison."""
        hash_key = self._generate_hash(item)
        return hash_key in self.history
    
    def add_to_history(self, item: dict[str, Any]) -> None:
        """Add item to history for future deduplication."""
        hash_key = self._generate_hash(item)
        self.history[hash_key] = item
    
    def get_duplicate_stats(self, items: list[dict[str, Any]]) -> dict[str, int]:
        """Generate statistics about duplicate detection."""
        stats = {
            "total_items": len(items),
            "duplicates_found": 0,
            "unique_items": 0,
            "history_size": len(self.history)
        }
        
        for item in items:
            if self.is_duplicate(item):
                stats["duplicates_found"] += 1
            else:
                stats["unique_items"] += 1
        
        return stats
    
    def filter_duplicates(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out duplicate items, returning only unique ones."""
        unique_items = []
        seen_hashes = set()
        
        for item in items:
            hash_key = self._generate_hash(item)
            
            # Check against history
            if hash_key in self.history:
                continue
            
            # Check against current batch
            if hash_key in seen_hashes:
                continue
            
            seen_hashes.add(hash_key)
            unique_items.append(item)
        
        return unique_items