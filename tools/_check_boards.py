# -*- coding: utf-8 -*-
"""只读核对：看板公开状态、关联仓库、议题与优先级。"""
import json, os, urllib.request

T = os.environ['GH_TOKEN']


def gql(q, v=None):
    r = urllib.request.Request('https://api.github.com/graphql',
                               data=json.dumps({'query': q, 'variables': v or {}}).encode(),
                               method='POST')
    r.add_header('Authorization', 'Bearer ' + T)
    r.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(r, timeout=60).read().decode())


Q = '''
query($o:String!){
  user(login:$o){
    projectsV2(first:30){
      nodes{
        number title public
        repositories(first:20){ nodes{ nameWithOwner } }
        items(first:40){
          totalCount
          nodes{
            content{ ... on Issue { title state } }
            fieldValues(first:12){
              nodes{ ... on ProjectV2ItemFieldSingleSelectValue { name } }
            }
          }
        }
      }
    }
  }
}
'''

r = gql(Q, {'o': os.environ.get('OWNER', '604665656')})
if 'data' not in r:
    print(json.dumps(r, ensure_ascii=False, indent=2)[:2000])
    raise SystemExit(1)

for p in sorted(r['data']['user']['projectsV2']['nodes'], key=lambda x: x['number']):
    print('#%s  %-34s public=%-5s repos=%d items=%d' %
          (p['number'], p['title'], p['public'], len(p['repositories']['nodes']), p['items']['totalCount']))
    for n in p['repositories']['nodes']:
        print('     repo: %s' % n['nameWithOwner'])
    for it in p['items']['nodes']:
        c = it.get('content') or {}
        pv = [f['name'] for f in it['fieldValues']['nodes'] if f.get('name')]
        print('     - %-46s %-8s %s' % ((c.get('title') or '?')[:46], c.get('state', ''), pv))
    print()
