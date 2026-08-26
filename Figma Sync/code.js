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

// Cache de familias ya resueltas contra figma.listAvailableFontsAsync() en esta sesión del plugin —
// evita re-escanear la lista completa de fuentes del sistema por cada nodo con la misma familia.
const familyVariantCache = new Map();

// Resuelve dinámicamente el nombre de estilo real que Figma usa para "Regular" y "Bold"
// dentro de una familia dada. No asume literalmente "Regular"/"Bold" — varias familias
// usan variantes como "Book", "Roman", "SemiBold 700", etc. (Punto Crítico #1, cerrado).
function resolveFontVariants(family) {
    return __awaiter(this, void 0, void 0, function* () {
        if (familyVariantCache.has(family)) {
            return familyVariantCache.get(family);
        }
        const available = yield figma.listAvailableFontsAsync();
        const stylesInFamily = available
            .filter(f => f.fontName.family === family)
            .map(f => f.fontName.style);

        // Preferencia de nombre "Regular": exacto → alias comunes → primer estilo no-bold disponible.
        const REGULAR_ALIASES = ["Regular", "Book", "Roman", "Normal"];
        let regularStyle = stylesInFamily.find(s => REGULAR_ALIASES.includes(s));
        if (!regularStyle) {
            // Fallback: cualquier estilo que no contenga "bold"/"italic" en el nombre
            regularStyle = stylesInFamily.find(s => !/bold|italic/i.test(s)) || stylesInFamily[0];
        }

        // Preferencia de nombre "Bold": exacto → contiene "Bold" sin ser "Bold Italic" → cualquier match parcial.
        const BOLD_EXACT = "Bold";
        let boldStyle = stylesInFamily.find(s => s === BOLD_EXACT);
        if (!boldStyle) {
            boldStyle = stylesInFamily.find(s => /bold/i.test(s) && !/italic/i.test(s));
        }
        if (!boldStyle) {
            boldStyle = stylesInFamily.find(s => /bold/i.test(s));
        }
        const resolvedBoldMissing = !boldStyle;
        if (!boldStyle) {
            boldStyle = regularStyle;
        }

        // Preferencia de nombre "Italic": exacto → contiene "Italic" sin ser "Bold Italic" → cualquier match parcial.
        // Usado para fechas/períodos ("*February 2025 – March 2026*", convención del skill).
        const ITALIC_ALIASES = ["Italic", "Oblique"];
        let italicStyle = stylesInFamily.find(s => ITALIC_ALIASES.includes(s));
        if (!italicStyle) {
            italicStyle = stylesInFamily.find(s => /italic|oblique/i.test(s) && !/bold/i.test(s));
        }
        if (!italicStyle) {
            italicStyle = stylesInFamily.find(s => /italic|oblique/i.test(s));
        }
        const resolvedItalicMissing = !italicStyle;
        if (!italicStyle) {
            italicStyle = regularStyle;
        }

        // Variante combinada Bold+Italic — no se usa en el patrón actual del skill (Rol en
        // bold y Período en italic van en rangos separados, nunca solapados), pero se resuelve
        // por robustez ante un futuro caso de solape real.
        let boldItalicStyle = stylesInFamily.find(s => /bold/i.test(s) && /italic|oblique/i.test(s));
        const resolvedBoldItalicMissing = !boldItalicStyle;
        if (!boldItalicStyle) {
            boldItalicStyle = !resolvedBoldMissing ? boldStyle : (!resolvedItalicMissing ? italicStyle : regularStyle);
        }

        const result = {
            regular: { family, style: regularStyle },
            bold: { family, style: boldStyle },
            italic: { family, style: italicStyle },
            boldItalic: { family, style: boldItalicStyle },
            boldMissing: resolvedBoldMissing,
            italicMissing: resolvedItalicMissing,
            boldItalicMissing: resolvedBoldItalicMissing
        };
        familyVariantCache.set(family, result);
        return result;
    });
}

