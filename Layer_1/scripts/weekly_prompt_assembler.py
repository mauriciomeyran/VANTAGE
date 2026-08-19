#!/usr/bin/env python3
"""
VANTAGE — Weekly Prompt Assembler
Fetch Prompt A + Wrappers + Prompt E from Notion, substitute today's date,
concatenate (A + Wrapper) and write .md files ready for the engines.
"""

from datetime import date
from pathlib import Path
import re
import sys
import os
from dotenv import load_dotenv

# Load environment variables from project root
_LAYER_1_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_1_ROOT / ".env", override=True)

# Import notion utilities (local wrapper with cache, throttling, retry)
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from notion_utils import notion_get

# ─── CONFIG ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/Prompts")
TODAY = date.today().isoformat()  # 2026-08-08

COMPONENTS = {
    "prompt_a": "368938be-fc42-8162-ae48-d48970a729dc",
    "wrapper_career_sites": "374938be-fc42-8158-93e6-cfeb7bbc5f8b",
    "wrapper_linkedin": "374938be-fc42-81f0-8fc6-d80ae31080ea",
    "wrapper_aggregators": "379938be-fc42-8189-8460-f87cac78f4bc",
    "wrapper_gemini": "368938be-fc42-8139-b6a7-ee467f6c4584",
    "wrapper_grok": "368938be-fc42-8145-944d-d15245b6e65e",
    "wrapper_you": "368938be-fc42-81c8-95cd-d8d75ff3abe4",
    "prompt_e": "368938be-fc42-8177-b4a1-d2e8ea1e2e08",
}

ORDER = [
    ("Career_Sites", "prompt_a", "wrapper_career_sites"),
    ("LinkedIn", "prompt_a", "wrapper_linkedin"),
    ("Aggregators", "prompt_a", "wrapper_aggregators"),
    ("Gemini", "prompt_a", "wrapper_gemini"),
    ("Grok", "prompt_a", "wrapper_grok"),
    ("You_com", "prompt_a", "wrapper_you"),
]

# ─── FETCH (Notion API integration) ─────────────────────────────────────
def fetch_notion_page(page_id: str) -> str:
    """
    Fetch a Notion page by ID and extract its content as plain text.
    Uses notion_utils.notion_get for API calls with cache, throttling, and retry.
    """
    try:
        # Fetch the page properties and blocks
        page_data = notion_get(f"/v1/pages/{page_id}")
        
        # Extract the main content from blocks
        blocks_data = notion_get(f"/v1/blocks/{page_id}/children")
        
        # Convert blocks to plain text
        text_parts = []
        for block in blocks_data.get("results", []):
            block_type = block.get("type", "")
            content = ""
            
            if block_type == "paragraph":
                paragraph = block.get("paragraph", {})
                rich_text = paragraph.get("rich_text", [])
                content = extract_rich_text(rich_text)
            elif block_type == "heading_1":
                heading = block.get("heading_1", {})
                rich_text = heading.get("rich_text", [])
                content = "# " + extract_rich_text(rich_text)
            elif block_type == "heading_2":
                heading = block.get("heading_2", {})
                rich_text = heading.get("rich_text", [])
                content = "## " + extract_rich_text(rich_text)
            elif block_type == "heading_3":
                heading = block.get("heading_3", {})
                rich_text = heading.get("rich_text", [])
                content = "### " + extract_rich_text(rich_text)
            elif block_type == "bulleted_list_item":
                list_item = block.get("bulleted_list_item", {})
                rich_text = list_item.get("rich_text", [])
                content = "- " + extract_rich_text(rich_text)
            elif block_type == "numbered_list_item":
                list_item = block.get("numbered_list_item", {})
                rich_text = list_item.get("rich_text", [])
                content = "1. " + extract_rich_text(rich_text)
            elif block_type == "code":
                code = block.get("code", {})
                rich_text = code.get("rich_text", [])
                content = "```\n" + extract_rich_text(rich_text) + "\n```"
            elif block_type == "quote":
                quote = block.get("quote", {})
                rich_text = quote.get("rich_text", [])
                content = "> " + extract_rich_text(rich_text)
            elif block_type == "divider":
                content = "---"
            elif block_type == "callout":
                callout = block.get("callout", {})
                rich_text = callout.get("rich_text", [])
                content = "> " + extract_rich_text(rich_text)
            
            if content:
                text_parts.append(content)
        
        return "\n".join(text_parts)
    
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Notion page {page_id}: {e}")

def extract_rich_text(rich_text: list) -> str:
    """Extract plain text from Notion rich text objects."""
    text_parts = []
    for text_obj in rich_text:
        if "text" in text_obj:
            content = text_obj["text"].get("content", "")
            text_parts.append(content)
        elif "equation" in text_obj:
            equation = text_obj["equation"].get("expression", "")
            text_parts.append(f"${equation}$")
    return "".join(text_parts)

def clean_and_substitute(text: str) -> str:
    text = text.replace("<br>", "\n").replace("<br/>", "\n")
    text = re.sub(r"\\\[YYYY-MM-DD.*?\\\]", TODAY, text)
    text = re.sub(r"\{YYYY-MM-DD\}", TODAY, text)
    text = re.sub(r"\\{YYYY-MM-DD\\}", TODAY, text)
    text = re.sub(r"\[YYYY-MM-DD\]", TODAY, text)
    text = re.sub(r"TODAY'S DATE: \{injected_by_wrapper\}", f"TODAY'S DATE: {TODAY}", text)
    return text.strip()

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch all once
    contents = {}
    for key, pid in COMPONENTS.items():
        print(f"Fetching {key}...")
        raw = fetch_notion_page(pid)
        contents[key] = clean_and_substitute(raw)

    # 2. Concatenate A + Wrapper and write
    for name, base_key, wrap_key in ORDER:
        combined = contents[base_key] + "\n\n" + contents[wrap_key]
        out_path = OUTPUT_DIR / f"Prompt_{name}_{TODAY}.md"
        out_path.write_text(combined, encoding="utf-8")
        print(f"→ {out_path}")

    # 3. Prompt E alone
    e_path = OUTPUT_DIR / f"Prompt_E_Consolidation_{TODAY}.md"
    e_path.write_text(contents["prompt_e"], encoding="utf-8")
    print(f"→ {e_path}")

    print("\nDone. Files ready for the engines.")

if __name__ == "__main__":
    main()
