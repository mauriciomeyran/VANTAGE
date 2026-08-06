#!/usr/bin/env python3
"""
clean_caches.py — Limpieza de cachés de apps (Mac)
No toca estado de sesión (logins, LocalStorage) — solo caché regenerable.
Reporta espacio liberado por ruta.
"""
import shutil
from pathlib import Path

HOME = Path.home()

PATHS = [
    # Navegadores
    "Library/Caches/Google/Chrome",
    "Library/Application Support/Google/Chrome/Default/Application Cache",
    "Library/Caches/com.apple.Safari",
    "Library/Containers/com.apple.Safari.WebApp/Data/Library/Caches",
    "Library/Caches/Firefox",
    "Library/Caches/com.microsoft.edgemac",
    "Library/Application Support/Microsoft Edge/Default/Application Cache",
    # Mensajería
    "Library/Containers/desktop.WhatsApp/Data/Library/Caches",
    "Library/Group Containers/group.com.tencent.xinWeChat/Library/Caches",
    "Library/Group Containers/742FA4BM87.ru.keepcoder.Telegram/Library/Caches",
    "Library/Application Support/Telegram Desktop/tdata/user_data/cache",
    # IA / dev tools
    ".chatgpt",
    "Library/Caches/com.openai.chat",
    ".lmstudio/logs",
    ".npm/_cacache",
    ".cursor/User/workspaceStorage",
    "Library/Application Support/Code/Cache",
    "Library/Application Support/Code/CachedData",
    # Comms / productividad
    "Library/Caches/com.hnc.Discord",
    "Library/Caches/com.tinyspeck.slackmacgap",
    "Library/Application Support/com.raycast-x.macos/Cache",
    # Diseño
    "Library/Caches/com.figma.Desktop",
    "Library/Application Support/Figma/Cache",
    "Library/Application Support/Figma/GPUCache",
    "Library/Application Support/Adobe/Common/Media Cache Files",
    # Notion (solo caché)
    "Library/Application Support/Notion/Cache",
    # Comet
    "Library/Application Support/Comet/Cache",
    "Library/Application Support/Comet/GPUCache",
]


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main():
    print("Iniciando limpieza optimizada de aplicaciones...\n")
    total_freed = 0
    for rel in PATHS:
        target = HOME / rel
        size = dir_size(target)
        if size == 0:
            continue
        try:
            if target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
            print(f"  ✓ {rel} — {human(size)} liberado")
            total_freed += size
        except Exception as e:
            print(f"  ✗ {rel} — error: {e}")

    print(f"\nLimpieza completada exitosamente. Total liberado: {human(total_freed)}")


if __name__ == "__main__":
    main()
