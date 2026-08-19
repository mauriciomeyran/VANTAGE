#!/usr/bin/env python3
"""
analyze_block_ids.py

Extracts and compares block IDs from:
1. apply_hyperlinks.py MAPPING
2. V_ID_CENSUS_PRODUCTION.md
3. Live Notion API responses (from fetch results)

Reports valid vs broken links per document.
"""

import re
import json
from pathlib import Path
from collections import defaultdict

# Paths
APPLY_HYPERLINKS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/apply_hyperlinks.py")
CENSUS_PATH = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/V_ID_CENSUS_PRODUCTION.md")
KERNEL_FETCH_PATH = Path("/var/folders/s7/7cwdld9x55d_dsrgg2xsn7gm0000gp/T/devin-overflows-502/6664bc03/content.txt")
MANUAL_FETCH_PATH = Path("/var/folders/s7/7cwdld9x55d_dsrgg2xsn7gm0000gp/T/devin-overflows-502/bb85c062/content.txt")
SP_FETCH_PATH = Path("/var/folders/s7/7cwdld9x55d_dsrgg2xsn7gm0000gp/T/devin-overflows-502/d227f53d/content.txt")
CANON_FETCH_PATH = Path("/var/folders/s7/7cwdld9x55d_dsrgg2xsn7gm0000gp/T/devin-overflows-502/16ea3edc/content.txt")

def extract_block_ids_from_mapping(content):
    """Extract block IDs from apply_hyperlinks.py MAPPING dictionary."""
    pattern = r'#([a-f0-9]+)'
    matches = re.findall(pattern, content)
    return set(matches)

def extract_block_ids_from_census(content):
    """Extract block IDs from V_ID_CENSUS_PRODUCTION.md."""
    pattern = r'#([a-f0-9]+)'
    matches = re.findall(pattern, content)
    return set(matches)

def extract_block_ids_from_notion_fetch(content):
    """Extract block IDs from Notion API fetch response."""
    # Notion fetch responses contain blocks with IDs in various formats
    # Look for patterns like #39e938befc428... in URLs
    pattern = r'#([a-f0-9]+)'
    matches = re.findall(pattern, content)
    return set(matches)

