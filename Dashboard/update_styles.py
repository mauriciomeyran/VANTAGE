import re
import os

def patch_css(filename, new_css):
    if not os.path.exists(filename):
        print(f"Error: {filename} no encontrado.")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex para encontrar el bloque <style> completo y reemplazarlo
    style_pattern = re.compile(r'<style>.*?</style>', re.DOTALL | re.IGNORECASE)
    
    if style_pattern.search(content):
        new_content = style_pattern.sub(f'<style>\n{new_css}\n    </style>', content)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ {filename} actualizado con estilo Notion Dark.")
    else:
        print(f"⚠ No se encontró etiqueta <style> en {filename}.")

# --- CSS DEFINITIONS ---

CHECKLIST_CSS = """        :root {
            --bg-main: #191919;
            --text-main: #D4D4D4;
            --text-secondary: #9B9B9B;
            --accent: #2383E2;
            --border: rgba(255, 255, 255, 0.09);
            --font-family: 'Inter', -apple-system, sans-serif;
        }
        body { background-color: var(--bg-main); color: var(--text-main); font-family: var(--font-family); padding: 40px; }
        code { background: #252525; color: #EB5757; padding: 10px; border-radius: 4px; display: block; }
        .task-card { border-bottom: 1px solid var(--border); padding: 16px 0; }"""

DASHBOARD_CSS = """        :root {
            --bg-main: #191919;
            --bg-sidebar: #202020;
            --text-main: #D4D4D4;
            --border: rgba(255, 255, 255, 0.09);
            --accent-blue: #2E7CD1;
        }
        body { background-color: var(--bg-main); color: var(--text-main); display: flex; height: 100vh; margin: 0; }
        .sidebar { width: 260px; background: var(--bg-sidebar); border-right: 1px solid var(--border); padding: 20px; }
        .card { background: #252525; border: 1px solid var(--border); padding: 16px; margin-bottom: 20px; }"""

if __name__ == "__main__":
    patch_css("1783679346_Checklist.html", CHECKLIST_CSS)
    patch_css("1783679354_dashboard.html", DASHBOARD_CSS)