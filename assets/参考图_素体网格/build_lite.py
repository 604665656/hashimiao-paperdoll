#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手机可直接开的 8 方向速览：只内嵌 8×8=64 张代表帧 + 2 张总览图。"""
import os,json,base64,io
from PIL import Image
ROOT='/data/workspace';B=os.path.join(ROOT,'参考图_素体网格')
REF=os.path.join(B,'01_解读');WEB=os.path.join(B,'03_网页')
meta=json.load(open(os.path.join(B,'04_校验/校验数据.json'),encoding='utf-8'))
man=json.load(open(os.path.join(B,'02_精灵表/manifest.json'),encoding='utf-8'))

def b64(p):return 'data:image/png;base64,'+base64.b64encode(open(p,'rb').read()).decode()
def b64jpg(p,w=1000,q=78):
    im=Image.open(p).convert('RGB');im.thumbnail((w,w*9//16),Image.LANCZOS)
    b=io.BytesIO();im.save(b,'JPEG',quality=q,optimize=True)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()

ORDER=meta['dir8_order'];LB=meta['dir8_labels'];CF=meta['dir8_confidence']
# 每方向抽 8 帧（4 行 × 取 c1,c3,c5,c7 与 r2/r4），保证是动作相位而非全同
SAMPLE=['r1c1','r1c5','r2c3','r2c7','r3c1','r3c5','r4c3','r4c7']
board_of={}
for r in meta['ref_rows']:
    if r['dir8']:board_of[r['dir8']]=r['board']
D={'frames':{},'order':ORDER,'labels':LB,'conf':CF,
   'by8':meta['by_dir8'],'byBatch':meta['by_batch'],
   'asset_direction':man['asset_direction'],'missing':man['gaps']['missing_asset_directions'],
   'board':board_of,'sample':SAMPLE,
   'compass':b64jpg(os.path.join(REF,'八方向_罗盘矩阵.png'),700),
   'read':b64jpg(os.path.join(REF,'八方向_代表格判读.png'),1000),
   'report':open(os.path.join(B,'04_校验/参考图解读报告.md'),encoding='utf-8').read(),
   'totalRef':meta['ref_frames'],'assetCount':len(man['frames'])}
for d in ORDER:
    bd=board_of[d];lst=[]
    for s in SAMPLE:
        p=os.path.join(REF,'3D参考帧',f'{bd}_{s}.png')
        if os.path.exists(p):lst.append(dict(id=f'{bd}_{s}',img=b64(p)))
    D['frames'][d]=lst

HTML=r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>8 方向速览 · 素体姿态网格</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}body{background:#121a16;color:#e8ece6;
font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:12px;max-width:680px;margin:0 auto}
h1{font-size:17px;margin:4px 0 6px}h2{font-size:13px;color:#a8d6b6;margin:14px 0 7px;font-weight:600}
p{font-size:12px;color:#a9bbae;line-height:1.8}
.card{background:#1b2820;border:1px solid #304638;border-radius:12px;padding:10px;margin-bottom:10px}
.kpi{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.kpi div{flex:1;min-width:100px;background:#24362a;border-radius:9px;padding:8px;text-align:center}
.kpi b{display:block;font-size:18px;color:#7bc497}.kpi span{font-size:10px;color:#9fb3a5}
.kpi .warn b{color:#e88b8b}
img{width:100%;border-radius:8px;display:block}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}
.cell{background:#243329;border:1px solid #354c3c;border-radius:8px;padding:4px;text-align:center;cursor:pointer}
.cell.on{border-color:#6cc38c;background:#2d4a36}
.cell canvas{width:100%;height:auto;display:block;background:repeating-conic-gradient(#dcd8cf 0% 25%,#c0bbb1 0% 50%) 50%/10px 10px;border-radius:5px}
.cell span{display:block;font-size:10px;color:#a9bbae;margin-top:3px;line-height:1.3}
.center{display:flex;align-items:center;justify-content:center;background:#2b2320;border:1px solid #6a4a45;border-radius:8px;text-align:center;font-size:11px;color:#c9b0b0;line-height:1.6;padding:6px}
.stage{background:repeating-conic-gradient(#eae6dd 0% 25%,#cec8c0 0% 50%) 50%/14px 14px;border-radius:10px;width:200px;height:238px;margin:8px auto}
.stage canvas{display:block;width:100%;height:100%}
.row{display:flex;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;margin-top:8px}
button{font-family:inherit;cursor:pointer;border:1px solid #3c5745;background:#26382c;color:#dceade;border-radius:8px;padding:7px 12px;font-size:12px}
button.pri{background:#4e9a68;border-color:#6cc38c;color:#fff;font-weight:600}button.on{background:#4e9a68}
input[type=range]{accent-color:#5faf79;flex:1;max-width:110px}
table{width:100%;border-collapse:collapse;font-size:11px;margin-top:6px}
td,th{padding:4px 5px;border-bottom:1px solid #2c4133;text-align:left}th{color:#a8d6b6}
.hint{font-size:11px;color:#82988a;margin-top:7px;line-height:1.75}
a{color:#7bc497;font-size:12px}
#big{position:fixed;inset:0;z-index:80;background:rgba(8,14,10,.96);display:none;align-items:center;justify-content:center;flex-direction:column;gap:10px;padding:12px}
#big img{max-width:96%;max-height:78%;border-radius:8px}#big div{font-size:12px;color:#a8d6b6}
</style></head><body>
<div id="big"><div></div><img><button>关闭</button></div>
<h1>8 方向速览 · 素体姿态网格</h1>
<p>13 张纯色键绿 3D 白模网格 → 412 张透明参考帧。B 批 8 张各固定一个方向、内含 32 个动作相位，方向齐了。</p>
<div class="kpi">
 <div><b>8/8</b><span>参考层方向</span></div>
 <div><b>256</b><span>B 批相位帧</span></div>
 <div class="warn"><b>1/8</b><span>资产层方向</span></div>
 <div class="warn"><b>7 向</b><span>= 0 帧</span></div>
</div>
<div class="card"><h2>罗盘矩阵（点击放大）</h2><img id="compass" style="cursor:pointer"></div>
<div class="card"><h2>点方向 · 播放该向 8 个代表相位</h2>
 <div class="grid" id="grid"></div>
 <div class="stage"><canvas id="cv" width="160" height="190"></canvas></div>
 <div class="row"><button id="play" class="pri">▶ 播放</button>
  <button id="prev">◀</button><button id="next">▶</button>
  <label style="font-size:11px;color:#9fb3a5">fps</label><input type="range" id="fps" min="2" max="16" value="8"><span id="vf" style="font-size:11px">8</span></div>
 <p id="info" style="text-align:center;margin-top:6px"></p>
 <div class="hint">这里每向只内嵌 8 帧做速览；完整 32 帧/向在「完整播放器」里。方位名按耳突位置目视判读，E/W 置信高、其余为中，原始素材无标注。</div>
</div>
<div class="card"><h2>8 方向表</h2><table id="tbl"></table></div>
<div class="card"><h2>关键区分：参考层 ≠ 资产层</h2>
 <p>manifest 里 <b>64 个资产帧的 direction 全部是 N（正面）</b>，一个没改；<code>gaps.missing_asset_directions</code> 精确列出仍缺的 7 向。<b>没有</b>把白模背面/侧面裁片贴到厚涂资产上充数——那是之前反复翻车的「多源拼接」。</p>
 <p style="margin-top:6px">所以现在是：参考层 8/8 齐，资产层 1/8。有了标准答案，还没有作业。</p>
</div>
<div class="card"><h2>判读依据（点击放大）</h2><img id="read" style="cursor:pointer"></div>
<div class="card"><h2>更多</h2>
 <p><a href="素体姿态网格_参考与精灵表.html">→ 完整播放器（412 帧 + 精灵表 + manifest，约 16MB）</a></p>
 <p><a href="直接看.html">→ 直接看入口</a></p>
 <p style="margin-top:6px">同目录还有 <code>manifest.json</code>、逐帧透明 PNG、解读报告与校验数据。</p>
</div>
<div class="card"><h2>解读报告摘要</h2><p id="rpt" style="white-space:pre-wrap;font-size:11px;max-height:280px;overflow:auto"></p></div>
<script>
const D=__DATA__;
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const IMG={};let n=0,t=0;
for(const k in D){if(typeof D[k]==='string'&&D[k].startsWith('data:image')){t++;const i=new Image();i.onload=()=>{if(++n===t)ready()};i.src=D[k];IMG[k]=i;}}
for(const d in D.frames)for(const f of D.frames[d]){t++;const i=new Image();i.onload=()=>{if(++n===t)ready()};i.src=f.img;IMG[f.id]=i;}
const POS={NW:0,N:1,NE:2,W:3,E:5,SW:6,S:7,SE:8};
const S={d:'N',idx:0,playing:false,fps:8};
function chk(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');
 for(let y=0;y<h;y+=12)for(let q=0;q<w;q+=12){x.fillStyle=((q/12+y/12)%2)?'#cec8c0':'#f0ece5';x.fillRect(q,y,12,12)}return c;}
function draw(c,key){const x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);x.drawImage(chk(c.width,c.height),0,0);
 if(IMG[key])x.drawImage(IMG[key],0,0,IMG[key].width,IMG[key].height,0,0,c.width,c.height);}
function render(){const L=D.frames[S.d];const k=((S.idx%L.length)+L.length)%L.length;
 draw($('#cv'),L[k].id);
 $('#info').innerHTML=`<b>${S.d} · ${D.labels[S.d]}</b> · 置信 ${D.conf[S.d]} · 该向共 <b>${D.by8[S.d]}</b> 帧 · 速览第 ${k+1}/8 帧 <b>${L[k].id}</b><br>资产层同向帧数：<b style="color:${S.d==='N'?'#7bc497':'#e88b8b'}">${S.d==='N'?D.assetCount:0}</b>`;
 $$('#grid .cell').forEach(e=>e.classList.toggle('on',e.dataset.d===S.d));}
function ready(){
 $('#compass').src=D.compass;$('#read').src=D.read;
 const big=(key,txt)=>{const f=()=>{$('#big').style.display='flex';$('#big div').textContent=txt;$('#big img').src=D[key];};return f};
 $('#compass').onclick=big('compass','B 批 8 方向罗盘矩阵');
 $('#read').onclick=big('read','8 张各取 r2c2 代表格 · 方向判读依据');
 $('#big').onclick=()=>{$('#big').style.display='none'};
 const box=$('#grid');let slot=0;
 const cs=D.order.map(d=>[POS[d],d]).sort((a,b)=>a[0]-b[0]);
 for(const [p,d] of cs){
  while(slot<p){const blank=document.createElement('div');
   if(slot===4){blank.className='center';blank.innerHTML='资产层<br><b>仅 N</b><br>其余 7 向<br><b>0 帧</b>';}
   box.appendChild(blank);slot++;}
  const rep=D.frames[d][2]||D.frames[d][0];
  const e=document.createElement('div');e.className='cell';e.dataset.d=d;
  e.innerHTML=`<canvas width="80" height="95"></canvas><span>${d} ${D.labels[d]} · ${D.conf[d]}</span>`;
  e.onclick=()=>{S.d=d;S.idx=0;render()};box.appendChild(e);
  draw(e.querySelector('canvas'),rep.id);slot++;
 }
 while(slot<9){box.appendChild(document.createElement('div'));slot++;}
 let rows='<tr><th>方向</th><th>板</th><th>帧数</th><th>置信</th></tr>';
 for(const d of D.order)rows+=`<tr><td><b>${d}</b> ${D.labels[d]}</td><td>${D.board[d]}</td><td>${D.by8[d]}</td><td>${D.conf[d]}</td></tr>`;
 $('#tbl').innerHTML=rows;
 $('#rpt').textContent=D.report.slice(0,3200)+(D.report.length>3200?'\n…（完整报告见同目录 参考图解读报告.md）':'');
 $('#play').onclick=e=>{S.playing=!S.playing;e.target.textContent=S.playing?'⏸ 暂停':'▶ 播放';e.target.classList.toggle('on',S.playing)};
 $('#prev').onclick=()=>{S.idx--;render()};$('#next').onclick=()=>{S.idx++;render()};
 $('#fps').oninput=e=>{S.fps=+e.target.value;$('#vf').textContent=S.fps};
 document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')$('#prev').click();if(e.key==='ArrowRight')$('#next').click();
  if(e.key===' '){e.preventDefault();$('#play').click()}});
 let last=0;function loop(t){if(t-last>1000/S.fps){last=t;if(S.playing){S.idx++;render()}}requestAnimationFrame(loop)}
 requestAnimationFrame(loop);render();}
if(t===0)ready();
</script></body></html>'''
out=HTML.replace('__DATA__',json.dumps(D,ensure_ascii=False,separators=(',',':')))
p=os.path.join(WEB,'八方向_速览.html');open(p,'w',encoding='utf-8').write(out)
print('速览',round(os.path.getsize(p)/1024/1024,2),'MB',
      sum(len(v) for v in D['frames'].values()),'帧')
