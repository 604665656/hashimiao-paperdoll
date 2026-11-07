# -*- coding: utf-8 -*-
"""一次性脚本：为仓库建 GitHub Projects 看板、建标签与议题、挂进项目"""
import json, os, sys, urllib.request

TOKEN = os.environ.get('GH_TOKEN', '')
OWNER = '604665656'
REPO = 'hashimiao-paperdoll'
API = 'https://api.github.com'
GQL = 'https://api.github.com/graphql'


def req(url, method='GET', data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header('Authorization', 'Bearer ' + TOKEN)
    r.add_header('Accept', 'application/vnd.github+json')
    r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:400]}


def gql(query, variables=None):
    return req(GQL, 'POST', {'query': query, 'variables': variables or {}})


viewer = gql('query{viewer{id login}}')['data']['viewer']
print('viewer', viewer['login'])

repo = req('%s/repos/%s/%s' % (API, OWNER, REPO))
rid = repo['node_id']

# 1. 建看板
existing = gql('query{user(login:"%s"){projectsV2(first:20){nodes{id title url number}}}}' % OWNER)
if 'data' not in existing:
    print('query fail', json.dumps(existing, ensure_ascii=False)[:300]); sys.exit(1)
titles = [(p['title'], p['id'], p['url']) for p in existing['data']['user']['projectsV2']['nodes']]
hit = [t for t in titles if t[0].startswith('哈士喵')]
if hit:
    pid, purl = hit[0][1], hit[0][2]
    print('reuse project', purl)
else:
    r = gql('''mutation($o:ID!,$t:String!){createProjectV2(input:{ownerId:$o,title:$t}){projectV2{id url number}}}''',
            {'o': viewer['id'], 't': '哈士喵纸娃娃台 · 路线图'})
    if '_error' in r or 'errors' in r:
        print('create failed', json.dumps(r, ensure_ascii=False)[:400]); sys.exit(1)
    p = r['data']['createProjectV2']['projectV2']
    pid, purl = p['id'], p['url']
    print('project', purl)

# 2. 关联仓库
lk = gql('mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){repository{name}}}',
         {'p': pid, 'r': rid})
print('link', 'ok' if 'data' in lk and lk.get('data') else json.dumps(lk, ensure_ascii=False)[:160])

# 3. 优先级字段
fields = gql('query($p:ID!){node(id:$p){... on ProjectV2{fields(first:30){nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}}', {'p': pid})
f = fields['data']['node']['fields']['nodes']
prio = [x for x in f if x and x.get('name') == '优先级']
if prio:
    pfid = prio[0]['id']
    opts = {o['name']: o['id'] for o in prio[0]['options']}
else:
    r = gql('''mutation($p:ID!){createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:"优先级",
      singleSelectOptions:[{name:"P0",color:RED,description:"现在就做"},
                           {name:"P1",color:ORANGE,description:"下一批"},
                           {name:"P2",color:GRAY,description:"有空再说"}]}){projectV2Field{... on ProjectV2SingleSelectField{id options{id name}}}}}''',
            {'p': pid})
    fld = r['data']['createProjectV2Field']['projectV2Field']
    pfid = fld['id']
    opts = {o['name']: o['id'] for o in fld['options']}
print('priority field', 'ok', list(opts))

# 4. 标签
want = [('素材', '1D76DB'), ('功能', '0E8A16'), ('发布', '5319E7')]
labels = {l['name']: l['name'] for l in req('%s/repos/%s/%s/labels?per_page=100' % (API, OWNER, REPO))}
for n, c in want:
    if n not in labels:
        req('%s/repos/%s/%s/labels' % (API, OWNER, REPO), 'POST', {'name': n, 'color': c})

# 5. 议题
issues = [
    ('补表情分件：眼 5 张 + 嘴 6 张', 'P0',
     '现有 8 张整头表情拆成眼睛层与嘴层，组合出 30 种。\n\n- 眼：E1 平静 / E2 眨眼 / E3 笑眼 / E4 闭眼 / E5 惊讶\n- 嘴：M1 闭嘴 / M2 微笑 / M3 张嘴 / M4 大笑 / M5 惊讶圆嘴 / M6 吐舌\n\n要求 1328×1776 透明、与 L03/L04/L05 完全重合、不许裁切。\n规格见 `素材交付/素材清单.md`，交完跑 `tools/体检.bat` 自检。', ['素材']),
    ('编辑器接入表情下拉（眼 × 嘴 组合）', 'P0',
     '在装扮面板加两个下拉：眼型、嘴型，替换 L03/L04/L05 的显示层，组合矩阵 5×6。\n需要同步写进存档与搭配码，旧方案要能兼容（缺省回落到 L03~L05）。', ['功能']),
    ('银时配饰整图上架', 'P1',
     '白卷发 + 和服 + 腰牌合成一张 1328×1776 透明整图，脸/眼镜/手/脚/尾巴留空。\n放进 `assets/单源版/02_配饰层/银时/配饰_假发与衣身.png`，再在 `js/parts.js` 的 suits 里加一条。', ['素材']),
    ('举牌道具与举手替换层', 'P1',
     '拆两件：`木牌.png`（只有牌子）+ `手_举起.png`（替换 L09）。\n道具层要能单独开关，木牌支持换文字。', ['素材', '功能']),
    ('八向帧扩展到表情/服装版本', 'P2',
     '现在八向帧是素体，换装与表情后对不上。需要按 8 向 × 4 帧 × 套数 重出，命名沿用 `N_p1.png`。', ['素材']),
    ('导出增强：APNG / GIF 循环动画', 'P2',
     '现在只能导雪碧图与单帧 PNG。八向帧模式直接导出可播放的循环动图，省掉手工拼。', ['功能']),
    ('一键加部件：入库产物自动写入 parts.js', 'P2',
     '`素材入库/out` 切好的图，自动缩放到目标画布、落到对应目录、更新槽位表，省掉手工对位。', ['功能']),
    ('Pages 上线检查：首屏说明与资源加载', 'P1',
     'Pages 已开启（main / 根目录）。需确认中文路径资源能加载、首屏给出使用说明、移动端可用。', ['发布']),
]

created = 0
for title, prio_name, body, labs in issues:
    ex = req('%s/repos/%s/%s/issues?state=all&per_page=100' % (API, OWNER, REPO))
    if isinstance(ex, list) and any(i.get('title') == title for i in ex):
        print('skip existing', title); continue
    it = req('%s/repos/%s/%s/issues' % (API, OWNER, REPO), 'POST',
             {'title': title, 'body': body, 'labels': labs})
    if '_error' in it:
        print('issue fail', title, it['_error'], it['_body'][:120]); continue
    add = gql('mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}',
              {'p': pid, 'c': it['node_id']})
    iid = add['data']['addProjectV2ItemById']['item']['id']
    if prio_name in opts:
        gql('''mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(
              input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}''',
            {'p': pid, 'i': iid, 'f': pfid, 'o': opts[prio_name]})
    created += 1
    print('issue+', title)

print('done, created', created, 'project', purl)
