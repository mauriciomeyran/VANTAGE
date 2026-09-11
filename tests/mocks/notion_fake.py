"""
Notion Client Fake para Tests

H3: Fake espeja la cadena real `client.pages.update/retrieve` vía namespace
`fake.pages` (+ métodos planos `pages_update`/`pages_retrieve` por compat).
"""

from typing import Dict, Any, Optional


class _PagesNamespace:
    """Namespace `fake.pages` — espeja `client.pages.*` (H3)."""

    def __init__(self, outer: "NotionClientFake"):
        self._outer = outer

    def update(self, page_id: Optional[str] = None, properties: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        return self._outer.pages_update(page_id, properties or {})

    def retrieve(self, page_id: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self._outer.pages_retrieve(page_id)


class NotionClientFake:
    """
    Cliente Notion fake para tests - espeja la cadena real del cliente.

    H3: `fake.pages.update(page_id=..., properties=...)` y
    `fake.pages.retrieve(page_id=...)` espejan `client.pages.*`.
    Los métodos planos se conservan para compatibilidad con tests existentes.
    Registros almacenados con estructura API real (id, properties,
    last_edited_time, last_edited_by={object,id}).
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.pages = _PagesNamespace(self)
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

        if page_id not in self._store:
            self._store[page_id] = {
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
        self._store[page_id]["properties"].update(properties)

        # Update last_edited metadata
        self._store[page_id]["last_edited_time"] = "2026-09-10T12:00:00.000Z"
        self._store[page_id]["last_edited_by"] = {"object": "user", "id": "fake-bot-id"}

        return self._store[page_id]

    def pages_retrieve(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Fake de client.pages.retrieve.

        Returns the full page record with API structure.
        """
        self.retrieve_count += 1
        return self._store.get(page_id)

    def get_update_count(self) -> int:
        """Helper para verificar número de llamadas a pages.update"""
        return self.update_count

    def get_update_log(self) -> list[Dict[str, Any]]:
        """Helper para verificar log de updates"""
        return self.update_log

    def reset(self):
        """Reset fake state"""
        self._store.clear()
        self.update_count = 0
        self.retrieve_count = 0
        self.update_log.clear()
