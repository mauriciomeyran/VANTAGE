figma.showUI(__html__, { width: 450, height: 500 });

// Función auxiliar para extraer y cargar todas las fuentes únicas del array de nodos antes de iterar
async function preloadFontsForNodes(textNodes: TextNode[]) {
  const fontSet = new Set<string>();
  const fontsToLoad: FontName[] = [];

  for (const node of textNodes) {
    if (node.fontName !== figma.mixed) {
      const key = `${node.fontName.family}-${node.fontName.style}`;
      if (!fontSet.has(key)) {
        fontSet.add(key);
        fontsToLoad.push(node.fontName);
      }
    } else {
      const len = node.characters.length;
      for (let i = 0; i < len; i++) {
        const font = node.getRangeFontName(i, i + 1) as FontName;
        const key = `${font.family}-${font.style}`;
        if (!fontSet.has(key)) {
          fontSet.add(key);
          fontsToLoad.push(font);
        }
      }
    }
  }

  // Cargar TODAS las fuentes en paralelo antes de mutar
  await Promise.all(fontsToLoad.map(font => figma.loadFontAsync(font)));
}

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'sync-nodes') {
    try {
      let rawData = msg.payload;
      
      // Parsear si el payload llegó como string JSON desde la UI
      if (typeof rawData === 'string') {
        rawData = JSON.parse(rawData);
      }

      const nodesToUpdate = Array.isArray(rawData) ? rawData : (rawData.nodes || []);
      
      // 1. Recolectar referencias a nodos válidos
      const targetNodes: { node: TextNode; characters: string }[] = [];
      for (const item of nodesToUpdate) {
        if (!item.id || item.characters === undefined) continue;
        const node = figma.getNodeById(item.id);
        if (node && node.type === "TEXT") {
          targetNodes.push({ node: node as TextNode, characters: item.characters });
        }
      }

      // 2. Precargar fuentes de todos los nodos en una sola llamada paralela
      await preloadFontsForNodes(targetNodes.map(t => t.node));

      // 3. Inyección síncrona inmediata
      let updatedCount = 0;
      for (const { node, characters } of targetNodes) {
        node.characters = characters;
        updatedCount++;
      }

      figma.ui.postMessage({
        type: 'sync-result',
        count: updatedCount,
        errors: []
      });

    } catch (err: any) {
      figma.ui.postMessage({
        type: 'sync-result',
        count: 0,
        errors: [err.message || String(err)]
      });
    }
  }
};
