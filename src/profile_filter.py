"""Profile filter for VANTAGE Scout, integrated with Layer_1 alias_map patterns."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ProfileFilter:
    """Advanced profile filtering using Layer_1 alias_map and exclusion patterns."""
    
    def __init__(self, alias_map_path: Path | None = None):
        self.alias_map = self._load_alias_map(alias_map_path)
        self.exclude_patterns = self._load_exclude_patterns()
        self.vm_signals = self._load_vm_signals()
    
    def _load_alias_map(self, custom_path: Path | None = None) -> dict[str, Any]:
        """Load alias_map.json from Layer_1 or use defaults."""
        if custom_path and custom_path.exists():
            try:
                return json.loads(custom_path.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        
        # Try default Layer_1 path
        default_path = Path("../../Layer_1/config/alias_map.json")
        if default_path.exists():
            try:
                return json.loads(default_path.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        
        # Fallback to empty map
        return {"aliases": {}, "holding_map": {}}
    
    def _load_exclude_patterns(self) -> list[tuple[str, str]]:
        """Load exclusion patterns with context reasons."""
        patterns = [
            # Sales/Commercial roles (unless VM signal present)
            (r"\bvendedor\b", "ventas_directas"),
            (r"\bsales\b", "ventas_directas"),
            (r"\basesor comercial\b", "ventas_directas"),
            (r"\bcommercial advisor\b", "ventas_directas"),
            
            # Store management (unless VM signal present)
            (r"\bstore\s+manager(?!.*visual)", "gerente_tienda"),
            (r"\bgerente\s+de\s+tienda(?!.*visual)", "gerente_tienda"),
            
            # Junior roles
            (r"\bassistant\b", "rol_junior"),
            (r"\basistente\b", "rol_junior"),
            (r"\bauxiliar\b", "rol_junior"),
            (r"\bjr\.", "rol_junior"),
            (r"\bintern\b", "rol_junior"),
            (r"\binternship\b", "rol_junior"),
            (r"\bentry\s+level\b", "rol_junior"),
            (r"\bpasantía\b", "rol_junior"),
            
            # C-Level and Director roles (unless explicitly VM)
            (r"\bdirector\b(?!.*visual)", "rol_senior"),
            (r"\bvp\b(?!.*visual)", "rol_senior"),
            (r"\bc[-_]?level\b", "rol_senior"),
        ]
        return patterns
    
    def _load_vm_signals(self) -> list[str]:
        """Load VM-related signal keywords."""
        return [
            "visual",
            "merchandis",
            "brand environment",
            "retail design",
            "store design",
            "visual merchandising",
            "vm",
            "brand experience",
            "retail experience"
        ]
    
    def is_hard_blocked(self, brand: str) -> tuple[bool, str]:
        """
        Check if brand is hard blocked using Layer_1 alias_map.
        Returns (is_blocked, reason).
        """
        if not brand:
            return False, ""
        
        brand_lower = brand.strip().lower()
        
        # Check against alias_map
        for alias_key, alias_data in self.alias_map.get("aliases", {}).items():
            if alias_key in brand_lower or brand_lower in alias_key:
                if alias_data.get("hard_block", False):
                    holding = alias_data.get("holding", "Unknown")
                    return True, f"Hard block via alias_map: {holding}"
        
        # Basic hard blocks (fallback)
        basic_blocks = {
            "l'oréal": "L'Oréal division",
            "loreal": "L'Oréal division",
            "levi's": "Levi's",
            "levis": "Levi's",
            "el palacio de hierro": "El Palacio de Hierro"
        }
        
        for block, reason in basic_blocks.items():
            if block in brand_lower:
                return True, f"Hard block: {reason}"
        
        return False, ""
    
    def is_role_excluded(self, title: str) -> tuple[bool, str]:
        """
        Check if role is excluded with context-aware exceptions.
        Returns (is_excluded, reason).
        """
        title_lower = title.lower().strip()
        
        # Check for VM signal (exceptions for certain exclusions)
        has_vm_signal = self._has_vm_signal(title)
        
        for pattern, reason in self.exclude_patterns:
            if re.search(pattern, title_lower):
                # VM signal exceptions for specific reasons
                if has_vm_signal and reason in ["ventas_directas", "gerente_tienda"]:
                    continue
                return True, reason
        
        return False, ""
    
    def _has_vm_signal(self, text: str) -> bool:
        """Detect VM-related signals in text."""
        text_lower = text.lower()
        return any(signal in text_lower for signal in self.vm_signals)
    
    def is_location_allowed(self, location: str, notes: str | None = None) -> tuple[bool, str]:
        """
        Check if location is allowed (CDMX or remote Mexico).
        Returns (is_allowed, reason).
        """
        if not location:
            return False, "Missing location"
        
        text = f"{location} {notes or ''}".lower()
        
        # CDMX hints
        cdmx_hints = [
            "cdmx", "ciudad de mexico", "ciudad de méxico", "mexico city", "méxico city",
            "cd. de mexico", "cd. de méxico", "benito juarez", "benito juárez",
            "polanco", "cuauhtemoc", "cuauhtémoc", "miguel hidalgo",
            "coyoacan", "coyoacán", "alvaro obregon", "álvaro obregón"
        ]
        
        # Mexico hints (broader)
        mexico_hints = cdmx_hints + ["mexico", "méxico", "mx"]
        
        # Remote detection
        remote_pattern = r'\b(remote|remoto)\b'
        is_remote = re.search(remote_pattern, text) is not None
        
        if is_remote:
            # Remote roles must be based in Mexico
            if any(hint in text for hint in mexico_hints):
                return True, "Remote Mexico allowed"
            return False, "Remote outside Mexico"
        
        # On-site roles must be in CDMX
        if any(hint in text for hint in cdmx_hints):
            return True, "CDMX location allowed"
        
        return False, "Location outside CDMX"
    
    def filter_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter items through all profile rules.
        Returns only items that pass all filters.
        """
        filtered_items = []
        stats = {
            "total": len(items),
            "hard_blocked": 0,
            "role_excluded": 0,
            "location_blocked": 0,
            "passed": 0
        }
        
        for item in items:
            brand = item.get("brand", "")
            title = item.get("title", "")
            location = item.get("location", "")
            notes = item.get("notes", "")
            
            # Check hard block
            is_blocked, block_reason = self.is_hard_blocked(brand)
            if is_blocked:
                stats["hard_blocked"] += 1
                continue
            
            # Check role exclusion
            is_excluded, exclude_reason = self.is_role_excluded(title)
            if is_excluded:
                stats["role_excluded"] += 1
                continue
            
            # Check location
            is_allowed, location_reason = self.is_location_allowed(location, notes)
            if not is_allowed:
                stats["location_blocked"] += 1
                continue
            
            # Item passed all filters
            filtered_items.append(item)
            stats["passed"] += 1
        
        return filtered_items, stats
    
    def get_filter_stats(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate detailed filtering statistics without modifying items."""
        stats = {
            "total": len(items),
            "by_block_reason": {},
            "hard_blocked": 0,
            "role_excluded": 0,
            "location_blocked": 0,
            "passed": 0
        }
        
        for item in items:
            brand = item.get("brand", "")
            title = item.get("title", "")
            location = item.get("location", "")
            notes = item.get("notes", "")
            
            # Check hard block
            is_blocked, block_reason = self.is_hard_blocked(brand)
            if is_blocked:
                stats["hard_blocked"] += 1
                stats["by_block_reason"][block_reason] = stats["by_block_reason"].get(block_reason, 0) + 1
                continue
            
            # Check role exclusion
            is_excluded, exclude_reason = self.is_role_excluded(title)
            if is_excluded:
                stats["role_excluded"] += 1
                stats["by_block_reason"][exclude_reason] = stats["by_block_reason"].get(exclude_reason, 0) + 1
                continue
            
            # Check location
            is_allowed, location_reason = self.is_location_allowed(location, notes)
            if not is_allowed:
                stats["location_blocked"] += 1
                stats["by_block_reason"][location_reason] = stats["by_block_reason"].get(location_reason, 0) + 1
                continue
            
            stats["passed"] += 1
        
        return stats