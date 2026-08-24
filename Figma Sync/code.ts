// VANTAGE CV Sync - Improved Font Loading & Payload Handling
// Fix for Figma Plugin Sync & Script Automation

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'sync-nodes') {
    let nodesToUpdate = msg.payload;

    // Handle wrapped payload if passed
    if (!Array.isArray(nodesToUpdate) && nodesToUpdate.nodes) {
      nodesToUpdate = nodesToUpdate.nodes;
    } else if (Array.isArray(nodesToUpdate) && nodesToUpdate[0]?.nodes) {
      nodesToUpdate = nodesToUpdate[0].nodes;
    }

    let updatedCount = 0;
    let errors = [];

    for (const item of nodesToUpdate) {
      if (!item.id || item.characters === undefined) continue;

      const node = figma.getNodeById(item.id);
      if (node && node.type === "TEXT") {
        try {
          // Handle font loading per character segment or root fontName
          if (node.fontName !== figma.mixed) {
            await figma.loadFontAsync(node.fontName as FontName);
          } else {
            // If node has mixed fonts, load all unique fonts in range
            const len = node.characters.length;
            for (let i = 0; i < len; i++) {
              await figma.loadFontAsync(node.getRangeFontName(i, i + 1) as FontName);
            }
          }

          // Update text content cleanly
          node.characters = item.characters;
          updatedCount++;
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : String(err);
          errors.push(`Failed node ${item.id}: ${errorMessage}`);
        }
      }
    }

    figma.ui.postMessage({
      type: 'sync-result',
      count: updatedCount,
      errors: errors
    });
  }
};
