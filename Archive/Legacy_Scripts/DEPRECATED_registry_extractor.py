cat << 'EOF' > "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Figma Sync/ui.html"
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Inter, sans-serif; padding: 12px; background: #1e1e1e; color: #fff; margin: 0; }
    button { width: 100%; padding: 10px; margin-bottom: 8px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
    .btn-extract { background: #0d99ff; color: #fff; }
    textarea { width: 100%; height: 210px; background: #2c2c2c; color: #00ff66; border: 1px solid #444; border-radius: 4px; font-family: monospace; font-size: 11px; box-sizing: border-box; padding: 8px; }
  </style>
</head>
<body>
  <button class="btn-extract" onclick="extract()">1. Extraer Registry Completo (JSON)</button>
  <textarea id="output" placeholder="El nuevo registry_seed.json aparecerá aquí..."></textarea>

  <script>
    function extract() {
      parent.postMessage({ pluginMessage: { type: 'export-full-registry' } }, '*');
    }

    window.onmessage = (event) => {
      const msg = event.data.pluginMessage;
      if (msg && msg.type === 'registry-generated') {
        document.getElementById('output').value = JSON.stringify(msg.data, null, 2);
      }
    };
  </script>
</body>
</html>
EOF

cat << 'EOF' > "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Figma Sync/code.js"
figma.showUI(__html__, { width: 440, height: 320 });

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'export-full-registry') {
    const registry = {};
    let scannedCount = 0;

    function scanNode(node) {
      if (node.name.startsWith('[VANTAGE]')) {
        const cleanKey = node.name.replace('[VANTAGE]', '').trim();
        registry[cleanKey] = node.id;
        scannedCount++;
      }
      if ('children' in node) {
        for (const child of node.children) {
          scanNode(child);
        }
      }
    }

    for (const pageNode of figma.currentPage.children) {
      scanNode(pageNode);
    }

    figma.ui.postMessage({
      type: 'registry-generated',
      data: registry
    });

    figma.notify(`VANTAGE Extractor: ${scannedCount} nodos registrados.`);
  }
};
EOF
