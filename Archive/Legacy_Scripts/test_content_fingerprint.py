#!/usr/bin/env python3
"""
VANTAGE Content Fingerprint Test — Verificación de dedup por fingerprint

Este script prueba la funcionalidad de deduplication basada en fingerprint
de contenido (título + empresa + ubicación) para casos donde el jk de Indeed
rota entre reposts del mismo listing.

Caso de referencia: GILSA con 3 jk distintos para el mismo puesto.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Add scripts directory to path
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Import functions from feed_processor
from feed_processor import (
    content_fingerprint,
    compute_content_fingerprint_hash,
    composite_key,
    sha256_hex,
)


def test_gilsa_case():
    """
    Test del caso GILSA: 3 jk distintos para el mismo puesto.
    
    Estos registros deberían tener el mismo fingerprint de contenido
    aunque tengan diferentes jk parameters.
    """
    print("🧪 Test Caso GILSA — Indeed jk rotation")
    print("=" * 50)
    
    # Simular 3 registros con diferente jk pero mismo contenido
    gilsa_records = [
        {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "brand_raw": "GILSA",
            "location": "Mexico City",
            "job_id": "9f45d9e2450010ca",  # jk 1
            "apply_url": "https://mx.indeed.com/viewjob?jk=9f45d9e2450010ca",
        },
        {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "brand_raw": "GILSA",
            "location": "Mexico City",
            "job_id": "cf3ca0540af5d305",  # jk 2
            "apply_url": "https://mx.indeed.com/viewjob?jk=cf3ca0540af5d305",
        },
        {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "brand_raw": "GILSA",
            "location": "Mexico City",
            "job_id": "cf3ca0540af5e1f7cb5",  # jk 3
            "apply_url": "https://mx.indeed.com/viewjob?jk=cf3ca0540af5e1f7cb5",
        },
    ]
    
    fingerprints = []
    composite_keys = []
    
    for i, record in enumerate(gilsa_records, 1):
        fp = content_fingerprint(record)
        ck = composite_key(record)
        fingerprints.append(fp)
        composite_keys.append(ck)
        
        print(f"\nRegistro {i}:")
        print(f"  Título: {record['title']}")
        print(f"  Empresa: {record['brand']}")
        print(f"  Ubicación: {record['location']}")
        print(f"  JK: {record['job_id']}")
        print(f"  Fingerprint: {fp[:16]}...")
        print(f"  Composite Key: {ck}")
    
    # Verificar que todos los fingerprints sean iguales
    unique_fingerprints = set(fingerprints)
    unique_composite_keys = set(composite_keys)
    
    print("\n" + "=" * 50)
    print("📊 Resultados:")
    print(f"  Fingerprints únicos: {len(unique_fingerprints)}")
    print(f"  Composite Keys únicos: {len(unique_composite_keys)}")
    
    if len(unique_fingerprints) == 1:
        print("  ✅ PASS: Todos los registros tienen el mismo fingerprint")
        print("  ✅ El fingerprint detecta correctamente que es el mismo puesto")
    else:
        print("  ❌ FAIL: Los fingerprints son diferentes")
        print(f"  ❌ Unique fingerprints: {unique_fingerprints}")
    
    if len(unique_composite_keys) == 1:
        print("  ✅ PASS: Todos los registros tienen el mismo composite key")
    else:
        print("  ❌ FAIL: Los composite keys son diferentes")
    
    return len(unique_fingerprints) == 1


def test_different_positions():
    """
    Test que puestos diferentes generen fingerprints diferentes.
    """
    print("\n\n🧪 Test Puestos Diferentes")
    print("=" * 50)
    
    different_records = [
        {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "location": "Mexico City",
        },
        {
            "title": "Store Manager",
            "brand": "GILSA",
            "location": "Mexico City",
        },
        {
            "title": "Visual Merchandiser",
            "brand": "Nike",
            "location": "Mexico City",
        },
    ]
    
    fingerprints = []
    
    for i, record in enumerate(different_records, 1):
        fp = content_fingerprint(record)
        fingerprints.append(fp)
        
        print(f"\nRegistro {i}:")
        print(f"  Título: {record['title']}")
        print(f"  Empresa: {record['brand']}")
        print(f"  Ubicación: {record['location']}")
        print(f"  Fingerprint: {fp[:16]}...")
    
    unique_fingerprints = set(fingerprints)
    
    print("\n" + "=" * 50)
    print("📊 Resultados:")
    print(f"  Fingerprints únicos: {len(unique_fingerprints)}")
    print(f"  Total registros: {len(different_records)}")
    
    if len(unique_fingerprints) == len(different_records):
        print("  ✅ PASS: Cada puesto tiene un fingerprint único")
    else:
        print("  ❌ FAIL: Hay colisiones inesperadas en fingerprints")
    
    return len(unique_fingerprints) == len(different_records)


def test_case_insensitivity():
    """
    Test que el fingerprint sea case-insensitive.
    """
    print("\n\n🧪 Test Case Insensitivity")
    print("=" * 50)
    
    case_variations = [
        {
            "title": "Visual Merchandiser",
            "brand": "GILSA",
            "location": "Mexico City",
        },
        {
            "title": "visual merchandiser",
            "brand": "gilsa",
            "location": "mexico city",
        },
        {
            "title": "VISUAL MERCHANDISER",
            "brand": "GILSA",
            "location": "MEXICO CITY",
        },
    ]
    
    fingerprints = []
    
    for i, record in enumerate(case_variations, 1):
        fp = content_fingerprint(record)
        fingerprints.append(fp)
        
        print(f"\nRegistro {i}:")
        print(f"  Input: {record['title']} @ {record['brand']} ({record['location']})")
        print(f"  Fingerprint: {fp[:16]}...")
    
    unique_fingerprints = set(fingerprints)
    
    print("\n" + "=" * 50)
    print("📊 Resultados:")
    print(f"  Fingerprints únicos: {len(unique_fingerprints)}")
    
    if len(unique_fingerprints) == 1:
        print("  ✅ PASS: El fingerprint es case-insensitive")
    else:
        print("  ❌ FAIL: El fingerprint es case-sensitive")
    
    return len(unique_fingerprints) == 1


def main():
    print("🚀 VANTAGE Content Fingerprint Test Suite")
    print("=" * 50)
    
    results = []
    
    # Ejecutar tests
    results.append(("GILSA Case (Indeed jk rotation)", test_gilsa_case()))
    results.append(("Different Positions", test_different_positions()))
    results.append(("Case Insensitivity", test_case_insensitivity()))
    
    # Resumen
    print("\n\n" + "=" * 50)
    print("📋 RESUMEN DE TESTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 Todos los tests pasaron exitosamente")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())