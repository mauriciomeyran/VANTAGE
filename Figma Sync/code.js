"use strict";
// VANTAGE CV Sync - Improved Font Loading & Payload Handling
// Fix for Figma Plugin Sync & Script Automation
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
figma.ui.onmessage = (msg) => __awaiter(void 0, void 0, void 0, function* () {
    var _a;
    if (msg.type === 'sync-nodes') {
        let nodesToUpdate = msg.payload;
        // Handle wrapped payload if passed
        if (!Array.isArray(nodesToUpdate) && nodesToUpdate.nodes) {
            nodesToUpdate = nodesToUpdate.nodes;
        }
        else if (Array.isArray(nodesToUpdate) && ((_a = nodesToUpdate[0]) === null || _a === void 0 ? void 0 : _a.nodes)) {
            nodesToUpdate = nodesToUpdate[0].nodes;
        }
        let updatedCount = 0;
        let errors = [];
        for (const item of nodesToUpdate) {
            if (!item.id || item.characters === undefined)
                continue;
            const node = figma.getNodeById(item.id);
            if (node && node.type === "TEXT") {
                try {
                    // Handle font loading per character segment or root fontName
                    if (node.fontName !== figma.mixed) {
                        yield figma.loadFontAsync(node.fontName);
                    }
                    else {
                        // If node has mixed fonts, load all unique fonts in range
                        const len = node.characters.length;
                        for (let i = 0; i < len; i++) {
                            yield figma.loadFontAsync(node.getRangeFontName(i, i + 1));
                        }
                    }
                    // Update text content cleanly
                    node.characters = item.characters;
                    updatedCount++;
                }
                catch (err) {
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
});
