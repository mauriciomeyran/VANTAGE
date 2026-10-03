#!/usr/bin/env python3
"""
Divide VANTAGE_digest.md en archivos de menos de 500,000 palabras.
Corta en líneas para mantener la estructura del archivo.
"""

from pathlib import Path

INPUT_FILE = Path("VANTAGE_digest.md")
MAX_WORDS = 500000

def count_words(text: str) -> int:
    """Cuenta palabras en un string."""
    return len(text.split())

def split_file():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_part = []
    current_word_count = 0
    part_number = 1

    for line in lines:
        line_word_count = count_words(line)

        # Si agregar esta línea excede el límite y ya tenemos contenido,
        # guardar el parte actual y empezar uno nuevo
        if current_word_count + line_word_count > MAX_WORDS and current_part:
            # Guardar parte actual
            output_file = INPUT_FILE.parent / f"{INPUT_FILE.stem}_part_{part_number}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(current_part)
            words_saved = current_word_count
            print(f"Parte {part_number}: {words_saved:,} palabras -> {output_file.name}")

            # Empezar nuevo parte
            part_number += 1
            current_part = [line]
            current_word_count = line_word_count
        else:
            current_part.append(line)
            current_word_count += line_word_count

    # Guardar el último parte
    if current_part:
        output_file = INPUT_FILE.parent / f"{INPUT_FILE.stem}_part_{part_number}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(current_part)
        words_saved = current_word_count
        print(f"Parte {part_number}: {words_saved:,} palabras -> {output_file.name}")

    print(f"\nTotal de partes: {part_number}")

if __name__ == "__main__":
    if not INPUT_FILE.exists():
        print(f"Error: No se encontró {INPUT_FILE}")
        exit(1)

    print(f"Procesando {INPUT_FILE}...")
    split_file()
