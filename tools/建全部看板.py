# -*- coding: utf-8 -*-
"""给账号下的其他仓库统一整理：补 topics、建看板、建真实议题。
幂等：看板按标题复用，议题按标题去重。
用法：set GH_TOKEN=... && python tools/建全部看板.py
"""
import json, os, urllib.request

TOKEN = os.environ['GH_TOKEN']
OWNER = '604665656'
API = 'https://api.github.com'
GQL = 'https://api.github.com/graphql'


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


def gql(q, v=None):
    return call(GQL, 'POST', {'query': q, 'variables': v or {}})


# ---------- topics ----------
TOPICS = {
    'wqn': ['game', 'html', 'single-file', 'idle-game', 'history', 'offline', 'canvas'],
    'qingcong-rhythm': ['rhythm-game', 'web-audio', 'canvas', 'music', 'game-engine', 'single-file'],
    'qishui-dashboard': ['python', 'dashboard', 'data-visualization', 'pyinstaller', 'local-first'],
    'qishui-music-automation': ['python', 'automation', 'growth', 'analytics', 'music'],
    'qishui-host': ['python', 'plugin-host', 'launcher', 'pyinstaller', 'desktop'],
    'qishui-core': ['python', 'library', 'plugin-system', 'core', 'sdk'],
    'qishui-plugin-example-hello': ['python', 'plugin', 'example', 'qishui'],
    'qishui-plugin-sync': ['python', 'plugin', 'sync', 'qishui'],
    'qishui-plugin-resident': ['python', 'plugin', 'daemon', 'qishui'],
    'qishui-plugin-review': ['python', 'plugin', 'review', 'qishui'],
    'qishui-plugin-publish': ['python', 'plugin', 'publishing', 'qishui'],
    'qishui-plugin-studio': ['python', 'plugin', 'editor', 'qishui'],
    'qishui-plugin-lyricvideo': ['python', 'plugin', 'video', 'ffmpeg', 'lyrics'],
    'qishui-plugin-revenue': ['python', 'plugin', 'analytics', 'revenue'],
    'qishui-plugin-export': ['python', 'plugin', 'audio', 'export'],
    'qishui-plugin-dupscan': ['python', 'plugin', 'text-dedup', 'lyrics'],
    'qishui-plugin-selftest': ['python', 'plugin', 'diagnostics', 'selftest'],
    'qishui-plugin-account': ['python', 'plugin', 'auth', 'account'],
    'qishui-plugin-board': ['python', 'plugin', 'dashboard', 'metrics'],
    'qishui-plugin-coldstart': ['python', 'plugin', 'growth', 'traffic'],
    'bili-relation-manager': ['electron', 'javascript', 'bilibili', 'desktop-app', 'automation'],
    'ruochen-toy-games': ['game', 'html', 'bilibili', 'music', 'matching', 'mini-game'],
    'skyworth-8s03-physkey': ['shell', 'android', 'adb', 'tv', 'keymap', 'hardware'],
    'live-copilot': ['javascript', 'ai', 'game', 'assistant', 'danmaku', 'vision'],
}

QISHUI = [n for n in TOPICS if n.startswith('qishui-')]

