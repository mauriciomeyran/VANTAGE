#!/usr/bin/env python3

import requests
import json
import sys

BASE = "http://127.0.0.1:8000"

def test_health():
    r = requests.get(f"{BASE}/health")

    print("\n[HEALTH]")
    print("STATUS:", r.status_code)
    print(r.text)

    if r.status_code != 200:
        raise Exception("health failed")

def test_blocked():
    r = requests.get(f"{BASE}/blocked-vacancies")

    print("\n[BLOCKED VACANCIES]")
    print("STATUS:", r.status_code)

    try:
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)
        raise

    if r.status_code != 200:
        raise Exception("blocked-vacancies failed")

    if "vacancies" not in data:
        raise Exception("missing vacancies key")

def main():
    try:
        test_health()
        test_blocked()

        print("\nSMOKE PASSED")

    except Exception as e:
        print("\nSMOKE FAILED")
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
