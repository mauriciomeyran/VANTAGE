"""Helper for handling React Select components in web scraping."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ReactSelectHelper:
    """Helper for interacting with React Select dropdowns."""
    
    @staticmethod
    def get_react_select_instructions(field_name: str, search_term: str) -> str:
        """Generate browser-use instructions for React Select interaction."""
        return f"""
        For the React Select dropdown field "{field_name}":
        1. Click on the dropdown to open it
        2. Type "{search_term}" in the search/input field that appears
        3. Wait for the dropdown to show matching options
        4. Click on the option that matches "{search_term}" exactly or is the closest match
        5. If no exact match appears, select the most relevant option
        6. If the dropdown closes without selection, repeat the process
        
        Important: React Select components require direct DOM interaction, not URL parameters.
        Type the search term character by character to trigger the search functionality.
        """
    
    @staticmethod
    def get_bumeran_search_instructions(search_term: str, location: str) -> str:
        """Generate specific instructions for Bumeran search form."""
        return f"""
        Navigate to bumeran.com.mx and:
        1. Find the search form with "Buscar empleo por puesto o palabra clave"
        2. Click on the job title field (React Select dropdown)
        3. Type "{search_term}" slowly
        4. Wait for dropdown options to appear
        5. Select the option that matches "{search_term}" or closest equivalent
        6. Click on the location field (React Select dropdown)
        7. Type "{location}" slowly
        8. Wait for dropdown options to appear
        9. Select "Ciudad de México" or "Mexico City" from the options
        10. Click the "Buscar" button
        11. Wait for results to load
        12. Extract all job postings that match Visual Merchandising criteria
        
        If the dropdown doesn't respond to typing, try:
        - Clicking the field again to ensure focus
        - Using backspace to clear any existing text
        - Typing more slowly to allow React to process each keystroke
        """
    
    @staticmethod
    def get_fallback_search_instructions(url: str, search_term: str) -> str:
        """Generate fallback instructions when React Select fails."""
        return f"""
        If React Select interaction fails, try these alternatives:
        1. Look for a search button that might accept direct text input
        2. Check if there's a "Advanced Search" link with traditional form fields
        3. Look for category browsing links (e.g., "Marketing", "Retail", "Design")
        4. Try navigating through job categories manually
        5. Check if there's a sitemap or job listing page that doesn't require search
        
        Current URL: {url}
        Search term: {search_term}
        """