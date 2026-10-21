
#!/usr/bin/env python3
import re
import sys
import html
import urllib.parse
import urllib.request

def extract_magnet(url):
    # Descargar el HTML de la página
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        page = response.read().decode("utf-8", errors="replace")

    page = html.unescape(page)

    # Buscar enlaces magnet: directamente en el HTML
    pattern = r'magnet:\?[^\s"\'<>]+'
    matches = re.findall(pattern, page, flags=re.IGNORECASE)

    # Decodificar entidades y escapes HTML
    results = []
    for match in matches:
        magnet = urllib.parse.unquote(match).rstrip(");,")
        if magnet not in results:
            results.append(magnet)

    return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f'Uso: python3 {sys.argv[0]} "URL"')
        sys.exit(1)

    try:
        magnets = extract_magnet(sys.argv[1])

        if magnets:
            for magnet in magnets:
                print(magnet)
        else:
            print("No se encontraron enlaces magnet en el HTML.")
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