// Precarga TODAS las fuentes necesarias antes de mutar ningún nodo: la variante que el nodo
// ya tenía (comportamiento original, preservado) MÁS Regular y Bold resueltas dinámicamente
// para la familia del nodo, aunque el nodo no las use todavía (Punto Crítico #3, cerrado —
// antes solo se cargaba lo que el nodo ya tenía, por lo que aplicar bold nuevo lanzaba
// excepción de fuente no cargada).
function preloadFontsForNodes(textNodes) {
    return __awaiter(this, void 0, void 0, function* () {
        const fontSet = new Set();
        const fontsToLoad = [];
        const familiesSeen = new Set();

        function queueFont(font) {
            const key = `${font.family}-${font.style}`;
            if (!fontSet.has(key)) {
                fontSet.add(key);
                fontsToLoad.push(font);
            }
        }

        for (const node of textNodes) {
            if (node.fontName !== figma.mixed) {
                queueFont(node.fontName);
                familiesSeen.add(node.fontName.family);
            }
            else {
                const len = node.characters.length;
                for (let i = 0; i < len; i++) {
                    const font = node.getRangeFontName(i, i + 1);
                    queueFont(font);
                    familiesSeen.add(font.family);
                }
            }
        }

        // Cargar primero lo que los nodos ya tenían (comportamiento original intacto).
        yield Promise.all(fontsToLoad.map(font => figma.loadFontAsync(font)));

        // Resolver y precargar Regular + Bold + Italic + BoldItalic de cada familia vista,
        // para que la aplicación de boldRanges/italicRanges nunca falle por fuente no cargada.
        const variantResults = new Map();
        for (const family of familiesSeen) {
            const variants = yield resolveFontVariants(family);
            variantResults.set(family, variants);
            queueFont(variants.regular);
            queueFont(variants.bold);
            queueFont(variants.italic);
            queueFont(variants.boldItalic);
        }
        // Cargar las variantes recién resueltas que no estuvieran ya cubiertas arriba.
        yield Promise.all(fontsToLoad.map(font => figma.loadFontAsync(font)));

        return variantResults; // Map<family, {regular, bold, italic, boldItalic, ...Missing flags}>
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

            // 1. Recolectar referencias a nodos válidos — boldRanges, italicRanges y
            //    linkRanges opcionales, compatible con payloads que no los traigan.
            const targetNodes = [];
            for (const item of nodesToUpdate) {
                if (!item.id || item.characters === undefined)
                    continue;
                const node = figma.getNodeById(item.id);
                if (node && node.type === "TEXT") {
                    targetNodes.push({
                        node: node,
                        characters: item.characters,
                        boldRanges: Array.isArray(item.boldRanges) ? item.boldRanges : [],
                        italicRanges: Array.isArray(item.italicRanges) ? item.italicRanges : [],
                        linkRanges: Array.isArray(item.linkRanges) ? item.linkRanges : []
                    });
                }
            }

            // 2. Precargar fuentes de todos los nodos + variantes Regular/Bold resueltas dinámicamente.
            const variantsByFamily = yield preloadFontsForNodes(targetNodes.map(t => t.node));

            // 3. Inyección síncrona: texto → reset a Regular → aplicar boldRanges/italicRanges.
            let updatedCount = 0;
            const warnings = [];

            for (const { node, characters, boldRanges, italicRanges, linkRanges } of targetNodes) {
                // Familia base del nodo ANTES de reasignar characters (fontName puede ser
                // figma.mixed si el nodo ya traía bold/italic heredado de un run previo).
                const baseFamily = node.fontName !== figma.mixed
                    ? node.fontName.family
                    : node.getRangeFontName(0, 1).family;

                const variants = variantsByFamily.get(baseFamily);

                node.characters = characters;

                if (variants) {
                    // Reset completo a Regular — elimina cualquier bold/italic heredado de
                    // imports anteriores en texto que ya no debería llevarlo.
                    node.setRangeFontName(0, node.characters.length, variants.regular);

                    // Determinar, por carácter, si el rango es solo-bold, solo-italic, o
                    // ambos (solape) — para aplicar la variante correcta sin que una
                    // sobreescriba silenciosamente a la otra en la zona compartida.
                    const len = node.characters.length;
                    const boldMask = new Array(len).fill(false);
                    const italicMask = new Array(len).fill(false);

                    for (const range of boldRanges) {
                        const start = Math.max(0, range.start);
                        const end = Math.min(len, range.end);
                        for (let idx = start; idx < end; idx++) boldMask[idx] = true;
                    }
                    for (const range of italicRanges) {
                        const start = Math.max(0, range.start);
                        const end = Math.min(len, range.end);
                        for (let idx = start; idx < end; idx++) italicMask[idx] = true;
                    }

                    if (boldRanges.length > 0 && variants.boldMissing) {
                        warnings.push(`Nodo ${node.id}: familia "${baseFamily}" no tiene variante Bold real — boldRanges ignorados.`);
                    }
                    if (italicRanges.length > 0 && variants.italicMissing) {
                        warnings.push(`Nodo ${node.id}: familia "${baseFamily}" no tiene variante Italic real — italicRanges ignorados.`);
                    }

                    // Recorrer por segmentos contiguos del mismo tipo de estilo y aplicar una
                    // sola llamada por segmento (evita cientos de llamadas carácter-por-carácter).
                    let segStart = 0;
                    for (let idx = 1; idx <= len; idx++) {
                        const changed = idx === len ||
                            boldMask[idx] !== boldMask[segStart] ||
                            italicMask[idx] !== italicMask[segStart];
                        if (changed) {
                            const isB = boldMask[segStart] && !variants.boldMissing;
                            const isI = italicMask[segStart] && !variants.italicMissing;
                            let targetFont = variants.regular;
                            if (isB && isI) targetFont = variants.boldItalic;
                            else if (isB) targetFont = variants.bold;
                            else if (isI) targetFont = variants.italic;

                            if (targetFont !== variants.regular && segStart < idx) {
                                node.setRangeFontName(segStart, idx, targetFont);
                            }
                            segStart = idx;
                        }
                    }

                    // Aplicar hyperlinks reales (LinkedIn, Portfolio, etc.) — antes se
                    // descartaba la URL en ui.html y solo llegaba el texto plano.
                    for (const link of linkRanges) {
                        const start = Math.max(0, link.start);
                        const end = Math.min(len, link.end);
                        if (start < end && link.url) {
                            node.setRangeHyperlink(start, end, { type: "URL", value: link.url });
                        }
                    }
                } else {
                    warnings.push(`Nodo ${node.id}: no se pudo resolver familia tipográfica — texto actualizado sin control de estilo.`);
                }

                updatedCount++;
            }

            figma.ui.postMessage({
                type: 'sync-result',
                count: updatedCount,
                errors: warnings
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
