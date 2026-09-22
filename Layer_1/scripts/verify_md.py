import re, sys

def verify(path):
    content = open(path, encoding='utf-8').read()
    lines = content.split('\n')
    issues = []

    for i, line in enumerate(lines):
        if line != line.rstrip():
            issues.append(f'L{i+1}: trailing whitespace -> {line!r}')

    for i, line in enumerate(lines):
        if re.match(r'^\*\*.+\*\*\s+$', line):
            issues.append(f'L{i+1}: bold con espacio final -> {line!r}')

    for i, line in enumerate(lines):
        if line.startswith('###### [figma_text_id]'):
            if i+1 < len(lines):
                nxt = lines[i+1]
                if re.search(r'^\s*\|?\s*\*[0-9]', nxt) or re.match(r'^\s*\|\s*\*', nxt):
                    if not nxt.startswith(' | *'):
                        issues.append(f'L{i+2}: nodo de periodo mal formado (debe iniciar " | *") -> {nxt!r}')

    for i, line in enumerate(lines):
        if line.startswith('###### [figma_text_id]'):
            if i+1 < len(lines) and lines[i+1] == '':
                if i+2 < len(lines) and (lines[i+2] == '' or lines[i+2].startswith('###### [figma_text_id]')):
                    issues.append(f'L{i+1}: nodo completamente vacio ("") -> usar un solo espacio " " en vez de string vacio')

    for i, line in enumerate(lines):
        if '[PENDING DATA]' in line:
            issues.append(f'L{i+1}: [PENDING DATA] prohibido en entrega final')

    return issues

if __name__ == '__main__':
    path = sys.argv[1]
    issues = verify(path)
    print(f'Issues encontrados: {len(issues)}')
    for x in issues:
        print(x)