# ---------- 看板定义 ----------
# (标题, 简介, 关联仓库列表, 议题列表[(标题, 优先级, 正文, 仓库名, 标签)])
BOARDS = [
    ('wqn · 上下五千年 路线图', '单文件历史分支页游：构建、上线与内容扩展',
     ['wqn'], [
         ('开 Pages：用 build.js 产物发在线 demo', 'P1',
          '当前仓库只有源码与 `build.js`，没有可直接访问的构建产物。\n\n- 产物是单文件 HTML，适合直接上 Pages\n- 建议加一个 Action：push 时跑 `node build.js`，把产物推到 `gh-pages`\n- 上线后在 README 顶部挂链接', 'wqn', ['发布']),
         ('补 CI：push 时构建并校验产物体积', 'P2',
          '单文件页游最容易悄悄变大。\n\n- 构建后检查产物体积，超过阈值就提示\n- 顺便跑一次语法检查，避免产物里带语法错误', 'wqn', ['功能']),
     ]),
    ('清聪节奏 · 路线图', '单文件 Web 音游引擎：构建、试玩与谱面工具',
     ['qingcong-rhythm'], [
         ('开 Pages：build 产物发在线试玩', 'P1',
          '`build/` 里有 `game.template.html` 与构建脚本，但仓库没开 Pages。\n\n- 一页试玩 + 一页模式说明\n- 注意音频要用户手势后才能播，首屏需要"点击开始"', 'qingcong-rhythm', ['发布']),
         ('补 CI：构建 + 冒烟脚本自动跑', 'P2',
          '`build/` 下已有 `_smoke_protos.js`、`live_check.js` 等脚本，但没有自动化入口。\n\n- push 时跑构建与冒烟脚本\n- 失败时把日志贴到 PR 评论', 'qingcong-rhythm', ['功能']),
     ]),
    ('B站关注管理台 · 路线图', 'Electron 桌面版：发版、许可与体验',
     ['bili-relation-manager'], [
         ('定许可：补 LICENSE', 'P1',
          '仓库没有 LICENSE，别人无法判断能不能用、能不能改。\n\n- 代码建议 MIT 或 AGPL（涉及 B 站接口，注意平台条款）\n- 与 README 的"使用说明/免责声明"保持一致', 'bili-relation-manager', ['整理']),
         ('发版：把 RELEASE_NOTES 接进 GitHub Releases', 'P2',
          '仓库有 `RELEASE_NOTES.md`，但 Releases 页是空的。\n\n- 打 tag 时自动把对应段落发成 Release\n- 附带安装包校验值', 'bili-relation-manager', ['发布']),
     ]),
    ('live-copilot · 路线图', '弹幕游戏 AI 导演：进度对齐与许可',
     ['live-copilot'], [
         ('定许可：补 LICENSE', 'P1',
          '仓库无 LICENSE。涉及自研源码，建议先明确授权范围再对外。', 'live-copilot', ['整理']),
         ('STATUS.md 与实际进度对齐', 'P2',
          '`STATUS.md`、`GAME-ANALYSIS.md`、`GAME-CONTROL-MATRIX.md` 三份文档并存，容易互相矛盾。\n\n- 以 STATUS 为唯一进度源，其余两份只做参考并标注更新时间\n- 未完成项拆成议题挂到本看板', 'live-copilot', ['整理']),
     ]),
    ('若辰曲库 × Toy 小游戏 · 路线图', '匹配体系与生成物：公开策略、许可与整理',
     ['ruochen-toy-games'], [
         ('定许可：补 LICENSE', 'P1',
          '仓库私有且无 LICENSE。若要从私有转公开，先定许可与曲库数据的使用边界。', 'ruochen-toy-games', ['整理']),
         ('公开策略：toy/ 下小游戏是否上 Pages', 'P1',
          '`toy/01-cat-feeding.html`、`toy/game-match-board.html` 是可直接访问的独立页面。\n\n- 私有仓开 Pages 需要付费方案，先决定是否转公开\n- 转公开前检查曲库元数据是否含不宜公开的信息', 'ruochen-toy-games', ['发布']),
     ]),
    ('skyworth 8S03 物理按键 · 路线图', '电视物理按键映射：机型覆盖与风险说明',
     ['skyworth-8s03-physkey'], [
         ('补机型/固件对照表', 'P2',
          '目前只针对 8S03 / 42E600Y。\n\n- 列出已验证机型、固件版本、按键码\n- 未验证机型标注"可能可用/风险未知"', 'skyworth-8s03-physkey', ['整理']),
         ('补回滚与变砖风险说明', 'P1',
          '涉及改系统按键映射，出问题可能开不了机。\n\n- README 顶部写清楚风险与恢复步骤\n- 提供一键还原脚本', 'skyworth-8s03-physkey', ['整理']),
     ]),
    ('汽水音乐工具集 · 路线图', '13 个仓库：宿主 / 内核 / 插件族的统一维护',
     QISHUI, [
         ('补齐缺失的 LICENSE', 'P1',
          '`qishui-dashboard`、`qishui-music-automation` 没有 LICENSE，其余插件都有。\n\n- 与插件族保持一致\n- 注意抓取类代码的平台条款', 'qishui-dashboard', ['整理']),
         ('统一 CI：插件族共用构建矩阵', 'P2',
          '13 个仓库结构几乎一致（`plugin.json` + `build_exe.py` + `selftest`），现在全靠手工构建。\n\n- 一个可复用 workflow，按插件清单跑 build + selftest\n- 产物统一命名，便于 host 拉取', 'qishui-host', ['功能']),
         ('插件索引页：从 plugin.json 自动生成', 'P2',
          '插件越加越多，缺一个总览。\n\n- 扫各仓库 `plugin.json` 生成一张表：名称/版本/依赖/状态\n- 可挂在 host 的 README 或独立 Pages', 'qishui-core', ['功能']),
         ('宿主与插件版本兼容矩阵', 'P2',
          'host 更新/回滚机制已有，但缺一张"哪些插件版本配哪个 host 版本"的表。', 'qishui-host', ['整理']),
     ]),
]

