#!/bin/zsh
# fetch_hashes.sh — Resuelve orphan hashes via Notion API REST
# Uso: zsh fetch_hashes.sh
source ~/.zshrc 2>/dev/null

TOKEN="${NOTION_API_KEY}"
ORPHAN_FILE="$HOME/output/orphan_page_ids.json"
TEMP_DIR="$HOME/output/hash_fetch_tmp"
INDEX_FILE="$HOME/output/entity_index_v2.json"
mkdir -p "$TEMP_DIR"

echo "Token: ${TOKEN:0:20}..."

ALL_IDS=$(python3 -c "import json; f=open('$ORPHAN_FILE'); d=json.load(f); print(' '.join(d['vantage']+d['archivo']))") 

TOTAL=$(echo "$ALL_IDS" | wc -w | tr -d ' ')
echo "Orphans: $TOTAL"

COUNT=0; RESOLVED=0
rm -f "$TEMP_DIR/resolved.tsv"

for PAGE_ID in $ALL_IDS; do
  COUNT=$((COUNT + 1))
  RESPONSE=$(curl -s "https://api.notion.com/v1/pages/${PAGE_ID}"     -H "Authorization: Bearer $TOKEN"     -H "Notion-Version: 2022-06-28")

  HASH=$(echo "$RESPONSE" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  props=d.get('properties',{})
  for k in ['hash','Hash','HASH']:
    if k in props:
      p=props[k]; t=p.get('type','')
      if t=='rich_text':
        arr=p.get('rich_text',[])
        if arr: print(arr[0]['plain_text']); sys.exit(0)
      elif t=='formula':
        v=p.get('formula',{})
        if 'string' in v: print(v['string']); sys.exit(0)
  print('__EMPTY__')
except: print('__ERROR__')
")

  echo "${PAGE_ID}|${HASH}" >> "$TEMP_DIR/resolved.tsv"
  if [[ "$HASH" != "__EMPTY__" && "$HASH" != __ERROR__* && -n "$HASH" ]]; then
    RESOLVED=$((RESOLVED + 1))
    echo "  OK [$COUNT/$TOTAL] ${PAGE_ID:0:8}... -> ${HASH:0:16}..."
  else
    echo "  -- [$COUNT/$TOTAL] ${PAGE_ID:0:8}... sin hash"
  fi
  sleep 0.35
done

echo ""
echo "Fetch: $RESOLVED/$TOTAL resueltos. Aplicando JSON..."

python3 - << PYEOF
import json, os
index_path = os.path.expanduser('~/output/entity_index_v2.json')
tsv_path = os.path.expanduser('~/output/hash_fetch_tmp/resolved.tsv')
with open(index_path) as f: idx = json.load(f)
resolved = {}
with open(tsv_path) as f:
  for line in f:
    line=line.strip()
    if '|' in line:
      pid,h=line.split('|',1)
      if h and h!='__EMPTY__' and not h.startswith('__ERROR__'): resolved[pid]=h
print(f'TSV hashes: {len(resolved)}')
lookup={e['page_id']:e for e in idx['entities']}
patched=0
for pid,h in resolved.items():
  if pid in lookup:
    e=lookup[pid]; e['entity_id']=f'TRACKER:H_{h[:16]}'; e['canonical_id']=h; e['hash']=h; patched+=1
entities=list(lookup.values()); total=len(entities)
has_hash=sum(1 for e in entities if not e['entity_id'].startswith('TRACKER:U_'))
orphans=total-has_hash; hash_cov=round(has_hash/total,4)
idx['entities']=entities; idx['metrics']['hash_coverage']=hash_cov; idx['metrics']['orphan_candidates']=orphans
with open(index_path,'w') as f: json.dump(idx,f,indent=2,ensure_ascii=False)
print(f'Patched:{patched} | Coverage:{has_hash}/{total} ({hash_cov*100:.1f}%) | Orphans:{orphans}')
PYEOF

echo "Listo — entity_index_v2.json actualizado."
