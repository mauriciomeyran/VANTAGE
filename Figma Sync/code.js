// Abrir modal de interfaz al ejecutar el plugin
figma.showUI(__html__, { width: 440, height: 360 });

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'sync-nodes') {
    const payload = msg.payload;
    let updatedCount = 0;

    for (const key in payload) {
      // Fallback: si key no está en REGISTRY, usar key cruda (ej. "2:5")
      const rawId = (typeof REGISTRY !== 'undefined' && REGISTRY[key]) ? REGISTRY[key] : key;
      const data = payload[key];

      try {
        const node = figma.getNodeById(rawId);
        if (node && node.type === 'TEXT') {
          // Cargar fuente base antes de mutar el texto
          await figma.loadFontAsync(node.fontName);
          
          node.characters = data.text;
          
          // Aplicar rangos de negrita
          if (data.boldRanges && Array.isArray(data.boldRanges)) {
            for (const range of data.boldRanges) {
              const currentFont = node.getRangeFontName(range.start, range.end);
              if (currentFont !== figma.mixed) {
                await figma.loadFontAsync({ family: currentFont.family, style: 'Bold' });
                node.setRangeFontName(range.start, range.end, { family: currentFont.family, style: 'Bold' });
              }
            }
          }
          updatedCount++;
        }
      } catch (err) {
        console.error(`Error actualizando nodo ${key} (${rawId}):`, err);
      }
    }

    figma.notify(`Sincronización finalizada: ${updatedCount} nodos actualizados.`);
  }
};
