#!/bin/zsh
# clean_caches.sh — Limpieza de cachés de apps (Mac)
# NO toca estado de sesión (logins, LocalStorage) — solo caché regenerable.

(
unsetopt NOMATCH 2>/dev/null
echo "Iniciando limpieza optimizada de aplicaciones..."

# --- Navegadores ---
rm -rf "$HOME/Library/Caches/Google/Chrome"
rm -rf "$HOME/Library/Application Support/Google/Chrome/Default/Application Cache"
rm -rf "$HOME/Library/Caches/com.apple.Safari"
rm -rf "$HOME/Library/Containers/com.apple.Safari.WebApp/Data/Library/Caches"
rm -rf "$HOME/Library/Caches/Firefox"
rm -rf "$HOME/Library/Caches/com.microsoft.edgemac"
rm -rf "$HOME/Library/Application Support/Microsoft Edge/Default/Application Cache"

# --- Mensajería ---
rm -rf "$HOME/Library/Containers/desktop.WhatsApp/Data/Library/Caches"
rm -rf "$HOME/Library/Group Containers/group.com.tencent.xinWeChat/Library/Caches"
rm -rf "$HOME/Library/Group Containers/742FA4BM87.ru.keepcoder.Telegram/Library/Caches"
rm -rf "$HOME/Library/Application Support/Telegram Desktop/tdata/user_data/cache"

# --- IA / dev tools ---
rm -rf "$HOME/.chatgpt"
rm -rf "$HOME/Library/Caches/com.openai.chat"
rm -rf "$HOME"/.ollama/history*
rm -rf "$HOME/.lmstudio/logs"
rm -rf "$HOME/.npm/_cacache"
rm -rf "$HOME/.cursor/User/workspaceStorage"
rm -rf "$HOME/Library/Application Support/Code/Cache"
rm -rf "$HOME/Library/Application Support/Code/CachedData"

# --- Comms / productividad ---
rm -rf "$HOME/Library/Caches/com.hnc.Discord"
rm -rf "$HOME/Library/Caches/com.tinyspeck.slackmacgap"
rm -rf "$HOME/Library/Application Support/com.raycast-x.macos/Cache"

# --- Diseño ---
rm -rf "$HOME/Library/Caches/com.figma.Desktop"
rm -rf "$HOME/Library/Application Support/Figma/Cache"
rm -rf "$HOME/Library/Application Support/Figma/GPUCache"
rm -rf "$HOME/Library/Application Support/Adobe/Common/Media Cache Files"
rm -rf "$HOME/Library/Caches/com.adobe."*

# --- Notion (solo caché, sin Local Storage) ---
rm -rf "$HOME/Library/Application Support/Notion/Cache"

# --- Comet ---
rm -rf "$HOME/Library/Application Support/Comet/Cache"
rm -rf "$HOME/Library/Application Support/Comet/GPUCache"

echo "Limpieza completada exitosamente."
)
