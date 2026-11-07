# -*- coding: utf-8 -*-
"""删掉最早那个空的私人看板（@604665656's untitled project）。

安全闸：只删 items=0 且 repositories=0 的，非空一律跳过。
用法：export GH_TOKEN=... && python tools/_删空看板.py
"""
import json, os, urllib.request

T = os.environ['GH_TOKEN']


def gql(q, v=None):
    r = urllib.request.Request('https://api.github.com/graphql',
                               data=json.dumps({'query': q, 'variables': v or {}}).encode(),
                               method='POST')
    r.add_header('Authorization', 'Bearer ' + T)
    r.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(r, timeout=45).read().decode())


LIST = '''
query($o:String!){
  user(login:$o){
    projectsV2(first:30){
      nodes{ id number title public
             items(first:1){totalCount}
             repositories(first:1){totalCount} }
    }
  }
}
'''

r = gql(LIST, {'o': '604665656'})
if 'data' not in r:
    raise SystemExit('查询失败：%s' % json.dumps(r, ensure_ascii=False)[:300])

for p in r['data']['user']['projectsV2']['nodes']:
    print('#%s  %-34s public=%-5s items=%d repos=%d' % (
        p['number'], p['title'], p['public'],
        p['items']['totalCount'], p['repositories']['totalCount']))

target = [p for p in r['data']['user']['projectsV2']['nodes']
          if p['title'].endswith('untitled project')]
if not target:
    print('\n没有待删的空看板')
    raise SystemExit(0)

for p in target:
    if p['items']['totalCount'] or p['repositories']['totalCount']:
        print('\n跳过 #%s：非空' % p['number'])
        continue
    d = gql('mutation($p:ID!){deleteProjectV2(input:{projectId:$p}){projectV2{id title}}}', {'p': p['id']})
    print('\n删除 #%s ->' % p['number'], json.dumps(d, ensure_ascii=False)[:160])
