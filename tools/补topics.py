# -*- coding: utf-8 -*-
"""只补 topics。PATCH /repos 会静默忽略 topics，必须走 PUT /repos/{o}/{r}/topics。"""
import json, os, re, urllib.request, urllib.error

TOKEN = os.environ['GH_TOKEN']
OWNER = '604665656'
API = 'https://api.github.com'


def call(url, method='GET', data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header('Authorization', 'Bearer ' + TOKEN)
    r.add_header('Accept', 'application/vnd.github+json')
    r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:200]}


# 从 建全部看板.py 里读 TOPICS，避免两份定义漂移
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '建全部看板.py'), encoding='utf-8').read()
block = re.search(r'TOPICS = (\{.*?\n\})', src, re.S).group(1)
TOPICS = eval(block)

ok = bad = 0
for name, tp in TOPICS.items():
    # 并集写入：保留仓库上已有的 topics，只追加，绝不覆盖
    cur = call('%s/repos/%s/%s/topics' % (API, OWNER, name))
    prev = cur.get('names') or []
    merged = prev + [x for x in tp if x not in prev]
    r = call('%s/repos/%s/%s/topics' % (API, OWNER, name), 'PUT', {'names': merged})
    got = r.get('names') if isinstance(r, dict) else None
    if got is None:
        bad += 1
        print('  FAIL %-28s %s' % (name, json.dumps(r, ensure_ascii=False)[:120]))
    else:
        ok += 1
        added = len([x for x in got if x not in prev])
        print('  ok   %-28s %d (+%d)' % (name, len(got), added))
print('== %d ok / %d fail ==' % (ok, bad))
