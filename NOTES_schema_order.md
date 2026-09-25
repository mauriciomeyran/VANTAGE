# Comparación: qué columnas de Tracker (view ALL) existen en el Archivo Tracker
# y con qué nombre real. Las que NO existen se saltan en el SHOW.

# Tracker ALL → nombre real en Archivo Tracker
Fuente            → Fuente 1          (select, 9 opciones)
Next_Action       → Next_Action 1     (select, 11 opciones)
Fetch             → Fetch 1           (select, 3 opciones)
Score_Method      → Score_Method 1    (select, 2 opciones)
VM_Scope          → VM_Scope 1        (select, 2 opciones)
Prioridad_Auto    → Prioridad_Auto    (select, creado)
Outcome           → Outcome           (select, creado)
Figma             → Figma             (checkbox, creado)
PDF               → PDF               (checkbox, creado)
Archivar          → Archivar          (checkbox igual)
CV-A              → CV-A              (checkbox igual)
CV-B              → CV-B              (checkbox igual)
Figma             → Figma             (checkbox igual)
PDF               → PDF               (checkbox igual)
Postular          → Postular          (checkbox igual)
Interview         → Interview         (checkbox igual)
Positioning_Mode  → Positioning_Mode  (select igual)
Gate_Decision     → Gate_Decision     (select, 7 opciones)
Prioridad         → Prioridad         (select, 4 opciones)
Dedup_Flag        → Dedup_Flag        (select, 1 opción)
layer             → layer             (select igual)
Fuente 1          → Fuente 1          (select, 9 opciones)
Next_Action 1     → Next_Action 1     (select, 11 opciones)
Fetch 1           → Fetch 1           (select, 3 opciones)
Score_Method 1    → Score_Method 1    (select, 2 opciones)
VM_Scope 1        → VM_Scope 1        (select, 2 opciones)

# Campos que SÍ existen en Archivo Tracker (confirmados en el fetch)
# y que se incluyen en el SHOW:
"Fecha de creación",   # created_time, igual que Tracker
"layer",               # select L1/L2/L3
"Fuente 1",            # select → Tracker Fuente
"Optimizar",           # checkbox
"Interview",           # checkbox
"Archivar",            # checkbox
"Rol",                 # title
"Marca",               # text
"Holding",             # text
"Score",               # number
"Prioridad",           # select → Tracker Prioridad
"VM_Scope 1",          # select → Tracker VM_Scope
"Status",              # select (tracker tiene más opciones, pero es el campo)
"Next_Action 1",       # select → Tracker Next_Action
"Gate_Decision",       # select → Tracker Gate_Decision
"Last_Gate_Run",       # date
"hash",                # text
"Fetch 1",             # select → Tracker Fetch
"URL",                 # userDefined:URL
"Score_Method 1",      # select → Tracker Score_Method
"JD",                  # text
"JD_Quality",          # select
"Dedup_Flag",          # select
"JOB_ID",              # text
"Positioning_Mode",    # select
"NAD",                 # date
"Apply Date",          # date
"Interview_Date",      # date
"Rej Date",            # date
"Outcome",             # select → Tracker Outcome
"Contacto",            # text
"Notas",               # text
"Source_Type",         # select
"URL Notion",          # url
"Role_Class",          # select
"Files",               # file
"Prioridad_Auto",      # select → Tracker Prioridad_Auto
"CV-A",                # checkbox
"CV-B",                # checkbox
"Class_B_Last_Run",    # date
"Figma",               # checkbox → Tracker Figma
"PDF",                 # checkbox → Tracker PDF
