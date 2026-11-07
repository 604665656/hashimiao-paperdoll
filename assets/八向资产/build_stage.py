#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""8 向导演台：白模参考 / 厚涂候选 / 现有资产三栏对照 + 按 rect 播帧 + 换装叠加 + 挑图导出。"""
import os,json,base64,io,glob
from PIL import Image
ROOT='/data/workspace';B=os.path.join(ROOT,'八向资产')
WEB=os.path.join(B,'04_网页');os.makedirs(WEB,exist_ok=True)
REF=os.path.join(ROOT,'参考图_素体网格/01_解读/3D参考帧')
PART=os.path.join(ROOT,'人形素体/02_裁切透明件')
MP=os.path.join(ROOT,'参考图_素体网格/02_精灵表/manifest.json')
man=json.load(open(MP,encoding='utf-8'))
meta=json.load(open(os.path.join(ROOT,'参考图_素体网格/04_校验/校验数据.json'),encoding='utf-8'))
report=open(os.path.join(B,'05_校验/候选自检报告.md'),encoding='utf-8').read()
checklist=json.load(open(os.path.join(B,'05_校验/16帧候选清单.json'),encoding='utf-8'))

def b64(p):return 'data:image/png;base64,'+base64.b64encode(open(p,'rb').read()).decode()
def b64jpg(p,w=1000,q=78):
    im=Image.open(p).convert('RGB');im.thumbnail((w,w*9//16),Image.LANCZOS)
    b=io.BytesIO();im.save(b,'JPEG',quality=q,optimize=True)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()

ORDER=['N','NE','E','SE','S','SW','W','NW']
LAB=dict(N='正面',NE='右前斜',E='右侧',SE='右后斜',S='背面',SW='左后斜',W='左侧',NW='左前斜')
REFBOARD=dict(N='H6',NE='H2',E='H3',SE='H7',S='H8',SW='H5',W='H4',NW='H1')
SAMPLE=['r1c1','r1c5','r2c3','r2c7','r3c1','r3c5','r4c3','r4c7']
PHASE=['并脚站立','迈左腿','双腿交错','迈右腿']
COVERED=['N','E','S','W']

# 白模：每向 8 个代表相位
D={'white':{},'cand':{},'assets':{},'assetMeta':man['frames'],'sheet':None,
   'previews':{},'meta':dict(order=ORDER,labels=LAB,phases=PHASE,covered=COVERED,
        not_generated=['NE','SE','SW','NW'],sample=SAMPLE,
        ref_total=meta['ref_frames'],by_dir8=meta['by_dir8'],
        asset_direction=man['asset_direction'],missing=man['gaps']['missing_asset_directions'],
        candidate_coverage=man['gaps']['candidate_coverage'],
        dir8_confidence=meta['dir8_confidence']),
   'manifest':man['candidates'],'report':report,'checklist':checklist['rows'],
   'anchors':dict(hair_short=(160,100,158),hair_cap=(160,96,140),hair_twin=(160,112,172),
        hair_long=(160,114,168),ear_cat=(160,70,150),ear_elf=(160,70,146),
        horn_small=(160,66,134),horn_big=(160,64,152),eye_open=(160,132,116),
        eye_closed=(160,132,112),eye_smile=(160,132,112),eye_star=(160,132,116),
        glasses_round=(160,130,152),blush=(160,158,132),
        mouth_open=(160,170,62),mouth_o=(160,170,44))}
for d in ORDER:
    bd=REFBOARD[d];D['white'][d]=[]
    for s in SAMPLE:
        p=os.path.join(REF,f'{bd}_{s}.png')
        if os.path.exists(p):D['white'][d].append(dict(id=f'{bd}_{s}',img=b64(p)))
    D['cand'][d]=[]
    for i in range(1,5):
        p=os.path.join(B,'04_候选dist',f'{d}_p{i}.png')
        if os.path.exists(p):D['cand'][d].append(dict(id=f'{d}_p{i}',img=b64(p)))
# 现有资产：只取姿态 8 帧 + 配件 16 件（控制体积）
KEEP=set(['act_stand1','act_stand2','act_walk','act_run','act_sit','act_lie','act_wave','act_chest',
          'hair_short','hair_cap','hair_twin','hair_long','ear_cat','ear_elf','horn_small','horn_big',
          'eye_open','eye_closed','eye_smile','eye_star','glasses_round','blush','mouth_open','mouth_o'])
for fr in man['frames']:
    aid=fr['id']
    if aid not in KEEP or aid.endswith('__s'):continue
    g=glob.glob(os.path.join(PART,'**',f'*_{aid}.png'),recursive=True)
    if g:D['assets'][aid]=b64(g[0])
D['sheet']=b64(os.path.join(B,'八向候选_精灵表_4向.png'))
for k,p in [('fourBoards','02_预览/四板总览.png'),
            ('claimVsReal','02_预览/32帧_声称vs实测方向.png'),
            ('cand16','02_预览/16帧候选_四向总览.png'),
            ('colorFix','02_预览/毛色归一化_前后对比.png')]:
    D['previews'][k]=b64jpg(os.path.join(B,p),1000,76)

HTML=r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>8 向导演台 · 参考 / 候选 / 资产 / 换装</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}html,body{height:100%;background:#121a16;color:#e8ece6;
font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
header{display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid #2c4032;background:#16211a}
h1{font-size:14px;font-weight:600;white-space:nowrap}#badge{margin-left:auto;font-size:11px;color:#9fb3a5;text-align:right}
nav{display:flex;gap:5px;padding:7px 12px;border-bottom:1px solid #26382c;overflow-x:auto}
.tab{font-family:inherit;font-size:12px;padding:6px 12px;border-radius:8px;border:1px solid #354c3c;background:#1e2c23;color:#c8d9cd;cursor:pointer;white-space:nowrap}
.tab.on{background:#4e9a68;color:#fff;border-color:#6cc38c;font-weight:600}
main{height:calc(100% - 92px);overflow:auto;padding:12px}
section{display:none}section.show{display:block}
.wrap{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start}
.side{width:270px;flex:0 0 270px;display:flex;flex-direction:column;gap:9px}
.panel{background:#1b2820;border:1px solid #304638;border-radius:11px;padding:10px}
.panel h2{font-size:12px;color:#a8d6b6;margin-bottom:7px;font-weight:600}
.kv{font-size:11px;line-height:1.75;color:#c3d3c7}
.hint{font-size:10.5px;color:#82988a;line-height:1.7;margin-top:7px}
button{font-family:inherit;cursor:pointer;border:1px solid #3c5745;background:#26382c;color:#dceade;border-radius:8px;padding:6px 10px;font-size:11px}
button.pri{background:#4e9a68;border-color:#6cc38c;color:#fff;font-weight:600}button.on{background:#4e9a68;color:#fff}
button.warn{background:#5a342f;border-color:#8a5048;color:#f0d6d0}
.row{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.dirbtns{display:grid;grid-template-columns:repeat(4,1fr);gap:4px}
.dirbtns button{padding:7px 2px;font-size:10px;line-height:1.3}
.dirbtns button.cov{border-color:#6cc38c;color:#a8d6b6}
.dirbtns button.miss{border-color:#6a4a45;color:#c9a5a0}
.dirbtns button.on{background:#4e9a68;color:#fff}
.triple{display:flex;gap:10px;flex-wrap:wrap}
.col{background:#1b2820;border:1px solid #304638;border-radius:11px;padding:9px;text-align:center}
.col h3{font-size:11px;color:#a8d6b6;margin-bottom:6px;font-weight:600}
canvas{display:block;background:repeating-conic-gradient(#e8e4dc 0% 25%,#cbc5bb 0% 50%) 50%/12px 12px;border-radius:7px;width:160px;height:190px}
.col .cap{font-size:10px;color:#9fb3a5;margin-top:6px;line-height:1.5;min-height:30px}
.empty{display:flex;align-items:center;justify-content:center;color:#c9a5a0;font-size:11px;
 background:#2b2320;border:1px dashed #6a4a45;border-radius:7px;width:160px;height:190px;padding:12px;line-height:1.7}
input[type=range]{accent-color:#5faf79;flex:1;max-width:110px}
select,input[type=text]{font-family:inherit;font-size:11px;background:#24362a;color:#dceade;border:1px solid #3c5745;border-radius:6px;padding:5px}
label{font-size:11px;color:#a9bbae}
table{border-collapse:collapse;width:100%;font-size:11px}
td,th{padding:4px 6px;border-bottom:1px solid #2c4133;text-align:left}th{color:#a8d6b6}
.sheetbox{position:relative;display:inline-block;line-height:0}
.sheetbox img{max-width:100%;border-radius:8px;display:block}
#rectHL{position:absolute;border:2px solid #6cc38c;box-shadow:0 0 0 2px rgba(0,0,0,.35);pointer-events:none}
img.pv{width:100%;border-radius:8px;display:block;cursor:zoom-in}
#big{position:fixed;inset:0;z-index:90;background:rgba(8,14,10,.96);display:none;align-items:center;justify-content:center;flex-direction:column;gap:10px;padding:14px}
#big img{max-width:94%;max-height:78%;border-radius:8px}#big div{font-size:12px;color:#a8d6b6}
pre{white-space:pre-wrap;font-size:11px;line-height:1.7;color:#c3d3c7;max-height:520px;overflow:auto}
.chips{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}.chip{font-size:10px;padding:3px 7px;border-radius:9px;background:#26382c;color:#a8c9b2;border:1px solid #3a5542}
.ok{color:#7bc497}.no{color:#e39a90}
@media(max-width:720px){.side{width:100%;flex:1 1 100%}.triple{justify-content:center}}
</style></head><body>
<header><h1>8 向导演台</h1><span id="badge"></span></header>
<nav>
 <button class="tab on" data-t="stage">导演台</button>
 <button class="tab" data-t="rect">按 rect 播帧</button>
 <button class="tab" data-t="dress">换装叠加</button>
 <button class="tab" data-t="review">挑图 / 自检</button>
 <button class="tab" data-t="docs">文档全文</button>
</nav>
<main>
<section id="s-stage" class="show"><div class="wrap">
 <div class="side">
  <div class="panel"><h2>方向（4 向有候选 / 4 向未生成）</h2>
   <div class="dirbtns" id="dirbtns"></div>
   <div class="hint">绿框 = 本轮有厚涂候选；红框 = 模型没画出来，精灵表留空。参考层 8 向全有，资产层仍只有 N。</div>
  </div>
  <div class="panel"><h2>播放</h2>
   <div class="row"><button id="play" class="pri">▶ 播放</button><button id="prev">◀</button><button id="next">▶</button>
    <label>fps</label><input type="range" id="fps" min="2" max="16" value="8"><span id="vf" class="kv">8</span></div>
   <div class="row" style="margin-top:6px"><label><input type="checkbox" id="sync" checked> 三栏同步相位</label></div>
   <div class="kv" id="nowInfo" style="margin-top:7px"></div>
  </div>
  <div class="panel"><h2>当前帧判定</h2>
   <div class="row"><button id="markOk" class="pri">✓ 认可</button><button id="markNo" class="warn">✕ 作废</button>
    <button id="clearMark">清除</button></div>
   <div class="kv" id="markInfo" style="margin-top:6px"></div>
   <div class="hint">挑图结果只存在本机浏览器，点「导出清单」下载 JSON，回传后我再转正进 dist。</div>
  </div>
  <div class="panel"><h2>缺口</h2><div class="kv" id="gapInfo"></div></div>
 </div>
 <div style="flex:1;min-width:340px">
  <div class="triple">
   <div class="col"><h3>① 3D 白模参考（每向 8 相位）</h3><canvas id="cW" width="160" height="190"></canvas><div class="cap" id="capW"></div></div>
   <div class="col"><h3>② 厚涂候选（status=candidate）</h3><canvas id="cC" width="160" height="190"></canvas><div class="cap" id="capC"></div></div>
   <div class="col"><h3>③ 现有可装配资产</h3><canvas id="cA" width="160" height="190"></canvas><div class="cap" id="capA"></div></div>
  </div>
  <div class="panel" style="margin-top:10px"><h2>本轮结论</h2>
   <div class="kv">4 张拼板 32 帧：<b class="ok">绿 0 / 多手 0 / 洞 0</b>；但 <b class="no">30/32 与声称方向不符</b>，模型实际只画出「正面 / 背面 / 朝右走路」3 类，板2~4 互相重复且漂成暖黄淡彩。<br>
   已做毛色归一化 + E 水平镜像补 W，挑出 <b>16 帧 / 4 向</b> 候选；<b>NE/SE/SW/NW 本轮 0 帧</b>，不塞重复帧充数。全部未转正。</div>
  </div>
 </div>
</div></section>

<section id="s-rect"><div class="wrap">
 <div class="side">
  <div class="panel"><h2>精灵表 8 列 × 4 行</h2>
   <div class="kv">列 = 8 方向，行 = 4 走路相位，单元格 160×190。<br>4 个斜向列是透明空格，不是漏裁。</div>
   <div class="row" style="margin-top:8px"><button id="rectPlay" class="pri">▶ 按 rect 播</button>
    <button id="rectNext">下一格 ▶</button></div>
   <div class="row" style="margin-top:6px"><label>方向</label><select id="rectDir"></select>
    <label>相位</label><select id="rectPhase"></select></div>
   <div class="kv" id="rectInfo" style="margin-top:8px"></div>
  </div>
  <div class="panel"><h2>manifest 字段</h2><div class="kv">每帧 <code>rect[x,y,w,h]</code> / <code>row,col</code> / <code>dir8</code> / <code>phase</code> / <code>status</code>；顶层 <code>covered</code> / <code>not_generated</code> / <code>method</code> / <code>rejected</code>。</div></div>
 </div>
 <div style="flex:1;min-width:340px"><div class="panel"><div class="sheetbox">
   <img id="sheetImg"><div id="rectHL"></div></div></div></div>
</div></section>

<section id="s-dress"><div class="wrap">
 <div class="side">
  <div class="panel"><h2>底图</h2>
   <div class="row"><label>方向</label><select id="dDir"></select><label>相位</label><select id="dPhase"></select></div>
   <div class="kv" id="dInfo" style="margin-top:7px"></div>
  </div>
  <div class="panel"><h2>配件（历史 16 件）</h2>
   <div class="row"><label>毛发</label><select id="dHair"></select></div>
   <div class="row" style="margin-top:5px"><label>耳/角</label><select id="dEar"></select></div>
   <div class="row" style="margin-top:5px"><label>眼睛</label><select id="dEye"></select></div>
   <div class="row" style="margin-top:5px"><label>嘴巴</label><select id="dMouth"></select></div>
   <div class="row" style="margin-top:6px"><button id="dBlush" class="on">腮红 ✓</button><button id="dGlass" class="on">眼镜 ✓</button></div>
   <div class="row" style="margin-top:6px"><label>dx</label><input type="range" id="dx" min="-30" max="30" value="0">
    <label>dy</label><input type="range" id="dy" min="-30" max="30" value="0"></div>
   <div class="row" style="margin-top:5px"><button id="dBare">纯素体</button><button id="dExport">导出 PNG</button></div>
   <div class="hint" style="color:#d8a89f">斜向 / 背面叠正面五官会穿帮——这个页就是用来照穿帮的，不是交付装配。要逐帧对齐得给每个姿态单独定锚点。</div>
  </div>
  <div class="panel"><h2>当前叠加</h2><div class="chips" id="dChips"></div></div>
 </div>
 <div style="flex:1;min-width:300px;text-align:center"><div class="panel" style="display:inline-block">
  <canvas id="cD" width="320" height="380" style="width:320px;height:380px"></canvas>
  <div class="kv" style="margin-top:6px">320×380 装配画布（候选帧等比放大 2×）</div></div></div>
</div></section>

<section id="s-review"><div class="wrap">
 <div class="side">
  <div class="panel"><h2>挑图进度</h2><div class="kv" id="reviewStat"></div>
   <div class="row" style="margin-top:8px"><button id="exportMarks" class="pri">导出清单 JSON</button><button id="resetMarks">清空本机记录</button></div>
   <div class="hint">认可 / 作废只影响本机标记，不改变任何文件；导出后回传给我，我按清单转正。</div>
  </div>
  <div class="panel"><h2>四张诊断图（点击放大）</h2><div class="row" id="pvBtns"></div></div>
 </div>
 <div style="flex:1;min-width:340px"><div class="panel"><h2>16 帧候选清单</h2>
  <div style="max-height:560px;overflow:auto"><table id="tbl"></table></div></div></div>
</div></section>

<section id="s-docs"><div class="wrap">
 <div class="side"><div class="panel"><h2>文档</h2>
  <div class="row"><button class="docbtn on" data-k="report">候选自检报告</button>
   <button class="docbtn" data-k="manifest">候选 manifest</button>
   <button class="docbtn" data-k="checklist">16 帧清单 JSON</button></div></div>
  <div class="panel"><h2>其他入口</h2><div class="kv">
   <a style="color:#7bc497" href="../八方向_速览.html">8 方向速览</a><br>
   <a style="color:#7bc497" href="../../参考图_素体网格/03_网页/素体姿态网格_参考与精灵表.html">412 帧全量播放器</a><br>
   <a style="color:#7bc497" href="../../人形素体/04_网页/人形素体_全维度换装实验室.html">人形换装实验室</a>
  </div><div class="hint">相对链接需整包解压后使用；本页自身所有帧已内嵌，单独双击可开。</div></div>
 </div>
 <div style="flex:1;min-width:340px"><div class="panel"><pre id="docBox"></pre></div></div>
</div></section>
</main>
<div id="big"><div></div><img><button>关闭</button></div>
<script>
const D=__DATA__;
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const IMG={};let n=0,t=0;
function reg(key,src){t++;const i=new Image();i.onload=()=>{if(++n===t)ready()};i.src=src;IMG[key]=i;}
for(const d in D.white)for(const x of D.white[d])reg('w_'+x.id,x.img);
for(const d in D.cand)for(const x of D.cand[d])reg('c_'+x.id,x.img);
for(const k in D.assets)reg('a_'+k,D.assets[k]);
for(const k in D.previews)reg('p_'+k,D.previews[k]);
reg('sheet',D.sheet);
const S={tab:'stage',d:'N',i:0,playing:false,fps:8,sync:true,
         rectIdx:0,rectPlaying:false,
         dDir:'N',dPhase:0,hair:'hair_short',ear:'ear_cat',eye:'eye_open',
         mouth:'mouth_open',blush:true,glass:true,dx:0,dy:0};
let marks={};try{marks=JSON.parse(localStorage.getItem('husmeow8_marks')||'{}')}catch(e){marks={}}
function save(){localStorage.setItem('husmeow8_marks',JSON.stringify(marks))}
function chk(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');
 for(let y=0;y<h;y+=12)for(let q=0;q<w;q+=12){x.fillStyle=((q/12+y/12)%2)?'#cbc5bb':'#e8e4dc';x.fillRect(q,y,12,12)}return c;}
function draw(c,key,scale){const x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);
 x.drawImage(chk(c.width,c.height),0,0);
 if(IMG[key])x.drawImage(IMG[key],0,0,IMG[key].width,IMG[key].height,0,0,c.width,c.height);}
function drawD(c,keys){const x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);x.drawImage(chk(c.width,c.height),0,0);
 for(const k of keys){const i=IMG[k];if(!i)continue;x.drawImage(i,0,0,i.width,i.height,0,0,c.width,c.height);}}
function curWhite(){const L=D.white[S.d];return L.length?L[S.i%L.length]:null}
function curCand(){const L=D.cand[S.d];return L.length?L[S.i%L.length]:null}
function curAsset(){ // 资产层只有 N；用板F 8 姿态按相位映射
 const ids=['act_stand1','act_stand2','act_walk','act_run','act_sit','act_lie','act_wave','act_chest'];
 return ids[S.i%ids.length];}
function renderStage(){
 const w=curWhite(),c=curCand();
 draw($('#cW'),w?'w_'+w.id:'');
 if(c){draw($('#cC'),'c_'+c.id);$('#capC').innerHTML=`<b>${c.id}</b><br>${S.d} ${D.meta.labels[S.d]} · 相位 ${S.i%4+1}/4 · status=candidate`;}
 else{$('#cC').getContext('2d').clearRect(0,0,160,190);
  $('#capC').innerHTML=`<b style="color:#e39a90">本轮未生成</b><br>模型没画出 ${S.d} ${D.meta.labels[S.d]}`;}
 if(S.d==='N'){draw($('#cA'),'a_'+curAsset());$('#capA').innerHTML=`<b>${curAsset()}</b><br>现有 64 帧资产 · 全部 direction=N`;}
 else{$('#cA').getContext('2d').clearRect(0,0,160,190);
  $('#capA').innerHTML=`<b style="color:#e39a90">资产层 0 帧</b><br>该向从未转正`;}
 $('#capW').innerHTML=w?`<b>${w.id}</b><br>3D 白模参考 · 第 ${S.i%8+1}/8 相位<br><span style="font-size:9px;color:#82988a">该向 32 帧的抽样，含转身过渡</span>`:'—';
 $('#nowInfo').innerHTML=`方向 <b>${S.d} ${D.meta.labels[S.d]}</b> · 相位 <b>${S.i%4+1}/4</b><br>参考层该向 <b>${D.meta.by_dir8[S.d]}</b> 帧 · 候选 <b>${D.cand[S.d].length}</b> 帧`;
 $$('#dirbtns button').forEach(b=>b.classList.toggle('on',b.dataset.d===S.d));
 const key=c?c.id:null;
 $('#markInfo').innerHTML=key?`当前候选 <b>${key}</b> · 标记 <b class="${marks[key]==='ok'?'ok':'no'}">${marks[key]||'未判定'}</b>`:'该方向没有候选帧，无需判定';
 $('#gapInfo').innerHTML=`参考层 <b class="ok">8/8</b>（每向 32 帧 / 共 ${D.meta.ref_total}）<br>候选层 <b>4/8</b>（N/E/S/W，未转正）<br>资产层 <b class="no">1/8</b>（仅 ${D.meta.asset_direction}，64 帧）<br>资产层仍缺 <b class="no">${D.meta.missing.join(' / ')}</b><br>候选层仍缺 <b class="no">${D.meta.not_generated.join(' / ')}</b>`;
}
function buildDirBtns(){$('#dirbtns').innerHTML=D.meta.order.map(d=>{
 const cov=D.meta.covered.includes(d);
 return `<button data-d="${d}" class="${cov?'cov':'miss'}" title="${D.meta.labels[d]}">${d}<br>${D.meta.labels[d]}<br><span style="font-size:9px">${cov?'候选4帧':'未生成'}</span></button>`}).join('');
 $$('#dirbtns button').forEach(b=>b.onclick=()=>{S.d=b.dataset.d;S.i=0;renderStage()});}
function renderRect(){
 const f=D.manifest.frames[S.rectIdx];
 const img=$('#sheetImg');const k=img.naturalWidth?1280/img.naturalWidth:1;
 const hl=$('#rectHL');
 const r=f.rect;hl.style.left=(r[0]*k)+'px';hl.style.top=(r[1]*k)+'px';
 hl.style.width=(r[2]*k)+'px';hl.style.height=(r[3]*k)+'px';
 $('#rectInfo').innerHTML=`FRAME ${f.index} · <b>${f.id||'未生成'}</b><br>rect=[${r.join(',')}] · row${f.row} col${f.col}<br>dir8=<b>${f.dir8} ${D.meta.labels[f.dir8]}</b> · ${f.phase} · <b class="${f.status==='candidate'?'ok':'no'}">${f.status}</b>`;
 $('#rectDir').value=f.dir8;$('#rectPhase').value=String(f.row-1);
}
function dressKeys(){
 const base=D.cand[S.dDir][S.dPhase];
 if(!base)return [];
 const keys=[base.img?D.cand[S.dDir][S.dPhase].id:null];
 return keys;
}
function renderDress(){
 const L=D.cand[S.dDir];
 if(!L.length){$('#dInfo').innerHTML='<b class="no">该向未生成候选帧</b>';$('#cD').getContext('2d').clearRect(0,0,320,380);return;}
 const base=L[S.dPhase%L.length];
 const x=$('#cD').getContext('2d');x.clearRect(0,0,320,380);x.drawImage(chk(320,380),0,0);
 // 候选帧 160×190 → 320×380 等比 2×
 const bi=IMG['c_'+base.id];if(bi)x.drawImage(bi,0,0,bi.width,bi.height,0,0,320,380);
 // 配件锚点：历史 320×380 坐标，按 dx/dy 微调
 const A=D.anchors;const picks=[S.hair,S.ear,S.eye,S.mouth];
 if(S.blush)picks.push('blush');if(S.glass)picks.push('glasses_round');
 for(const k of picks){
  if(!k||k==='none'||!A[k])continue;
  const ai=IMG['a_'+k];if(!ai)continue;
  const cx=A[k][0]+S.dx,cy=A[k][1]+S.dy,tw=A[k][2];
  const s=tw/320;const w=320*s,h=320*s*(ai.height/ai.width);
  x.drawImage(ai,0,0,ai.width,ai.height,cx-w/2,cy-h/2,w,h);
 }
 $('#dInfo').innerHTML=`底图 <b>${base.id}</b> · ${S.dDir} ${D.meta.labels[S.dDir]} · ${D.meta.phases[S.dPhase]}<br>status=candidate · 配件为历史 320×380 锚点叠层`;
 $('#dChips').innerHTML=[base.id,S.hair,S.ear,S.eye,S.mouth,
   S.blush?'blush':null,S.glass?'glasses_round':null]
   .filter(x=>x&&x!=='none').map(k=>`<span class="chip">${k}</span>`).join('');
}
function renderReview(){
 const rows=D.checklist;let ok=0,no=0;
 for(const r of rows){if(marks[r.id]==='ok')ok++;if(marks[r.id]==='no')no++;}
 $('#reviewStat').innerHTML=`16 帧候选 · <b class="ok">认可 ${ok}</b> · <b class="no">作废 ${no}</b> · 未判定 ${16-ok-no}`;
 let h='<tr><th>帧</th><th>方向</th><th>相位</th><th>来源</th><th>相位差</th><th>标记</th></tr>';
 for(const r of rows)h+=`<tr><td><b>${r.id}</b></td><td>${r.dir8} ${r.dir_cn}</td><td>${r.phase}</td>
  <td style="font-size:10px">${r.method}</td><td>${r.phase_diff_mean}</td>
  <td class="${marks[r.id]==='ok'?'ok':'no'}">${marks[r.id]||'—'}</td></tr>`;
 $('#tbl').innerHTML=h;
 $('#pvBtns').innerHTML=Object.keys(D.previews).map(k=>`<button class="pvbtn" data-k="${k}">${k}</button>`).join('');
 $$('.pvbtn').forEach(b=>b.onclick=()=>showBig('p_'+b.dataset.k,b.dataset.k));
}
function showBig(key,txt){$('#big').style.display='flex';$('#big div').textContent=txt;$('#big img').src=IMG[key]?IMG[key].src:'';}
function go(t){S.tab=t;$$('.tab').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 $$('section').forEach(s=>s.classList.toggle('show',s.id==='s-'+t));
 document.querySelector('main').scrollTop=0;
 if(t==='stage')renderStage();if(t==='rect')renderRect();
 if(t==='dress')renderDress();if(t==='review')renderReview();if(t==='docs')showDoc('report');}
function showDoc(k){
 if(k==='report')$('#docBox').textContent=D.report;
 if(k==='manifest')$('#docBox').textContent=JSON.stringify(D.manifest,null,1);
 if(k==='checklist')$('#docBox').textContent=JSON.stringify(D.checklist,null,1);
 $$('.docbtn').forEach(b=>b.classList.toggle('on',b.dataset.k===k));}
function tick(){if(S.playing){S.i++;renderStage()}}
function ready(){
 $('#sheetImg').src=D.sheet;$('#sheetImg').onload=()=>renderRect();
 $('#badge').textContent='参考层 8/8 · 候选层 4/8（未转正）· 资产层 1/8 · 16 帧候选可挑';
 buildDirBtns();
 $('#rectDir').innerHTML=D.meta.order.map(d=>`<option value="${d}">${d} ${D.meta.labels[d]}</option>`).join('');
 $('#rectPhase').innerHTML=D.meta.phases.map((p,i)=>`<option value="${i}">${p}</option>`).join('');
 $('#rectDir').onchange=e=>{const d=e.target.value;S.rectIdx=D.manifest.frames.findIndex(f=>f.dir8===d&&f.row===1);renderRect()};
 $('#rectPhase').oninput=e=>{const f=D.manifest.frames[S.rectIdx];S.rectIdx=D.manifest.frames.findIndex(x=>x.dir8===f.dir8&&x.row===+e.target.value+1);renderRect()};
 $('#dDir').innerHTML=D.meta.covered.map(d=>`<option value="${d}">${d} ${D.meta.labels[d]}</option>`).join('');
 $('#dPhase').innerHTML=D.meta.phases.map((p,i)=>`<option value="${i}">${p}</option>`).join('');
 const opts=(ids)=>[['none','不装'],...ids.map(x=>[x,x])].map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
 $('#dHair').innerHTML=opts(['hair_short','hair_cap','hair_twin','hair_long']);
 $('#dEar').innerHTML=opts(['ear_cat','ear_elf','horn_small','horn_big']);
 $('#dEye').innerHTML=opts(['eye_open','eye_closed','eye_smile','eye_star']);
 $('#dMouth').innerHTML=opts(['mouth_open','mouth_o']);
 $('#dHair').value=S.hair;$('#dEar').value=S.ear;$('#dEye').value=S.eye;$('#dMouth').value=S.mouth;
 $$('.tab').forEach(b=>b.onclick=()=>go(b.dataset.t));
 $('#play').onclick=e=>{S.playing=!S.playing;e.target.textContent=S.playing?'⏸ 暂停':'▶ 播放';e.target.classList.toggle('on',S.playing)};
 $('#prev').onclick=()=>{S.i--;renderStage()};$('#next').onclick=()=>{S.i++;renderStage()};
 $('#fps').oninput=e=>{S.fps=+e.target.value;$('#vf').textContent=S.fps};
 $('#sync').onchange=e=>{S.sync=e.target.checked};
 $('#markOk').onclick=()=>{const c=curCand();if(c){marks[c.id]='ok';save();renderStage();renderReview()}};
 $('#markNo').onclick=()=>{const c=curCand();if(c){marks[c.id]='no';save();renderStage();renderReview()}};
 $('#clearMark').onclick=()=>{const c=curCand();if(c){delete marks[c.id];save();renderStage();renderReview()}};
 $('#rectPlay').onclick=e=>{S.rectPlaying=!S.rectPlaying;e.target.textContent=S.rectPlaying?'⏸ 暂停':'▶ 按 rect 播';e.target.classList.toggle('on',S.rectPlaying)};
 $('#rectNext').onclick=()=>{S.rectIdx=(S.rectIdx+1)%D.manifest.frames.length;renderRect()};
 $('#dDir').onchange=e=>{S.dDir=e.target.value;S.dPhase=0;$('#dPhase').value='0';renderDress()};
 $('#dPhase').onchange=e=>{S.dPhase=+e.target.value;renderDress()};
 ['Hair','Ear','Eye','Mouth'].forEach(k=>{$('#d'+k).onchange=e=>{S[k.toLowerCase()]=e.target.value;renderDress()}});
 $('#dBlush').onclick=e=>{S.blush=!S.blush;e.target.textContent=S.blush?'腮红 ✓':'腮红 ✕';e.target.classList.toggle('on',S.blush);renderDress()};
 $('#dGlass').onclick=e=>{S.glass=!S.glass;e.target.textContent=S.glass?'眼镜 ✓':'眼镜 ✕';e.target.classList.toggle('on',S.glass);renderDress()};
 $('#dx').oninput=e=>{S.dx=+e.target.value;renderDress()};$('#dy').oninput=e=>{S.dy=+e.target.value;renderDress()};
 $('#dBare').onclick=()=>{S.hair='none';S.ear='none';S.eye='none';S.mouth='none';S.blush=false;S.glass=false;
  $('#dHair').value='none';$('#dEar').value='none';$('#dEye').value='none';$('#dMouth').value='none';renderDress()};
 $('#dExport').onclick=()=>{const a=document.createElement('a');a.download='换装叠加_'+S.dDir+'_p'+(S.dPhase+1)+'.png';
  a.href=$('#cD').toDataURL('image/png');a.click()};
 $('#exportMarks').onclick=()=>{const blob=new Blob([JSON.stringify({status:'user_review',frames:marks},null,2)],{type:'application/json'});
  const a=document.createElement('a');a.download='眼镜猫_八向挑图清单.json';a.href=URL.createObjectURL(blob);a.click()};
 $('#resetMarks').onclick=()=>{marks={};save();renderStage();renderReview()};
 $$('.docbtn').forEach(b=>b.onclick=()=>showDoc(b.dataset.k));
 $('#big').onclick=()=>{$('#big').style.display='none'};
 document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')$('#prev').click();if(e.key==='ArrowRight')$('#next').click();
  if(e.key===' '){e.preventDefault();$('#play').click()}});
 let last=0,lastR=0;function loop(t){if(t-last>1000/S.fps){last=t;tick()}
  if(t-lastR>1000/S.fps){lastR=t;if(S.rectPlaying){S.rectIdx=(S.rectIdx+1)%D.manifest.frames.length;renderRect()}}
  requestAnimationFrame(loop)}requestAnimationFrame(loop);
 renderStage();renderRect();
}
if(t===0)ready();
</script>
<script>if(location.search.includes('play')){setTimeout(()=>{document.body.classList.add('fullscreen');
 try{const p=document.documentElement.requestFullscreen?.();if(p&&p.catch)p.catch(()=>{})}catch(e){}},300)}</script>
</body></html>'''
out=HTML.replace('__DATA__',json.dumps(D,ensure_ascii=False,separators=(',',':')))
p=os.path.join(WEB,'八向导演台.html');open(p,'w',encoding='utf-8').write(out)
print('导演台',round(os.path.getsize(p)/1024/1024,2),'MB',
      sum(len(v) for v in D['white'].values()),'白模帧',
      sum(len(v) for v in D['cand'].values()),'候选帧',
      len(D['assets']),'资产件')
# 直接看入口
entry='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>直接看 · 8 向导演台</title><style>html,body{height:100%;margin:0;background:#0e1611;color:#e8ece6;
font-family:-apple-system,"PingFang SC",sans-serif;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px;text-align:center;padding:20px}
h1{font-size:18px}p{font-size:12px;color:#9fb3a5;line-height:1.9;max-width:360px}
a{display:block;width:280px;padding:14px;border-radius:12px;background:#4e9a68;color:#fff;text-decoration:none;font-size:15px;font-weight:600}
a.sec{background:#26382c;font-weight:400;font-size:13px}</style></head><body>
<h1>8 向导演台</h1><p>参考层 <b style="color:#7bc497">8/8</b> · 候选层 <b>4/8</b>（未转正）· 资产层 <b style="color:#e39a90">1/8</b><br>三栏对照 / 按 rect 播帧 / 换装叠加 / 挑图导出</p>
<a href="八向导演台.html?play=1">▶ 直接打开</a>
<a class="sec" href="八向导演台.html">完整页面</a>
<p style="font-size:11px;color:#6f8577">单文件，file:// 双击可开，所有帧已内嵌</p></body></html>'''
open(os.path.join(WEB,'直接看.html'),'w',encoding='utf-8').write(entry)
