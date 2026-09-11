"""
Notion Client Fake para Tests

G6: Fake espeja client.pages.update con chain structure real
"""

from typing import Dict, Any, Optional


class NotionClientFake:
    """
    Cliente Notion fake para tests - espeja client.pages.update chain structure.
    
    G6: This fake mirrors the real Notion client API structure:
    - client.pages.update(page_id=..., properties=...) returns updated page
    - Properties are stored in a proper API-like structure
    - Pages are stored with full API record structure (id, properties, last_edited_*)
    """
    
    def __init__(self):
        self.pages: Dict[str, Dict[str, Any]] = {}
        self.update_count = 0
        self.retrieve_count = 0
        self.update_log: list[Dict[str, Any]] = []
    
    def pages_update(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fake de client.pages.update - espeja la API real.
        
        Returns the full updated page record with API structure:
        {
            "id": page_id,
            "properties": {...updated properties...},
            "last_edited_time": "...",
            "last_edited_by": {"object": "user", "id": "..."}
        }
        """
        self.update_count += 1
        
        if page_id not in self.pages:
            self.pages[page_id] = {
                "id": page_id,
                "properties": {},
                "last_edited_time": "2026-09-10T12:00:00.000Z",
                "last_edited_by": {"object": "user", "id": "fake-bot-id"}
            }
        
        # Log the update for verification
        self.update_log.append({
            "page_id": page_id,
            "properties": properties,
            "timestamp": self.update_count
        })
        
        # Update the page properties
        self.pages[page_id]["properties"].update(properties)
        
        # Update last_edited metadata
        self.pages[page_id]["last_edited_time"] = "2026-09-10T12:00:00.000Z"
        self.pages[page_id]["last_edited_by"] = {"object": "user", "id": "fake-bot-id"}
        
        return self.pages[page_id]
    
    def pages_retrieve(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Fake de client.pages.retrieve.
        
        Returns the full page record with API structure.
        """
        self.retrieve_count += 1
        return self.pages.get(page_id)
    
    def get_update_count(self) -> int:
        """Helper para verificar número de llamadas a pages.update"""
        return self.update_count
    
    def get_update_log(self) -> list[Dict[str, Any]]:
        """Helper para verificar log de updates"""
        return self.update_log
    
    def reset(self):
        """Reset fake state"""
        self.pages.clear()
        self.update_count = 0
        self.retrieve_count = 0
        self.update_log.clear()