viewer = gql('query{viewer{id login}}')['data']['viewer']
existing = gql('query{user(login:"%s"){projectsV2(first:50){nodes{id title url number}}}}' % OWNER)['data']['user']['projectsV2']['nodes']
by_title = {p['title']: p for p in existing}

repo_ids = {}
print('== topics ==')
for name, tp in TOPICS.items():
    # 注意：PATCH /repos 会静默忽略 topics，必须走 PUT /repos/{o}/{r}/topics
    # 并且要并集写入，否则会抹掉仓库上原有的 topics
    cur = call('%s/repos/%s/%s/topics' % (API, OWNER, name))
    prev = cur.get('names') or []
    merged = prev + [x for x in tp if x not in prev]
    r = call('%s/repos/%s/%s/topics' % (API, OWNER, name), 'PUT', {'names': merged})
    print('  %-28s %s' % (name, 'ok' if r.get('names') else r.get('_error')))

print('== boards ==')
made = []
for title, desc, repos, issues in BOARDS:
    if title in by_title:
        pid, purl = by_title[title]['id'], by_title[title]['url']
        print('  reuse %s' % title)
    else:
        r = gql('mutation($o:ID!,$t:String!){createProjectV2(input:{ownerId:$o,title:$t}){projectV2{id url}}}',
                {'o': viewer['id'], 't': title})
        if 'data' not in r:
            print('  FAIL create', title, json.dumps(r, ensure_ascii=False)[:160]); continue
        p = r['data']['createProjectV2']['projectV2']
        pid, purl = p['id'], p['url']
        print('  create %s' % title)
    gql('mutation($p:ID!,$d:String!){updateProjectV2(input:{projectId:$p,public:true,shortDescription:$d}){projectV2{id}}}',
        {'p': pid, 'd': desc})
    for rn in repos:
        if rn not in repo_ids:
            rr = call('%s/repos/%s/%s' % (API, OWNER, rn))
            repo_ids[rn] = rr.get('node_id')
        if repo_ids[rn]:
            gql('mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){repository{name}}}',
                {'p': pid, 'r': repo_ids[rn]})
    # 优先级字段
    f = gql('query($p:ID!){node(id:$p){... on ProjectV2{fields(first:30){nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}}', {'p': pid})
    nodes = [x for x in f['data']['node']['fields']['nodes'] if x and x.get('name') == '优先级']
    if nodes:
        pfid, opts = nodes[0]['id'], {o['name']: o['id'] for o in nodes[0]['options']}
    else:
        r = gql('''mutation($p:ID!){createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:"优先级",
          singleSelectOptions:[{name:"P0",color:RED,description:"现在就做"},
                               {name:"P1",color:ORANGE,description:"下一批"},
                               {name:"P2",color:GRAY,description:"有空再说"}]}){projectV2Field{... on ProjectV2SingleSelectField{id options{id name}}}}}''', {'p': pid})
        fld = r['data']['createProjectV2Field']['projectV2Field']
        pfid, opts = fld['id'], {o['name']: o['id'] for o in fld['options']}
    # 标签
    for rn in set([i[3] for i in issues]):
        labs = call('%s/repos/%s/%s/labels?per_page=100' % (API, OWNER, rn))
        names = {l['name'] for l in labs} if isinstance(labs, list) else set()
        for n, c in [('整理', '5319E7'), ('发布', '1D76DB'), ('功能', '0E8A16')]:
            if n not in names:
                call('%s/repos/%s/%s/labels' % (API, OWNER, rn), 'POST', {'name': n, 'color': c})
    # 议题
    n = 0
    for it_title, prio, body, rn, labs in issues:
        ex = call('%s/repos/%s/%s/issues?state=all&per_page=100' % (API, OWNER, rn))
        if isinstance(ex, list) and any(i.get('title') == it_title for i in ex):
            continue
        it = call('%s/repos/%s/%s/issues' % (API, OWNER, rn), 'POST',
                  {'title': it_title, 'body': body, 'labels': labs})
        if '_error' in it:
            print('    issue fail', it_title, it['_error']); continue
        add = gql('mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}',
                  {'p': pid, 'c': it['node_id']})
        iid = add['data']['addProjectV2ItemById']['item']['id']
        if prio in opts:
            gql('''mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(
                  input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}''',
                {'p': pid, 'i': iid, 'f': pfid, 'o': opts[prio]})
        n += 1
    made.append((title, purl, n))
print('== done ==')
for t, u, n in made:
    print('  %-32s +%d  %s' % (t, n, u))