def main():
    print("🔍 EXTRACTING BLOCK IDs FROM ALL SOURCES\n")
    print("=" * 80)
    
    # 1. Extract from apply_hyperlinks.py
    print("\n📋 apply_hyperlinks.py MAPPING:")
    with open(APPLY_HYPERLINKS_PATH, 'r') as f:
        mapping_content = f.read()
    mapping_ids = extract_block_ids_from_mapping(mapping_content)
    print(f"   Total block IDs found: {len(mapping_ids)}")
    print(f"   Sample IDs: {list(mapping_ids)[:5]}")
    
    # 2. Extract from V_ID_CENSUS_PRODUCTION.md
    print("\n📋 V_ID_CENSUS_PRODUCTION.md:")
    with open(CENSUS_PATH, 'r') as f:
        census_content = f.read()
    census_ids = extract_block_ids_from_census(census_content)
    print(f"   Total block IDs found: {len(census_ids)}")
    print(f"   Sample IDs: {list(census_ids)[:5]}")
    
    # 3. Extract from live Notion fetches
    print("\n📋 Live Notion API Fetches:")
    
    kernel_ids = set()
    manual_ids = set()
    sp_ids = set()
    canon_ids = set()
    
    if KERNEL_FETCH_PATH.exists():
        with open(KERNEL_FETCH_PATH, 'r') as f:
            kernel_content = f.read()
        kernel_ids = extract_block_ids_from_notion_fetch(kernel_content)
        print(f"   KERNEL: {len(kernel_ids)} block IDs")
    
    if MANUAL_FETCH_PATH.exists():
        with open(MANUAL_FETCH_PATH, 'r') as f:
            manual_content = f.read()
        manual_ids = extract_block_ids_from_notion_fetch(manual_content)
        print(f"   MANUAL: {len(manual_ids)} block IDs")
    
    if SP_FETCH_PATH.exists():
        with open(SP_FETCH_PATH, 'r') as f:
            sp_content = f.read()
        sp_ids = extract_block_ids_from_notion_fetch(sp_content)
        print(f"   SYSTEM PROMPT: {len(sp_ids)} block IDs")
    
    if CANON_FETCH_PATH.exists():
        with open(CANON_FETCH_PATH, 'r') as f:
            canon_content = f.read()
        canon_ids = extract_block_ids_from_notion_fetch(canon_content)
        print(f"   CAREER CANON: {len(canon_ids)} block IDs")
    
    # Combine all live Notion IDs
    all_live_ids = kernel_ids | manual_ids | sp_ids | canon_ids
    print(f"   TOTAL (all pages): {len(all_live_ids)} block IDs")
    
    # 4. Compare mapping vs live
    print("\n" + "=" * 80)
    print("📊 COMPARISON: apply_hyperlinks.py MAPPING vs Live Notion API")
    print("=" * 80)
    
    mapping_only = mapping_ids - all_live_ids
    live_only = all_live_ids - mapping_ids
    common = mapping_ids & all_live_ids
    
    print(f"\n✅ VALID links (block ID exists in live Notion): {len(common)}")
    print(f"❌ BROKEN links (block ID NOT in live Notion): {len(mapping_only)}")
    print(f"➕ NEW in live Notion (not in mapping): {len(live_only)}")
    
    # 5. Compare census vs live
    print("\n" + "=" * 80)
    print("📊 COMPARISON: V_ID_CENSUS_PRODUCTION.md vs Live Notion API")
    print("=" * 80)
    
    census_only = census_ids - all_live_ids
    live_only_census = all_live_ids - census_ids
    common_census = census_ids & all_live_ids
    
    print(f"\n✅ CENSUS matches live Notion: {len(common_census)}")
    print(f"❌ CENSUS has obsolete IDs: {len(census_only)}")
    print(f"➕ NEW in live Notion (not in census): {len(live_only_census)}")
    
    # 6. Compare mapping vs census
    print("\n" + "=" * 80)
    print("📊 COMPARISON: apply_hyperlinks.py MAPPING vs V_ID_CENSUS_PRODUCTION.md")
    print("=" * 80)
    
    mapping_only_census = mapping_ids - census_ids
    census_only_mapping = census_ids - mapping_ids
    common_mapping_census = mapping_ids & census_ids
    
    print(f"\n✅ MAPPING matches CENSUS: {len(common_mapping_census)}")
    print(f"❌ MAPPING has IDs not in CENSUS: {len(mapping_only_census)}")
    print(f"➕ CENSUS has IDs not in MAPPING: {len(census_only_mapping)}")
    
    # 7. Detailed breakdown by page
    print("\n" + "=" * 80)
    print("📊 DETAILED BREAKDOWN BY PAGE")
    print("=" * 80)
    
    # Extract mapping IDs by page from apply_hyperlinks.py
    kernel_page_ids = set()
    manual_page_ids = set()
    sp_page_ids = set()
    canon_page_ids = set()
    
    # Parse the MAPPING to separate by page
    lines = mapping_content.split('\n')
    current_page = None
    for line in lines:
        if '--- KERNEL ---' in line:
            current_page = 'KERNEL'
        elif '--- SYSTEM PROMPT ---' in line:
            current_page = 'SP'
        elif '--- MANUAL ---' in line:
            current_page = 'MANUAL'
        elif '--- CAREER CANON ---' in line:
            current_page = 'CANON'
        elif current_page and '#' in line and ':' in line:
            # Extract block ID from this line
            match = re.search(r'#([a-f0-9]+)', line)
            if match:
                block_id = match.group(1)
                if current_page == 'KERNEL':
                    kernel_page_ids.add(block_id)
                elif current_page == 'SP':
                    sp_page_ids.add(block_id)
                elif current_page == 'MANUAL':
                    manual_page_ids.add(block_id)
                elif current_page == 'CANON':
                    canon_page_ids.add(block_id)
    
    print(f"\n📄 KERNEL:")
    print(f"   Mapping IDs: {len(kernel_page_ids)}")
    print(f"   Live Notion IDs: {len(kernel_ids)}")
    kernel_valid = kernel_page_ids & kernel_ids
    kernel_broken = kernel_page_ids - kernel_ids
    print(f"   ✅ Valid: {len(kernel_valid)}")
    print(f"   ❌ Broken: {len(kernel_broken)}")
    if kernel_broken:
        print(f"   Broken IDs: {list(kernel_broken)[:5]}...")
    
    print(f"\n📄 MANUAL:")
    print(f"   Mapping IDs: {len(manual_page_ids)}")
    print(f"   Live Notion IDs: {len(manual_ids)}")
    manual_valid = manual_page_ids & manual_ids
    manual_broken = manual_page_ids - manual_ids
    print(f"   ✅ Valid: {len(manual_valid)}")
    print(f"   ❌ Broken: {len(manual_broken)}")
    if manual_broken:
        print(f"   Broken IDs: {list(manual_broken)[:5]}...")
    
    print(f"\n📄 SYSTEM PROMPT:")
    print(f"   Mapping IDs: {len(sp_page_ids)}")
    print(f"   Live Notion IDs: {len(sp_ids)}")
    sp_valid = sp_page_ids & sp_ids
    sp_broken = sp_page_ids - sp_ids
    print(f"   ✅ Valid: {len(sp_valid)}")
    print(f"   ❌ Broken: {len(sp_broken)}")
    if sp_broken:
        print(f"   Broken IDs: {list(sp_broken)[:5]}...")
    
    print(f"\n📄 CAREER CANON:")
    print(f"   Mapping IDs: {len(canon_page_ids)}")
    print(f"   Live Notion IDs: {len(canon_ids)}")
    canon_valid = canon_page_ids & canon_ids
    canon_broken = canon_page_ids - canon_ids
    print(f"   ✅ Valid: {len(canon_valid)}")
    print(f"   ❌ Broken: {len(canon_broken)}")
    if canon_broken:
        print(f"   Broken IDs: {list(canon_broken)[:5]}...")
    
    # 8. Final summary table
    print("\n" + "=" * 80)
    print("📋 FINAL SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Document':<20} {'Mapping IDs':<15} {'Live IDs':<15} {'Valid':<10} {'Broken':<10}")
    print("-" * 80)
    print(f"{'KERNEL':<20} {len(kernel_page_ids):<15} {len(kernel_ids):<15} {len(kernel_valid):<10} {len(kernel_broken):<10}")
    print(f"{'MANUAL':<20} {len(manual_page_ids):<15} {len(manual_ids):<15} {len(manual_valid):<10} {len(manual_broken):<10}")
    print(f"{'SYSTEM PROMPT':<20} {len(sp_page_ids):<15} {len(sp_ids):<15} {len(sp_valid):<10} {len(sp_broken):<10}")
    print(f"{'CAREER CANON':<20} {len(canon_page_ids):<15} {len(canon_ids):<15} {len(canon_valid):<10} {len(canon_broken):<10}")
    print("-" * 80)
    print(f"{'TOTAL':<20} {len(mapping_ids):<15} {len(all_live_ids):<15} {len(common):<10} {len(mapping_only):<10}")
    
    print("\n" + "=" * 80)
    print("🔍 CENSUS RELIABILITY ASSESSMENT")
    print("=" * 80)
    if len(common_census) == len(census_ids):
        print("✅ CENSUS appears to be reliable as source of truth")
        print(f"   All {len(census_ids)} CENSUS IDs match live Notion API")
    else:
        print(f"⚠️  CENSUS has {len(census_only)} obsolete IDs out of {len(census_ids)} total")
        print(f"   Reliability: {len(common_census)}/{len(census_ids)} ({100*len(common_census)/len(census_ids):.1f}%)")
    
    print("\n" + "=" * 80)
    print("🏁 ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()