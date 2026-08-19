"""Gate logic for VANTAGE Scout, adapted from Layer_1 patterns."""

from __future__ import annotations

from typing import Any


class ScoutGate:
    """Gate logic system following Layer_1 terminal state protection patterns."""
    
    # Terminal statuses that should never be overwritten
    TERMINAL_STATUSES = {"Postulado", "Rechazado", "Archivar", "Expirada"}
    
    # Terminal next actions that should never be overwritten
    TERMINAL_ACTIONS = {"Archivar", "Expirada"}
    
    @staticmethod
    def should_process(item: dict[str, Any]) -> bool:
        """
        Determine if an item should be processed based on gate logic.
        Implements terminal state protection where manual human intent overrides automation.
        """
        # Check terminal statuses
        status = item.get("status", "")
        if status in ScoutGate.TERMINAL_STATUSES:
            return False
        
        # Check terminal next actions
        next_action = item.get("next_action", "")
        if next_action in ScoutGate.TERMINAL_ACTIONS:
            return False
        
        return True
    
    @staticmethod
    def get_suggested_action(item: dict[str, Any]) -> str:
        """
        Get suggested next action based on item properties.
        This is a simplified version for Scout local usage.
        """
        # If item has terminal action, respect it
        next_action = item.get("next_action", "")
        if next_action in ScoutGate.TERMINAL_ACTIONS:
            return next_action
        
        # Simple heuristic for Scout
        source_type = item.get("source_type", "")
        fetch_status = item.get("fetch_status", "")
        
        if fetch_status == "direct_apply":
            return "Review & Apply"
        elif fetch_status == "redirect":
            return "Verify URL"
        elif fetch_status == "blocked":
            return "Investigate"
        else:
            return "Review"
    
    @staticmethod
    def filter_terminal_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out items in terminal states from processing."""
        processable_items = []
        terminal_count = 0
        
        for item in items:
            if ScoutGate.should_process(item):
                processable_items.append(item)
            else:
                terminal_count += 1
        
        return processable_items
    
    @staticmethod
    def get_gate_stats(items: list[dict[str, Any]]) -> dict[str, int]:
        """Generate statistics about gate filtering."""
        stats = {
            "total_items": len(items),
            "processable": 0,
            "terminal_protected": 0,
            "by_status": {},
            "by_action": {}
        }
        
        for item in items:
            status = item.get("status", "Unknown")
            next_action = item.get("next_action", "Unknown")
            
            # Count by status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by action
            stats["by_action"][next_action] = stats["by_action"].get(next_action, 0) + 1
            
            # Determine if processable
            if ScoutGate.should_process(item):
                stats["processable"] += 1
            else:
                stats["terminal_protected"] += 1
        
        return stats