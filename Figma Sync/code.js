// VANTAGE Registry V2 — Resolver Layer V1
// Resolución por ID crudo O(1) vía registry_seed.json
// Deprecado: búsqueda semántica por nombre de capa (findAll)

const REGISTRY = {"HEADER_NAME":"2:4","SEC_PERFIL_PROFESIONAL_TITLE":"2:7","SEC_PERFIL_PROFESIONAL_BULLET_1":"2:9","SEC_HABILIDADES_CLAVE_TITLE":"2:12","SEC_HABILIDADES_CLAVE_BULLET_1":"2:14","SEC_EXPERIENCIA_PROFESIONAL_TITLE":"2:20","EXP_L_OR_AL_LUXE_M_XICO_COMPANY":"2:22","EXP_L_OR_AL_LUXE_M_XICO_BULLET_1":"2:25","EXP_BISONTE_EXPERIENTIAL_MARKETING_COMPANY":"2:32","EXP_BISONTE_EXPERIENTIAL_MARKETING_BULLET_1":"2:35","EXP_LEVI_STRAUSS___CO___DOCKERS__COMPANY":"2:39","EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_1":"2:42","EXP_A_ROPOSTALE_COMPANY":"2:46","EXP_A_ROPOSTALE_BULLET_1":"2:49","EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__COMPANY":"2:54","EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_1":"2:57","SEC_FORMACION_ACADEMICA_TITLE":"2:62","EDU_UNAM_ARTES":"2:64","SEC_CURSOS_Y_CERTIFICACIONES_TITLE":"2:67","CERT_AUTOCAD":"2:69","EXP_L_OR_AL_LUXE_M_XICO_ROLE":"2:23","EXP_BISONTE_EXPERIENTIAL_MARKETING_ROLE":"2:33","EXP_LEVI_STRAUSS___CO___DOCKERS__ROLE":"2:40","EXP_A_ROPOSTALE_ROLE":"2:47","EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__ROLE":"2:55","HEADER_SUBTITLE":"2:5","SEC_HABILIDADES_CLAVE_BULLET_2":"2:15","EXP_L_OR_AL_LUXE_M_XICO_BULLET_2":"2:26","EXP_BISONTE_EXPERIENTIAL_MARKETING_BULLET_2":"2:36","EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_2":"2:43","EXP_A_ROPOSTALE_BULLET_2":"2:50","EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_2":"2:58","EDU_UNAM_DIPLOMADO":"2:65","CERT_ALDO":"2:70","SEC_PERFIL_PROFESIONAL_BULLET_2":"3:13","SEC_HABILIDADES_CLAVE_BULLET_3":"2:16","EXP_L_OR_AL_LUXE_M_XICO_BULLET_3":"2:27","EXP_BISONTE_EXPERIENTIAL_MARKETING_BULLET_3":"2:37","EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_3":"2:44","EXP_A_ROPOSTALE_BULLET_3":"2:51","EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_3":"2:59","SEC_PERFIL_PROFESIONAL_BULLET_3":"2:10","SEC_HABILIDADES_CLAVE_BULLET_4":"2:17","EXP_L_OR_AL_LUXE_M_XICO_BULLET_4":"2:28","EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_4":"3:9","EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_4":"2:60","SEC_HABILIDADES_CLAVE_BULLET_5":"2:18"};

figma.showUI(__html__, { width: 400, height: 280 });

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'execute-sync') {
    const data = msg.data;
    let successCount = 0;
    let missingNodes = [];

    for (const [key, item] of Object.entries(data)) {
      // Resolver: key puede ser VANTAGE_KEY semántica o ID crudo directo
      // Si viene del flujo Markdown (figma_text_id), key YA es ID crudo → uso directo
      // Si viene del flujo JSON por KEY semántica → resolver vía REGISTRY
      const rawId = REGISTRY[key] || key;
      const node = figma.getNodeById(rawId);

      if (!node || node.type !== 'TEXT') {
        missingNodes.push(key);
        continue;
      }

      try {
        let baseFont;
        if (node.fontName === figma.mixed) {
          const firstFont = node.getRangeFontName(0, 1);
          baseFont = { family: firstFont.family, style: "Regular" };
        } else {
          baseFont = node.fontName;
          if (baseFont && (baseFont.style === "Bold" || baseFont.style === "Medium" || baseFont.style === "SemiBold") && item.boldRanges && item.boldRanges.length > 0) {
            baseFont = { family: baseFont.family, style: "Regular" };
          }
        }

        try {
          await figma.loadFontAsync(baseFont);
        } catch (fontErr) {
          const backupFont = node.fontName === figma.mixed ? node.getRangeFontName(0, 1) : node.fontName;
          baseFont = backupFont;
          await figma.loadFontAsync(baseFont);
        }

        // Inyección limpia de caracteres
        node.characters = item.text;
        
        // Formateo quirúrgico de rangos en negrita
        if (item.boldRanges && item.boldRanges.length > 0) {
          const boldFont = { family: baseFont.family, style: "Bold" };
          try {
            await figma.loadFontAsync(boldFont);
            for (const range of item.boldRanges) {
              if (range.start < node.characters.length && range.end <= node.characters.length) {
                node.setRangeFontName(range.start, range.end, boldFont);
              }
            }
          } catch (err) {
            try {
              const mediumFont = { family: baseFont.family, style: "Medium" };
              await figma.loadFontAsync(mediumFont);
              for (const range of item.boldRanges) {
                if (range.start < node.characters.length && range.end <= node.characters.length) {
                  node.setRangeFontName(range.start, range.end, mediumFont);
                }
              }
            } catch (innerErr) {
              console.error(`Error de asignación de peso en: ${baseFont.family}`);
            }
          }
        }
        successCount++;
      } catch (err) {
        console.error(`Fallo crítico en nodo semántico ${vantageKey}:`, err);
      }
    }

    if (missingNodes.length > 0) {
      console.warn("Keys no encontradas en el lienzo actual:", missingNodes);
    }

    figma.notify(`VANTAGE Sync: ${successCount} nodos actualizados vía Registry V2 (ID crudo).${missingNodes.length > 0 ? ` Keys sin resolver: ${missingNodes.length}` : ''}`);
    figma.closePlugin();
  }
};