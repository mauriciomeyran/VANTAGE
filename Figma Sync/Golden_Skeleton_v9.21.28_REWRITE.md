### 12.2 CANON:OUTPUT-CONTRACT-002
Golden Skeleton
Use this exact sequence of IDs for any Figma-destined output.
- ID Header Sample: ###### figma_text_id
- KeySlots: 2:4 (Name), 2:5 (Headline), 2:9 (Profile), 2:14-18 (Skills), 2:22+ (Experience).
- Rule: If the skeleton changes in Figma, this record must be updated before the next CV-B run.
- Nota de orden: la secuencia de este bloque es narrativa (Compañía → Rol → Fecha → Bullets), NO el orden de escritura del registry_seed.json (que agrupa por parent_frame). El registry sigue siendo la SSOT de IDs numéricos (CANON:OUTPUT-CONTRACT-003); este documento es la capa de lectura/auditoría humana sobre esos mismos IDs.
---
```json
###### [figma_text_id](2:4)
**[NOMBRE COMPLETO]**

###### [figma_text_id](2:5)
**[TITULO DEL PUESTO | SUBTITULO O ESPECIALIDAD]**

###### [figma_text_id](8:56)
[UBICACION, CIUDAD]

###### [figma_text_id](8:57)
 | [TELEFONO]

###### [figma_text_id](8:58)
 | [CORREO ELECTRONICO]

###### [figma_text_id](8:62)
[ENLACE LINKEDIN]

###### [figma_text_id](8:63)
 | [ENLACE PORTAFOLIO]

###### [figma_text_id](2:7)
**PERFIL PROFESIONAL**

###### [figma_text_id](2:9)
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

###### [figma_text_id](3:13)
Lorem ipsum dolor sit amet, consectetur adipiscing elit: **[METRICA_1]** lorem ipsum dolor sit amet; **[METRICA_2]** lorem ipsum dolor sit amet; **[METRICA_3]** lorem ipsum dolor sit amet in **[CANTIDAD]** países. Lorem ipsum: **[METRICA_4]** lorem ipsum · **[METRICA_5]** lorem ipsum dolor sit amet.

###### [figma_text_id](2:10)
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:12)
**HABILIDADES CLAVE**

###### [figma_text_id](2:14)
**[CATEGORIA_HABILIDAD_1]:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore.

###### [figma_text_id](2:15)
**[CATEGORIA_HABILIDAD_2]:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore.

###### [figma_text_id](2:16)
**[CATEGORIA_HABILIDAD_3]:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore.

###### [figma_text_id](2:17)
**[CATEGORIA_HABILIDAD_4]:** Herramienta 1, Herramienta 2, Herramienta 3, Herramienta 4, Herramienta 5.

###### [figma_text_id](2:18)
**[CATEGORIA_IDIOMAS]:** Idioma 1 (Nivel) e Idioma 2 (Nivel).

###### [figma_text_id](2:20)
**EXPERIENCIA PROFESIONAL**

###### [figma_text_id](2:22)
**[NOMBRE EMPRESA 1]**

###### [figma_text_id](10:218)
**[TITULO DEL PUESTO 1]**

###### [figma_text_id](10:219)
 | *[MM/AAAA - MM/AAAA]*

###### [figma_text_id](2:25)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:26)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:27)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:28)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:32)
**[NOMBRE EMPRESA 2]**

###### [figma_text_id](4:17)
**[TITULO DEL PUESTO 2]**

###### [figma_text_id](4:18)
 | *[AAAA - AAAA]*

###### [figma_text_id](2:35)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:36)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:37)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:39)
**[NOMBRE EMPRESA 3]**

###### [figma_text_id](4:21)
**[TITULO DEL PUESTO 3]**

###### [figma_text_id](4:22)
 | *[AAAA - AAAA]*

###### [figma_text_id](2:42)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:43)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua (**[METRICA_PORCENTAJE]**).

###### [figma_text_id](2:44)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua (**[METRICA_PORCENTAJE]**).

###### [figma_text_id](3:9)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](3:2)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:46)
**[NOMBRE EMPRESA 4]**

###### [figma_text_id](4:25)
**[TITULO DEL PUESTO 4]**

###### [figma_text_id](4:26)
 | *[AAAA - AAAA]*

###### [figma_text_id](2:49)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](2:50)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua (**[METRICA_1]** / **[METRICA_2]**).

###### [figma_text_id](2:51)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](10:186)
**[NOMBRE EMPRESA 5]**

###### [figma_text_id](10:188)
**[TITULO DEL PUESTO 5A]**

###### [figma_text_id](10:189)
 | *[AAAA - AAAA]*

###### [figma_text_id](10:191)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](10:192)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](10:193)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](10:195)
**[TITULO DEL PUESTO 5B]**

###### [figma_text_id](10:196)
 | *[AAAA - AAAA]*

###### [figma_text_id](10:198)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

###### [figma_text_id](10:154)
**FORMACIÓN ACADÉMICA**

###### [figma_text_id](10:158)
**[GRADO O TITULO ACADEMICO 1]**

###### [figma_text_id](10:159)
 | *[AAAA - AAAA]*

###### [figma_text_id](10:161)
[INSTITUCION / UNIVERSIDAD 1]

###### [figma_text_id](10:164)
**[DIPLOMADO O CURSO ACADEMICO 2]** 

###### [figma_text_id](10:165)
| *[AAAA]*

###### [figma_text_id](10:167)
[INSTITUCION / FACULTAD 2]

###### [figma_text_id](10:213)
**CURSOS Y CERTIFICACIONES**

###### [figma_text_id](10:202)
[NOMBRE DEL CURSO 1]

###### [figma_text_id](10:203)
 | *[AAAA]*

###### [figma_text_id](10:204)
[PLATAFORMA / INSTITUCION]

###### [figma_text_id](10:207)
[NOMBRE DEL CURSO 2]

###### [figma_text_id](10:208)
 | *[AAAA]*

###### [figma_text_id](10:209)
[INSTITUCION / UBICACION]
```
