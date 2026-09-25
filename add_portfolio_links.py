#!/usr/bin/env python3
"""Agrega hipervínculo clickable a la palabra PORTAFOLIO/PORTFOLIO en CVs de Mauricio Meyrán."""
import pymupdf
import os

BASE = "/Users/mauriciomeyran/.hermes/attachments"
OUTPUT_SUFFIX = "_linked"

# Mapeo: archivo -> idioma
mapping = {
    "2026_Mauricio_Meyran_Adolfo_Dominguez_Visual_Merchandising.pdf": "ES",
    "2026_Mauricio_Meyran_Comercio_Excelente_Senior_Merchandising_Coordinator.pdf": "EN",
    "2026_Mauricio_Meyran_Commando_Retail_Retail_Operation_Manager.pdf": "ES",
    "2026_Mauricio_Meyran_Confidencial_Brand_Activation_Coordinator.pdf": "EN",
    "2026_Mauricio_Meyran_Grupo_Axo_Gerente_Visual_Merchandising.pdf": "ES",
    "2026_Mauricio_Meyran_Grupo_SomosUno_Coordinador_a_de_Display_Visual_Merchandising.pdf": "ES",
    "2026_Mauricio_Meyran_LG_Electronics_In_Store_Display_Analyst.pdf": "ES",
    "2026_Mauricio_Meyran_Match_Consulting_Especialista_Contenido_Comunicacion_Visual_Marcas_Lujo.pdf": "ES",
    "2026_Mauricio_Meyran_Modatelas_Supervisor_Distrital_Imagen_Visual_Merchandising.pdf": "ES",
    "2026_Mauricio_Meyran_Monster_Energy_MAT_Lead_Gold_Squad.pdf": "ES",
    "2026_Mauricio_Meyran_Philip_Morris_International_Retail_Activation_Coordinator.pdf": "ES",
    "2026_Mauricio_Meyran_SC_Johnson_Sr_Analyst_Trade_Customer_Marketing.pdf": "ES",
    "2026_Mauricio_Meyran_Sanborns_Supervisor_Visual_Merchandising_Muebles.pdf": "ES",
    "2026_Mauricio_Meyran_Suntory_Global_Spirits_Merch_Supervisor.pdf": "EN",
    "2026_Mauricio_Meyran_Tendam_RIT_Visual_Merchandising.pdf": "ES",
    "2026_Mauricio_Meyran_Tiffany_Co_Retail_Field_Coach_CV-A.pdf": "EN",
    "2026_Mauricio_Meyran_Tiffany_Co_Visual_Merchandising_Analyst.pdf": "EN",
    "2026_Mauricio_Meyran_Viva_Brand_Production_Specialist.pdf": "ES",
}

URL_ES = "https://mmeyranesp.myportfolio.com/"
URL_EN = "https://mmeyraneng.myportfolio.com/"

PALABRA_ES = "PORTAFOLIO"
PALABRA_EN = "PORTFOLIO"


def process_pdf(filepath):
    doc = pymupdf.open(filepath)
    page = doc[0]  # primera página (header)

    filename = os.path.basename(filepath)
    lang = mapping.get(filename)
    if not lang:
        print(f"SKIP {filename}: no lang mapping")
        doc.close()
        return False

    word = PALABRA_ES if lang == "ES" else PALABRA_EN
    url = URL_ES if lang == "ES" else URL_EN

    # Buscar la palabra - search_for busca substring, devuelve lista de Rect
    rects = page.search_for(word)

    if not rects:
        # Intentar buscar la palabra más completa
        alt_word = "PORTAFOLIO CREATIVO" if lang == "ES" else "PORTFOLIO"
        rects = page.search_for(alt_word)

    if not rects:
        print(f"FAIL {filename}: word '{word}' not found on page 0")
        doc.close()
        return False

    rect = rects[0]  # Usar el primer match

    # Verificar que no exista ya un link en esa posición
    existing_links = page.get_links()
    link_exists = any(
        l.get('kind') == pymupdf.LINK_GOTO
        and abs(l.get('from', pymupdf.Rect(0, 0, 0, 0)).x0 - rect.x0) < 1
        and abs(l.get('from', pymupdf.Rect(0, 0, 0, 0)).y0 - rect.y0) < 1
        for l in existing_links
    )

    if link_exists:
        print(f"SKIP {filename}: link already exists on '{word}'")
        doc.close()
        return True

    # Crear link anotado con insert_link
    page.insert_link({
        'from': rect,
        'kind': pymupdf.LINK_URI,
        'uri': url
    })

    # Guardar en nuevo archivo
    out_name = filename.replace('.pdf', f'{OUTPUT_SUFFIX}.pdf')
    out_path = os.path.join(BASE, out_name)
    doc.save(out_path, garbage=4, deflate=True)
    doc.close()

    print(f"OK {filename} -> {out_name} (lang={lang}, url={url})")
    return True


# Procesar todos
pdfs = sorted([
    f for f in os.listdir(BASE)
    if f.endswith('.pdf') and OUTPUT_SUFFIX not in f
    and f in mapping
])
print(f"Processing {len(pdfs)} PDFs...\n")

results = {}
for pdf in pdfs:
    ok = process_pdf(os.path.join(BASE, pdf))
    results[pdf] = ok

print("\n--- SUMMARY ---")
ok_count = sum(1 for v in results.values() if v)
print(f"OK: {ok_count}/{len(results)}")
for pdf, ok in results.items():
    status = "✓" if ok else "✗"
    print(f"  {status} {pdf}")
