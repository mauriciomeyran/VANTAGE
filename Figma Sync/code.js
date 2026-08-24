"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
figma.showUI(__html__, { width: 450, height: 500 });
// Función auxiliar para extraer y cargar todas las fuentes únicas del array de nodos antes de iterar
function preloadFontsForNodes(textNodes) {
    return __awaiter(this, void 0, void 0, function* () {
        const fontSet = new Set();
        const fontsToLoad = [];
        for (const node of textNodes) {
            if (node.fontName !== figma.mixed) {
                const key = `${node.fontName.family}-${node.fontName.style}`;
                if (!fontSet.has(key)) {
                    fontSet.add(key);
                    fontsToLoad.push(node.fontName);
                }
            }
            else {
                const len = node.characters.length;
                for (let i = 0; i < len; i++) {
                    const font = node.getRangeFontName(i, i + 1);
                    const key = `${font.family}-${font.style}`;
                    if (!fontSet.has(key)) {
                        fontSet.add(key);
                        fontsToLoad.push(font);
                    }
                }
            }
        }
        // Cargar TODAS las fuentes en paralelo antes de mutar
        yield Promise.all(fontsToLoad.map(font => figma.loadFontAsync(font)));
    });
}
figma.ui.onmessage = (msg) => __awaiter(void 0, void 0, void 0, function* () {
    if (msg.type === 'sync-nodes') {
        try {
            let rawData = msg.payload;
            // Parsear si el payload llegó como string JSON desde la UI
            if (typeof rawData === 'string') {
                rawData = JSON.parse(rawData);
            }
            const nodesToUpdate = Array.isArray(rawData) ? rawData : (rawData.nodes || []);
            // 1. Recolectar referencias a nodos válidos
            const targetNodes = [];
            for (const item of nodesToUpdate) {
                if (!item.id || item.characters === undefined)
                    continue;
                const node = figma.getNodeById(item.id);
                if (node && node.type === "TEXT") {
                    targetNodes.push({ node: node, characters: item.characters });
                }
            }
            // 2. Precargar fuentes de todos los nodos en una sola llamada paralela
            yield preloadFontsForNodes(targetNodes.map(t => t.node));
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
        }
        catch (err) {
            figma.ui.postMessage({
                type: 'sync-result',
                count: 0,
                errors: [err.message || String(err)]
            });
        }
    }
});
