"""URL validator for VANTAGE Scout, integrated with Layer_1 patterns."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # Fallback if httpx not available


class URLValidator:
    """URL validation and source classification following Layer_1 patterns."""
    
    # Source classifications
    SOURCE_CATEGORIES = {
        "Career_Page_Premium": [
            "lvmh", "richemont", "kering", "nike", "adidas", "gucci", "dior",
            "louis vuitton", "chanel", "prada", "hermès", "hermes", "balenciaga"
        ],
        "Career_Page_Standard": [
            "careers.", "jobs.", "empleos.", "career.", "vacantes."
        ],
        "Aggregator": [
            "linkedin", "indeed", "occ", "computrabajo", "bumeran", "fashionjobs"
        ],
        "Retail_Giant": [
            "zara", "h&m", "inditex", "gap", "h&m"
        ]
    }
    
    def __init__(self, cache_enabled: bool = True):
        self.url_history: dict[str, dict[str, Any]] = {}
        self.cache_enabled = cache_enabled
        self.source_stats = defaultdict(lambda: {
            "total": 0,
            "accessible": 0,
            "inaccessible": 0,
            "errors": 0
        })
    
    def classify_source(self, url: str) -> str:
        """Classify source type based on URL patterns."""
        if not url:
            return "Unknown"
        
        url_lower = url.lower()
        
        # Check each category
        for category, patterns in self.SOURCE_CATEGORIES.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return category
        
        return "Other"
    
    async def validate_url(self, url: str, timeout: int = 10) -> dict[str, Any]:
        """
        Validate URL accessibility before navigation.
        Returns validation result with status and metadata.
        """
        if not url:
            return {
                "accessible": False,
                "status": "invalid",
                "error": "Empty URL",
                "source_type": "Unknown"
            }
        
        # Check cache if enabled
        if self.cache_enabled and url in self.url_history:
            cached = self.url_history[url]
            cached["from_cache"] = True
            return cached
        
        source_type = self.classify_source(url)
        
        # Update stats
        self.source_stats[source_type]["total"] += 1
        
        # If httpx not available, return optimistic result
        if httpx is None:
            result = {
                "accessible": True,  # Optimistic assumption
                "status": "unknown",
                "error": "httpx not installed - validation skipped",
                "source_type": source_type,
                "from_cache": False
            }
            self.url_history[url] = result
            return result
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try HEAD request first (lighter)
                try:
                    response = await client.head(url, follow_redirects=True)
                    status_code = response.status_code
                except Exception:
                    # Fallback to GET if HEAD fails
                    response = await client.get(url, follow_redirects=True)
                    status_code = response.status_code
                
                result = {
                    "accessible": status_code == 200,
                    "status": status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "source_type": source_type,
                    "from_cache": False
                }
                
                # Update stats
                if status_code == 200:
                    self.source_stats[source_type]["accessible"] += 1
                else:
                    self.source_stats[source_type]["inaccessible"] += 1
                
                self.url_history[url] = result
                return result
                
        except Exception as e:
            result = {
                "accessible": False,
                "status": "error",
                "error": str(e),
                "source_type": source_type,
                "from_cache": False
            }
            self.source_stats[source_type]["errors"] += 1
            self.url_history[url] = result
            return result
    
    async def validate_urls_batch(self, urls: list[str], timeout: int = 10) -> dict[str, dict[str, Any]]:
        """Validate multiple URLs concurrently."""
        tasks = [self.validate_url(url, timeout) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        validation_results = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                validation_results[url] = {
                    "accessible": False,
                    "status": "error",
                    "error": str(result),
                    "source_type": self.classify_source(url)
                }
            else:
                validation_results[url] = result
        
        return validation_results
    
    def filter_valid_urls(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter items to only include those with valid URLs.
        This is a synchronous version that uses cached results.
        """
        valid_items = []
        invalid_count = 0
        
        for item in items:
            url = item.get("apply_url", "")
            
            if not url:
                # Items without URLs might still be valid (manual entry)
                valid_items.append(item)
                continue
            
            # Check cache
            if url in self.url_history:
                validation = self.url_history[url]
                if validation.get("accessible", False):
                    valid_items.append(item)
                else:
                    invalid_count += 1
            else:
                # If not in cache, assume valid (will be validated during navigation)
                valid_items.append(item)
        
        return valid_items
    
    def get_source_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics about URL validation by source type."""
        return dict(self.source_stats)
    
    def get_validation_summary(self) -> dict[str, Any]:
        """Get overall validation summary."""
        total_validated = len(self.url_history)
        accessible = sum(1 for v in self.url_history.values() if v.get("accessible", False))
        inaccessible = total_validated - accessible
        
        return {
            "total_validated": total_validated,
            "accessible": accessible,
            "inaccessible": inaccessible,
            "success_rate": accessible / total_validated if total_validated > 0 else 0,
            "cache_enabled": self.cache_enabled,
            "source_breakdown": self.get_source_stats()
        }
    
    def clear_cache(self) -> None:
        """Clear URL validation cache."""
        self.url_history.clear()
        self.source_stats = defaultdict(lambda: {
            "total": 0,
            "accessible": 0,
            "inaccessible": 0,
            "errors": 0
        })