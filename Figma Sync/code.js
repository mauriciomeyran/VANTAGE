const REGISTRY = {
  "HEADER": "2:4",
  "HEADER_BRIEF": "2:5",
  "HEADER_CONTACT": "4:39",
  "HEADER_LINK": "4:40",
  "SEC_PERFIL_PROFESIONAL_TITLE": "2:7",
  "SEC_PERFIL_PROFESIONAL_BULLET_1": "2:9",
  "SEC_PERFIL_PROFESIONAL_BULLET_2": "3:13",
  "SEC_PERFIL_PROFESIONAL_BULLET_3": "2:10",
  "SEC_HABILIDADES_CLAVE_TITLE": "2:12",
  "SEC_HABILIDADES_CLAVE_BULLET_1": "2:14",
  "SEC_HABILIDADES_CLAVE_BULLET_2": "2:15",
  "SEC_HABILIDADES_CLAVE_BULLET_3": "2:16",
  "SEC_HABILIDADES_CLAVE_BULLET_4": "2:17",
  "SEC_HABILIDADES_CLAVE_BULLET_5": "2:18",
  "SEC_EXPERIENCIA_PROFESIONAL_TITLE": "2:20",
  "EXP_L_OR_AL_LUXE_M_XICO_COMPANY": "2:22",
  "EXP_L_OR_AL_LUXE_M_XICO_ROLE": "2:23",
  "EXP_L_OR_AL_LUXE_M_XICO_YEARS": "4:14",
  "EXP_L_OR_AL_LUXE_M_XICO_BULLET_1": "2:25",
  "EXP_L_OR_AL_LUXE_M_XICO_BULLET_2": "2:26",
  "EXP_L_OR_AL_LUXE_M_XICO_BULLET_3": "2:27",
  "EXP_L_OR_AL_LUXE_M_XICO_BULLET_4": "2:28",
  "EXP_BISONTE_EXPERIENTIAL_MARKETING_COMPANY": "2:32",
  "EXP_BISONTE_EXPERIENTIAL_MARKETING_ROLE": "4:17",
  "EXP_BISONTE_EXPERIENTIAL_MARKETING_YERAS": "4:18",
  "EXP_BISONTE_EXPERIENTIAL_MARKETING_BULLET_1": "2:35",
  "EXP_BISONTE_EXPERIENTIAL_MARKETING_BULLET_2": "2:36",
  "EXP_BISONTE_EXPERIENTIAL_MARKETING_BULLET_3": "2:37",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__COMPANY": "2:39",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__ROLE": "4:21",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__YEARS": "4:22",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_1": "2:42",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_2": "2:43",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_3": "2:44",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_4": "3:9",
  "EXP_LEVI_STRAUSS___CO___DOCKERS__BULLET_5": "3:2",
  "EXP_A_ROPOSTALE_COMPANY": "2:46",
  "EXP_A_ROPOSTALE_ROLE": "4:25",
  "EXP_A_ROPOSTALE_YEARS": "4:26",
  "EXP_A_ROPOSTALE_BULLET_1": "2:49",
  "EXP_A_ROPOSTALE_BULLET_2": "2:50",
  "EXP_A_ROPOSTALE_BULLET_3": "2:51",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__COMPANY": "2:54",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__ROLE 1": "4:29",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__YEARS 1": "4:30",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_1": "2:57",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_2": "2:58",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_3": "2:59",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__ROLE 2": "4:33",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__YEARS 2": "4:34",
  "EXP_EL_PALACIO_DE_HIERRO__ALDO_GROUP__BULLET_4": "4:9",
  "SEC_FORMACION_ACADEMICA_TITLE": "2:62",
  "EDU_UNAM_ARTES": "2:64",
  "EDU_UNAM_DIPLOMADO": "2:65",
  "SEC_CURSOS_Y_CERTIFICACIONES_TITLE": "2:67",
  "CERT_AUTOCAD": "2:69",
  "CERT_ALDO": "2:70"
};

figma.showUI(__html__, { width: 440, height: 320 });

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'execute-sync') {
    const data = msg.data;
    let successCount = 0;
    let missingNodes = [];

    for (const [key, item] of Object.entries(data)) {
      let rawId = REGISTRY[key];
      let node = rawId ? figma.getNodeById(rawId) : null;

      if (!node) {
        const fullTagName = `[VANTAGE] ${key}`;
        node = figma.currentPage.findOne(n => n.name === fullTagName || n.name === key);
      }

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
        } catch (fErr) {
          baseFont = node.getRangeFontName(0, 1);
          await figma.loadFontAsync(baseFont);
        }

        node.fontName = baseFont;
        node.characters = item.text;

        if (item.boldRanges && item.boldRanges.length > 0) {
          const boldFont = { family: baseFont.family, style: "Bold" };
          try {
            await figma.loadFontAsync(boldFont);
            for (const range of item.boldRanges) {
              if (range.start < node.characters.length && range.end <= node.characters.length) {
                node.setRangeFontName(range.start, range.end, boldFont);
              }
            }
          } catch (e) {
            console.error(`Error asignando bold en ${key}:`, e);
          }
        }
        successCount++;
      } catch (err) {
        console.error(`Fallo en nodo ${key}:`, err);
      }
    }

    figma.notify(`VANTAGE Sync: ${successCount} nodos actualizados.${missingNodes.length > 0 ? ` Faltantes: ${missingNodes.length}` : ''}`);
    figma.closePlugin();
  }
};
