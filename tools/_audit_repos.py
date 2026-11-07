# -*- coding: utf-8 -*-
"""盘点所有仓库：文件结构、元数据、缺口。只读，不写任何东西。"""
import json, os, urllib.request

TOKEN = os.environ['GH_TOKEN']
API = 'https://api.github.com'


def get(url):
    r = urllib.request.Request(url)
    r.add_header('Authorization', 'Bearer ' + TOKEN)
    r.add_header('Accept', 'application/vnd.github+json')
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read().decode() or '{}')
    except Exception as e:
        return {'_err': str(e)}


repos = get(API + '/user/repos?per_page=100&sort=pushed&affiliation=owner')
rows = []
for r in repos:
    name = r['name']
    tree = get('%s/repos/604665656/%s/git/trees/%s?recursive=1' % (API, name, r['default_branch']))
    paths = [t['path'] for t in tree.get('tree', [])] if 'tree' in tree else []
    low = [p.lower() for p in paths]
    info = {
        'name': name,
        'lang': r.get('language'),
        'private': r['private'],
        'desc': r.get('description') or '',
        'topics': r.get('topics') or [],
        'pushed': r['pushed_at'][:10],
        'size_kb': r['size'],
        'files': len(paths),
        'truncated': tree.get('truncated', False),
        'readme': any(p.startswith('readme') for p in low),
        'license': any(p.startswith(('license', 'licence')) for p in low),
        'gitignore': '.gitignore' in low,
        'tests': any('test' in p for p in low),
        'pages': r['has_pages'],
        'issues': r['open_issues_count'],
        'top': [p for p in paths if '/' not in p][:14],
    }
    rows.append(info)

with open('_audit.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print('%-28s %-5s %-6s %-5s %-4s %-4s %-4s %-4s %-4s %s' % ('repo', 'lang', 'files', 'desc', 'RD', 'LIC', 'GI', 'TST', 'TPC', 'top'))
for i in rows:
    print('%-28s %-5s %-6d %-5s %-4s %-4s %-4s %-4s %-4d %s' % (
        i['name'], (i['lang'] or '-')[:5], i['files'], 'Y' if i['desc'] else '-',
        'Y' if i['readme'] else '-', 'Y' if i['license'] else '-',
        'Y' if i['gitignore'] else '-', 'Y' if i['tests'] else '-',
        len(i['topics']), ','.join(i['top'][:6])))
