#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3D 参考帧 / 厚涂资产帧 / 精灵表 manifest → 单文件对照播放器。"""
import os,json,base64,io
from PIL import Image
ROOT='/data/workspace';B=os.path.join(ROOT,'参考图_素体网格')
FR=os.path.join(B,'01_解读/3D参考帧');SH=os.path.join(B,'02_精灵表')
WEB=os.path.join(B,'03_网页');os.makedirs(WEB,exist_ok=True)
PART=os.path.join(ROOT,'人形素体/02_裁切透明件')
meta=json.load(open(os.path.join(B,'04_校验/校验数据.json'),encoding='utf-8'))
man=json.load(open(os.path.join(SH,'manifest.json'),encoding='utf-8'))
report=open(os.path.join(B,'04_校验/参考图解读报告.md'),encoding='utf-8').read()

def b64(p):return 'data:image/png;base64,'+base64.b64encode(open(p,'rb').read()).decode()
def b64jpg(p,w=1000,q=80):
    im=Image.open(p).convert('RGB');im.thumbnail((w,w*9//16),Image.LANCZOS)
    b=io.BytesIO();im.save(b,'JPEG',quality=q,optimize=True)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()

D={'ref':{},'refMeta':[],'sheet':b64(os.path.join(SH,'人形素体_精灵表.png')),
   'assets':{},'assetMeta':[],'manifest':man,'report':report,
   'boards':{},'meta':{'ref_count':len(meta['ref_rows']),'asset_count':len(man['frames']),
                       'cell':man['cell'],'cols':man['cols'],'rows':man['rows'],
                       'green_left':meta['green_left'],
                       'by_direction':meta['by_direction'],
                       'by_dir8':meta['by_dir8'],'by_batch':meta['by_batch'],
                       'dir8_order':meta['dir8_order'],'dir8_labels':meta['dir8_labels'],
                       'dir8_confidence':meta['dir8_confidence'],
                       'asset_direction':man['asset_direction'],
                       'missing':man['gaps']['missing_asset_directions'],
                       'directions':meta['directions']}}
for r in meta['ref_rows']:
    D['ref'][r['id']]=b64(os.path.join(ROOT,'参考图_素体网格',r['file']))
    D['refMeta'].append({k:r[k] for k in ('id','board','direction','dir8','batch',
                                         'direction_label','confidence',
                                         'row','col','alpha_px','green_left')})
# 现有 64 件（按 manifest 顺序，含 __s）
for fr in man['frames']:
    aid=fr['id'];base=aid[:-3] if aid.endswith('__s') else aid
    import glob
    g=glob.glob(os.path.join(PART,'**',f'*_{aid}.png'),recursive=True)
    if g:D['assets'][aid]=b64(g[0])
    D['assetMeta'].append(fr)
# 6 张原图缩略
for p in sorted(os.listdir(os.path.join(B,'00_原图去重'))):
    D['boards'][p[:-4]]=b64jpg(os.path.join(B,'00_原图去重',p))
# 解读板 + 参考帧总览
for k,p in [('cmp','01_解读/十五张参考图_解读对照板.png'),
            ('refBoard','01_解读/3D白模_参考帧总览.png'),
            ('backBoard','01_解读/G5_背面32帧_预览.png'),
            ('compass','01_解读/八方向_罗盘矩阵.png'),
            ('dirRead','01_解读/八方向_代表格判读.png'),
            ('sheetBoard','01_解读/精灵表_编号预览.png')]:
    D['boards'][k]=b64jpg(os.path.join(B,p),1400,72)

HTML=r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>素体姿态网格 · 参考帧 / 精灵表 / manifest</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}html,body{height:100%;background:#121a16;color:#e8ece6;
font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;overflow:hidden}
#app{height:100%;display:flex;flex-direction:column;max-width:1340px;margin:0 auto}
header{flex:0 0 auto;display:flex;align-items:center;gap:10px;padding:8px 12px;background:#1d2a22;border-bottom:1px solid #31473a}
header h1{font-size:15px;font-weight:600;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.badge{font-size:11px;color:#9fc4aa;background:#26382c;padding:3px 8px;border-radius:10px;white-space:nowrap}
button{font-family:inherit;cursor:pointer;border:1px solid #3c5745;background:#26382c;color:#dceade;border-radius:8px;padding:6px 10px;font-size:12px;transition:.15s}
button:hover{background:#33503c}button.on{background:#4e9a68;border-color:#6cc38c;color:#fff}button.pri{background:#4e9a68;border-color:#6cc38c;color:#fff;font-weight:600}
nav{flex:0 0 auto;display:flex;gap:4px;padding:6px 10px;background:#18241d;overflow-x:auto}
nav button{white-space:nowrap;flex:0 0 auto}main{flex:1;min-height:0;overflow:auto;padding:10px}
section{display:none}section.show{display:block}
.panel{background:#1b2820;border:1px solid #304638;border-radius:12px;padding:10px;margin-bottom:10px}
.panel h2{font-size:13px;color:#a8d6b6;margin-bottom:8px;font-weight:600}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:7px}
.row label{font-size:12px;color:#9fb3a5;min-width:56px}
select,input[type=range]{background:#24362a;color:#e8ece6;border:1px solid #3c5745;border-radius:7px;padding:5px 7px;font-size:12px}
select{min-width:130px;flex:1;max-width:250px}input[type=range]{padding:0;flex:1;min-width:80px;accent-color:#5faf79}
.wrap{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start}
.stage{background:linear-gradient(180deg,#eae6dd,#d8d2c6);border-radius:12px;overflow:hidden;flex:0 0 auto;width:280px;height:333px}
.stage canvas{display:block;width:100%;height:100%}
.side{flex:1;min-width:240px;max-width:600px}
.kv{font-size:11px;color:#9fb3a5;line-height:1.8}.kv b{color:#dceade;font-weight:600}
.doc{font-size:12px;line-height:1.8;color:#c4d2c6;white-space:pre-wrap;word-break:break-word}
.doc h1,.doc h2{color:#a8d6b6;font-size:14px;margin:8px 0 4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:5px}
.cell{background:#243329;border:1px solid #354c3c;border-radius:8px;padding:3px;text-align:center;cursor:pointer}
.cell:hover{border-color:#6cc38c}.cell.on{border-color:#6cc38c;background:#2d4a36}
.cell canvas,.cell img{width:100%;height:auto;display:block;background:repeating-conic-gradient(#dcd8cf 0% 25%,#c0bbb1 0% 50%) 50%/10px 10px;border-radius:5px}
.cell span{display:block;font-size:9px;color:#a9bbae;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}.chip{font-size:10px;padding:3px 7px;border-radius:9px;background:#26382c;color:#a8c9b2;border:1px solid #3a5542}
.d8cell{background:#243329;border:1px solid #354c3c;border-radius:8px;padding:4px;text-align:center;cursor:pointer;min-height:112px}
.d8cell:hover{border-color:#6cc38c}.d8cell.on{border-color:#6cc38c;background:#2d4a36}
.d8cell canvas{width:100%;height:auto;display:block;background:repeating-conic-gradient(#dcd8cf 0% 25%,#c0bbb1 0% 50%) 50%/10px 10px;border-radius:5px}
.d8cell span{display:block;font-size:9px;color:#a9bbae;margin-top:3px;line-height:1.3}
.d8center,.d8blank{display:flex;align-items:center;justify-content:center;border-radius:8px;min-height:112px}
.d8center{background:#2b2320;border:1px solid #6a4a45;text-align:center}
footer{flex:0 0 auto;display:flex;gap:6px;padding:6px 10px;background:#18241d;border-top:1px solid #2c4133;justify-content:center;flex-wrap:wrap}
footer button{font-size:11px;padding:5px 9px;min-width:40px}
#big{position:fixed;inset:0;z-index:80;background:rgba(8,14,10,.95);display:none;align-items:center;justify-content:center;flex-direction:column;gap:10px;padding:14px}
#big img{max-width:96%;max-height:80%;border-radius:8px}#big div{font-size:13px;color:#a8d6b6}
.fullscreen main{padding:4px}.fullscreen header,.fullscreen nav{padding:4px 10px}
.hint{font-size:11px;color:#82988a;margin-top:6px;line-height:1.7}
</style></head><body>
<div id="big"><div></div><img><button>关闭</button></div>
<div id="app"><header><h1>素体姿态网格 · 参考帧 / 精灵表 / manifest</h1>
<span class="badge" id="badge"></span><button id="btnFs">⛶ 全屏</button></header>
<nav>
<button class="tab on" data-t="cmp">双栏对照</button>
<button class="tab" data-t="dir8">8 方向罗盘</button>
<button class="tab" data-t="sheet">精灵表播放</button>
<button class="tab" data-t="dress">换装叠加</button>
<button class="tab" data-t="board">原图与总览</button>
<button class="tab" data-t="doc">解读报告</button>
</nav><main>
<section id="s-cmp" class="show"><div class="wrap">
 <div class="stage"><canvas id="cR" width="160" height="190"></canvas></div>
 <div class="stage"><canvas id="cA" width="160" height="190"></canvas></div>
 <div class="side"><div class="panel"><h2>左：3D 白模参考帧　右：厚涂资产帧</h2>
  <div class="row"><label>参考板</label><select id="selRefBoard"></select>
   <label>参考帧</label><select id="selRef"></select></div>
  <div class="row"><label>资产组</label><select id="selGroup"></select>
   <label>资产帧</label><select id="selAsset"></select></div>
  <div class="row"><button id="btnSync">⇄ 按序号同步</button><button id="btnRefPlay" class="pri">▶ 参考帧连播</button></div>
  <div class="kv" id="cmpInfo"></div>
  <div class="hint">B 批 8 张各固定一个方向、内含 32 个动作相位；选 H1~H8 可逐向看白模背/侧/斜角。但右侧资产仍是 N（正面）——7 向缺口是故意留着让人看见的，不拿白模裁片冒充资产。</div>
 </div>
 <div class="panel"><h2>规格</h2><div class="kv" id="specInfo"></div></div>
 <div class="panel"><h2>8 方向矩阵（B 批 turntable）</h2><div class="kv" id="dirInfo"></div>
  <div class="hint">参考层 8/8 方向齐（每向 32 帧）；资产层仍只有 N。方位名按耳突位置目视判读，E/W 置信高、其余为中，原始素材无标注，可在 DIRECTION 一处改名。</div></div></div></div>
</section>
<section id="s-dir8"><div class="wrap">
 <div class="side" style="max-width:520px"><div class="panel"><h2>8 方向罗盘 · 点方向看该向 32 相位</h2>
  <div id="d8Grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:5px"></div>
  <div class="row" style="margin-top:8px"><button id="btnD8Play" class="pri">▶ 播放本方向</button>
   <button id="btnD8Prev">◀</button><button id="btnD8Next">▶</button>
   <label>fps</label><input type="range" id="rD8" min="2" max="16" value="8" style="max-width:90px"><span class="kv" id="vD8">8</span></div>
  <div class="kv" id="d8Info"></div>
  <div class="hint">B 批每方向 8×4=32 帧，是同一白模在该朝向下的动作相位。中间格是资产层现状：仍只有 N 的 64 帧厚涂资产，其余 7 向 0 帧。</div>
 </div></div>
 <div class="stage" style="width:300px;height:356px"><canvas id="cD8" width="160" height="190"></canvas></div>
</section>
<section id="s-sheet"><div class="wrap">
 <div class="stage" style="width:320px;height:380px"><canvas id="cS" width="160" height="190"></canvas></div>
 <div class="side"><div class="panel"><h2>按 manifest.rect 播帧（引擎同款）</h2>
  <div class="row"><button id="btnPlay" class="on">⏸ 暂停</button><button id="btnPrev">◀</button><button id="btnNext">▶</button>
   <label>fps</label><input type="range" id="rF" min="2" max="16" value="8" style="max-width:110px"><span class="kv" id="vF">8</span></div>
  <div class="row"><label>只播组</label><select id="selFilter"></select>
   <button id="btnPoseLoop">🏃 只播 8 姿态</button></div>
  <div class="kv" id="sInfo"></div><div class="chips" id="sChips"></div>
  <div class="hint">每帧 rect=[x,y,w,h] 来自 manifest.json，与 GenioPlus 导出的 JSON 元数据同口径（帧尺寸 / 行列 / 每帧矩形）。</div>
 </div></div>
 <div class="panel"><h2>整张精灵表（点击放大）</h2><img id="sheetImg" style="width:100%;max-width:640px;border-radius:8px;cursor:pointer;background:repeating-conic-gradient(#dcd8cf 0% 25%,#c0bbb1 0% 50%) 50%/12px 12px"></div>
</section>
<section id="s-dress"><div class="wrap">
 <div class="stage" style="width:320px;height:380px"><canvas id="cD" width="160" height="190"></canvas></div>
 <div class="side"><div class="panel"><h2>姿态帧 + 现有换装件</h2>
  <div class="row"><label>姿态</label><select id="selPose"></select></div>
  <div class="row"><label>毛发</label><select id="selHair"></select>
   <label>耳/角</label><select id="selEar"></select></div>
  <div class="row"><label>眼睛</label><select id="selEye"></select>
   <label>嘴</label><select id="selMouth"></select></div>
  <div class="row"><button id="btnBlush" class="on">腮红 ✓</button><button id="btnGlass" class="on">眼镜 ✓</button>
   <button id="btnBare">◌ 只看素体</button></div>
  <div class="kv" id="dInfo"></div><div class="chips" id="dChips"></div>
  <div class="hint">姿态帧与配件都是 320×380 统一画布，按 manifest 对齐；躺平/坐姿仍会穿帮（配件钉在正面脸坐标），这正是要检查的。</div>
 </div></div></section>
<section id="s-board">
 <div class="panel"><h2>15 张去重原图（A批 5 + B批 8方向 + 米底 2）＋ 6 张生成总览（点击放大）</h2><div class="grid" id="bGrid"></div></div>
</section>
<section id="s-doc">
 <div class="panel"><h2>参考图解读报告</h2><div class="doc" id="docReport"></div></div>
 <div class="panel"><h2>manifest.json（引擎可读）</h2><div class="doc" id="docJson" style="max-height:300px;overflow:auto;font-size:11px"></div></div>
</section>
</main>
<footer><button id="kPrev">◀</button><button id="kPlay">⏯</button><button id="kNext">▶</button>
<button id="kSync">⇄</button><button id="kFs">⛶</button></footer></div>
<script>
const D=__DATA__;
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const IMG={},W=160,H=190;
function load(){let n=0,t=0;
 for(const k in D.ref){t++;const i=new Image();i.onload=()=>{if(++n===t)ready()};i.src=D.ref[k];IMG[k]=i;}
 for(const k in D.assets){t++;const i=new Image();i.onload=()=>{if(++n===t)ready()};i.src=D.assets[k];IMG[k]=i;}
 for(const k in D.boards){t++;const i=new Image();i.onload=()=>{if(++n===t)ready()};i.src=D.boards[k];IMG[k]=i;}}
const S={tab:'cmp',refBoard:'G1',ref:'',asset:'',group:'',sheetIdx:0,playing:false,fps:8,
 filter:'',seq:null,seqName:'',pose:'act_stand1',hair:'hair_short',ear:'ear_cat',eye:'eye_open',
 mouth:'mouth_open',blush:true,glass:true,refPlay:false,refIdx:0,
 dir8:'N',d8playing:false,d8idx:0,d8fps:8};
const groups=[...new Set(D.manifest.frames.map(f=>f.group))];
const poses=D.manifest.frames.filter(f=>f.slot==='pose').map(f=>f.id);
function chk(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');
 for(let y=0;y<h;y+=12)for(let q=0;q<w;q+=12){x.fillStyle=((q/12+y/12)%2)?'#cec8c0':'#f0ece5';x.fillRect(q,y,12,12)}return c;}
function draw(c,key,scale){const x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);
 x.drawImage(chk(c.width,c.height),0,0);
 if(IMG[key])x.drawImage(IMG[key],0,0,IMG[key].width,IMG[key].height,0,0,c.width,c.height);}
function drawPose(c,keys){const x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);x.drawImage(chk(c.width,c.height),0,0);
 keys.forEach(k=>{if(IMG[k])x.drawImage(IMG[k],0,0,IMG[k].width,IMG[k].height,0,0,c.width,c.height);});}
const DCOL={front:'#7bc497',side:'#8fb4e8',turn:'#e0bb7a',back:'#e88b8b',unknown:'#9aa',
            N:'#5ec48c',NE:'#8fd0a0',E:'#8fb4e8',SE:'#e0bb7a',S:'#e88b8b',SW:'#d79ac0',W:'#a9a9ee',NW:'#7bc9c9'};
function dirTag(d){return `<b style="color:${DCOL[d]||'#9aa'}">${d||'—'}</b>`}
function renderCmp(){draw($('#cR'),S.ref);draw($('#cA'),S.asset);
 const a=D.refMeta.find(x=>x.id===S.ref),b=D.assetMeta.find(x=>x.id===S.asset);
 const atag=a?(a.dir8?`${dirTag(a.dir8)} ${D.meta.dir8_labels[a.dir8]}`:dirTag(a.direction)):'—';
 $('#cmpInfo').innerHTML=`左 <b>${S.ref||'—'}</b> · ${a?a.board:''} ${atag} · ${a?a.batch:''}批 · 置信 ${a?a.confidence:''} · r${a?a.row:''}c${a?a.col:''} · 绿残留 ${a?a.green_left:''}<br>右 <b>${S.asset||'—'}</b> · ${b?b.name:''} · ${b?b.slot:''} · ${dirTag(b?b.direction:'N')}`;
 const o=D.meta.dir8_order,by=D.meta.by_dir8,lb=D.meta.dir8_labels,cf=D.meta.dir8_confidence;
 let rows='';
 for(let i=0;i<o.length;i+=4){
   rows+='<tr>'+o.slice(i,i+4).map(d=>`<td style="padding:2px 9px">${dirTag(d)} ${lb[d]} <b>${by[d]}</b>帧 <span style="color:${cf[d]==='高'?'#7bc497':'#d8b46a'}">${cf[d]}</span></td>`).join('')+'</tr>';
 }
 $('#dirInfo').innerHTML=`<table style="border-collapse:collapse;font-size:11px">${rows}</table>`
   +`<div style="margin-top:6px">参考层 <b>8/8</b> 方向齐 · B批 ${D.meta.by_batch.B} 帧（8×32）＋ A批 ${D.meta.by_batch.A} 帧混合动作</div>`
   +`<div>资产层 <b>${D.meta.asset_direction}</b> 全部 ${D.meta.asset_count} 帧 · 仍缺 <b style="color:#e88b8b">${D.meta.missing.join(' / ')}</b>（7 向 = 0 帧）</div>`;
 $('#specInfo').innerHTML=`参考帧 <b>${D.meta.ref_count}</b> 张（13 板：A批 5 + B批 8 方向，统一 160×190，绿残留合计 <b>${D.meta.green_left}</b> px）<br>资产帧 <b>${D.meta.asset_count}</b> 件 · 精灵表 <b>${D.meta.cols}×${D.meta.rows}</b> · 单元格 ${D.meta.cell.join('×')}<br>manifest 每帧含 rect / row / col / group / slot / <b>direction</b> / loop / fps`;}
function renderSheet(){const F=D.manifest.frames;let f;
 if(S.seq){f=F.find(x=>x.id===S.seq[S.sheetIdx%S.seq.length])||F[0];}
 else{const list=S.filter?F.filter(x=>x.group===S.filter):F;f=list[S.sheetIdx%list.length];}
 draw($('#cS'),f.id);
 $('#sInfo').innerHTML=`FRAME <b>${f.index}</b> · ${f.id}<br>rect=[${f.rect.join(',')}] · row${f.row} col${f.col}<br>${f.group} · ${f.slot} · ${dirTag(f.direction)} · ${f.loop} · ${S.fps}fps · idx ${S.sheetIdx}`;
 $('#sChips').innerHTML=`<span class="chip">${f.group}</span><span class="chip">${f.slot}</span><span class="chip">r${f.row}c${f.col}</span><span class="chip">${f.rect[2]}×${f.rect[3]}</span>`;}
function dressLayers(){let a=[S.pose];
 // 姿态帧全是 Q版比例，配件一律用 Q版原版，不切少女版（否则尺寸错位）
 if(S.hair!=='none')a.push(S.hair);
 if(S.ear!=='none')a.push(S.ear);
 if(S.eye!=='none')a.push(S.eye);
 if(S.blush)a.push('blush');if(S.mouth!=='none')a.push(S.mouth);if(S.glass)a.push('glasses_round');return a;}
function renderDress(){drawPose($('#cD'),dressLayers());
 $('#dInfo').innerHTML=`姿态 <b>${S.pose}</b> · 叠加 ${dressLayers().length-1} 件配件`;
 $('#dChips').innerHTML=dressLayers().map(k=>`<span class="chip">${k}</span>`).join('');}
function d8Frames(d){return D.refMeta.filter(x=>x.dir8===d).map(x=>x.id);}
function renderD8(){const list=d8Frames(S.dir8);const k=((S.d8idx%list.length)+list.length)%list.length;
 draw($('#cD8'),list[k]);
 const cf=D.meta.dir8_confidence[S.dir8];
 $('#d8Info').innerHTML=`当前 <b>${dirTag(S.dir8)} ${D.meta.dir8_labels[S.dir8]}</b> · 置信 ${cf} · <b>${list.length}</b> 帧 · 第 ${k+1} 帧 <b>${list[k]}</b><br>资产层同方向帧数：<b style="color:${S.dir8==='N'?'#7bc497':'#e88b8b'}">${S.dir8==='N'?D.meta.asset_count:0}</b>`;
 $$('#d8Grid .d8cell').forEach(e=>e.classList.toggle('on',e.dataset.d===S.dir8));}
function fillD8(){const box=$('#d8Grid');box.innerHTML='';
 const POS={NW:0,N:1,NE:2,W:3,C:4,E:5,SW:6,S:7,SE:8};
 const cells=[];
 for(const d of D.meta.dir8_order)cells.push([POS[d],d]);
 cells.sort((a,b)=>a[0]-b[0]);
 let slot=0;
 const centerHTML=`<div style="font-size:11px;line-height:1.6;color:#c9b0b0">资产层<br><b>仅 N</b><br>其余 7 向<br><b>0 帧</b></div>`;
 for(const [pos,d] of cells){
  while(slot<pos){
   const blank=document.createElement('div');blank.className='d8blank';
   if(slot===4){blank.className='d8center';blank.innerHTML=centerHTML;}
   box.appendChild(blank);slot++;
  }
  const list=d8Frames(d);const rep=list.find(x=>x.includes('_r2c2'))||list[0];
  const e=document.createElement('div');e.className='d8cell';e.dataset.d=d;
  e.innerHTML=`<canvas width="80" height="95"></canvas><span>${dirTag(d)} ${D.meta.dir8_labels[d]} · ${D.meta.dir8_confidence[d]} · ${list.length}帧</span>`;
  e.onclick=()=>{S.dir8=d;S.d8idx=0;renderD8()};box.appendChild(e);
  draw(e.querySelector('canvas'),rep);slot++;
 }
 while(slot<9){const e=document.createElement('div');box.appendChild(e);slot++;}
 renderD8();}
function render(){if(S.tab==='cmp')renderCmp();if(S.tab==='sheet')renderSheet();
 if(S.tab==='dress')renderDress();if(S.tab==='dir8')renderD8();}
function go(t){S.tab=t;$$('.tab').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 $$('section').forEach(s=>s.classList.toggle('show',s.id==='s-'+t));
 document.querySelector('main').scrollTop=0;render();}
function opt(v,t){return `<option value="${v}">${t}</option>`}
function fillRef(){const bs=[...new Set(D.refMeta.map(x=>x.board))];
 let html='';
 for(const batch of ['A','B']){
  const list=bs.filter(b=>(D.meta.directions[b]||{}).batch===batch);
  if(!list.length)continue;
  html+=`<optgroup label="${batch==='A'?'A批 · 混合动作网格 5 板':'B批 · 8 方向 turntable 8 板'}">`;
  html+=list.map(b=>{const d=D.meta.directions[b]||{};
    const t=d.dir8?`[${d.dir8} ${D.meta.dir8_labels[d.dir8]}]`:`[${d.direction||'?'}]`;
    return opt(b,`${b} ${t} ${d.confidence||''}`)}).join('');
  html+='</optgroup>';
 }
 $('#selRefBoard').innerHTML=html;
 const upd=()=>{const b=$('#selRefBoard').value;S.refBoard=b;
  const list=D.refMeta.filter(x=>x.board===b);$('#selRef').innerHTML=list.map(x=>opt(x.id,`r${x.row}c${x.col} · ${x.id}`)).join('');
  S.ref=list[0]?list[0].id:'';$('#selRef').value=S.ref;renderCmp();};
 $('#selRefBoard').onchange=upd;$('#selRef').onchange=e=>{S.ref=e.target.value;renderCmp()};upd();}
function fillAssets(){const gs=[...new Set(D.assetMeta.map(x=>x.group))];
 $('#selGroup').innerHTML=gs.map(g=>opt(g,g)).join('');
 const upd=()=>{const g=$('#selGroup').value;S.group=g;
  const list=D.assetMeta.filter(x=>x.group===g);$('#selAsset').innerHTML=list.map(x=>opt(x.id,x.name)).join('');
  S.asset=list[0]?list[0].id:'';$('#selAsset').value=S.asset;renderCmp();};
 $('#selGroup').onchange=upd;$('#selAsset').onchange=e=>{S.asset=e.target.value;renderCmp()};upd();}
function fillSheet(){$('#selFilter').innerHTML=opt('','（全部组）')+groups.map(g=>opt(g,g)).join('');
 $('#selFilter').onchange=e=>{S.filter=e.target.value;S.seq=null;S.seqName='';S.sheetIdx=0;renderSheet()};
 $('#sheetImg').src=D.sheet;}
function fillDress(){const sel=(id,ids)=>{const e=$(id);e.innerHTML=opt('none','不装')+ids.map(x=>{
  const it=D.assetMeta.find(y=>y.id===x);return opt(x,it?it.name:x)}).join('');};
 $('#selPose').innerHTML=poses.map(p=>{const it=D.assetMeta.find(x=>x.id===p);return opt(p,it?it.name:p)}).join('');
 $('#selPose').value=S.pose;
 sel('#selHair',['hair_short','hair_cap','hair_twin','hair_long']);
 sel('#selEar',['ear_cat','ear_elf','horn_small','horn_big']);
 sel('#selEye',['eye_open','eye_closed','eye_smile','eye_star']);
 sel('#selMouth',['mouth_open','mouth_o']);
 ['hair','ear','eye','mouth'].forEach(k=>{const s='#sel'+k[0].toUpperCase()+k.slice(1);$(s).value=S[k];
  $(s).onchange=e=>{S[k]=e.target.value;renderDress()};});
 $('#selPose').onchange=e=>{S.pose=e.target.value;renderDress()};}
function fillBoards(){const box=$('#bGrid');box.innerHTML='';
 for(const k in D.boards){const e=document.createElement('div');e.className='cell';e.style.gridColumn='span 2';
  e.innerHTML=`<img src="${D.boards[k]}"><span>${k}</span>`;
  e.onclick=()=>{$('#big').style.display='flex';$('#big div').textContent=k;$('#big img').src=D.boards[k];};box.appendChild(e);}
 $('#big').onclick=()=>{$('#big').style.display='none'};
 $('#sheetImg').onclick=()=>{$('#big').style.display='flex';$('#big div').textContent='人形素体精灵表 '+D.meta.cols+'×'+D.meta.rows;$('#big img').src=D.sheet;};}
function tick(){if(S.playing){S.sheetIdx++;renderSheet();}
 if(S.refPlay){S.refIdx++;const list=D.refMeta.filter(x=>x.board===S.refBoard);
  S.ref=list[S.refIdx%list.length].id;$('#selRef').value=S.ref;renderCmp();}}
function tick8(){if(S.d8playing){S.d8idx++;renderD8();}}
function md2html(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/^### (.*)$/gm,'<h2>$1</h2>')
 .replace(/^## (.*)$/gm,'<h1>$1</h1>').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>');}
function ready(){
 fillRef();fillAssets();fillSheet();fillDress();fillBoards();fillD8();
 $('#docReport').innerHTML=md2html(D.report);$('#docJson').textContent=JSON.stringify(D.manifest,null,1);
 $('#badge').textContent=D.meta.ref_count+' 参考帧 · 8 向齐（B批 '+D.meta.by_batch.B+'） · '+D.meta.asset_count+' 资产帧仅 N · '+D.meta.cols+'×'+D.meta.rows+' sheet';
 $$('.tab').forEach(b=>b.onclick=()=>go(b.dataset.t));
 $('#btnSync').onclick=$('#kSync').onclick=()=>{const r=D.refMeta.filter(x=>x.board===S.refBoard),a=D.assetMeta.filter(x=>x.group===S.group);
  const i=S.sheetIdx%Math.min(r.length,a.length);S.ref=r[i%r.length].id;S.asset=a[i%a.length].id;
  $('#selRef').value=S.ref;$('#selAsset').value=S.asset;go('cmp');renderCmp();};
 $('#btnRefPlay').onclick=e=>{S.refPlay=!S.refPlay;e.target.textContent=S.refPlay?'⏸ 停参考连播':'▶ 参考帧连播';e.target.classList.toggle('on',S.refPlay);};
 $('#btnPlay').onclick=e=>{S.playing=!S.playing;e.target.textContent=S.playing?'⏸ 暂停':'▶ 播放';e.target.classList.toggle('on',S.playing);};
 $('#btnPrev').onclick=()=>{S.sheetIdx=Math.max(0,S.sheetIdx-1);renderSheet();};
 $('#btnNext').onclick=()=>{S.sheetIdx++;renderSheet();};
 $('#btnPoseLoop').onclick=()=>{S.seq=poses;S.seqName='8 姿态循环';S.filter='';$('#selFilter').value='';S.sheetIdx=0;S.playing=true;
  $('#btnPlay').textContent='⏸ 暂停';$('#btnPlay').classList.add('on');go('sheet');renderSheet();};
 $('#rF').oninput=e=>{S.fps=+e.target.value;$('#vF').textContent=S.fps;};
 $('#btnD8Play').onclick=e=>{S.d8playing=!S.d8playing;e.target.textContent=S.d8playing?'⏸ 暂停':'▶ 播放本方向';e.target.classList.toggle('on',S.d8playing);};
 $('#btnD8Prev').onclick=()=>{S.d8idx--;renderD8()};
 $('#btnD8Next').onclick=()=>{S.d8idx++;renderD8()};
 $('#rD8').oninput=e=>{S.d8fps=+e.target.value;$('#vD8').textContent=S.d8fps;};
 $('#btnBlush').onclick=e=>{S.blush=!S.blush;e.target.classList.toggle('on',S.blush);e.target.textContent=S.blush?'腮红 ✓':'腮红 ✕';renderDress();};
 $('#btnGlass').onclick=e=>{S.glass=!S.glass;e.target.classList.toggle('on',S.glass);e.target.textContent=S.glass?'眼镜 ✓':'眼镜 ✕';renderDress();};
 $('#btnBare').onclick=()=>drawPose($('#cD'),[S.pose]);
 $('#kPrev').onclick=()=>$('#btnPrev').click();$('#kNext').onclick=()=>$('#btnNext').click();$('#kPlay').onclick=()=>$('#btnPlay').click();
 $('#btnFs').onclick=$('#kFs').onclick=()=>{if(!document.fullscreenElement){try{const p=document.documentElement.requestFullscreen?.();if(p&&p.catch)p.catch(()=>{})}catch(e){}document.body.classList.add('fullscreen');}
  else{try{document.exitFullscreen?.()}catch(e){}document.body.classList.remove('fullscreen');}};
 document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')$('#btnPrev').click();if(e.key==='ArrowRight')$('#btnNext').click();
  if(e.key===' '){e.preventDefault();$('#btnPlay').click()}if(e.key.toLowerCase()==='f')$('#btnFs').click();
  if(e.key.toLowerCase()==='s')$('#btnSync').click();});
 let last=0,last8=0;
 function loop(t){if(t-last>1000/S.fps){last=t;tick()}
  if(t-last8>1000/S.d8fps){last8=t;tick8()}requestAnimationFrame(loop)}
 requestAnimationFrame(loop);
 render();}
load();
</script></body></html>'''
out=HTML.replace('__DATA__',json.dumps(D,ensure_ascii=False,separators=(',',':')))
p=os.path.join(WEB,'素体姿态网格_参考与精灵表.html');open(p,'w',encoding='utf-8').write(out)
print('HTML',round(os.path.getsize(p)/1024/1024,2),'MB',len(D['ref']),'参考帧',len(D['assets']),'资产帧')

entry='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>直接看 · 素体姿态网格</title><style>html,body{height:100%;margin:0;background:#0e1611;color:#e8ece6;
font-family:-apple-system,"PingFang SC",sans-serif;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;text-align:center;padding:20px}
h1{font-size:18px;font-weight:600}p{font-size:12px;color:#9fb3a5;line-height:1.8;max-width:350px}
a{display:block;width:270px;padding:14px;border-radius:12px;background:#4e9a68;color:#fff;text-decoration:none;font-size:15px;font-weight:600}
a.sec{background:#26382c;font-weight:400;font-size:13px}</style></head><body>
<h1>素体姿态网格 · 8 方向已齐</h1><p>13 张 3D 白模绿幕网格 → <b>412 张</b>透明参考帧<br>B 批 <b style="color:#7bc497">8 方向 × 32 相位 = 256</b> ＋ A 批混合动作 156<br><b style="color:#e88b8b">资产层仍只有 N（正面）64 帧，其余 7 向 = 0</b></p>
<a href="素体姿态网格_参考与精灵表.html?play=1">▶ 直接打开对照</a>
<a class="sec" href="素体姿态网格_参考与精灵表.html">完整播放器</a>
<a class="sec" href="素体姿态网格_参考与精灵表.html#doc">看解读报告</a>
<p style="font-size:11px;color:#6f8577">单文件网页，file:// 双击可开，所有帧已内嵌</p></body></html>'''
open(os.path.join(WEB,'直接看.html'),'w',encoding='utf-8').write(entry)
inject='''<script>if(location.search.includes('play')){setTimeout(()=>{go('cmp');document.body.classList.add('fullscreen');try{const p=document.documentElement.requestFullscreen?.();if(p&&p.catch)p.catch(()=>{})}catch(e){}},300);}</script>'''
open(p,'w',encoding='utf-8').write(out.replace('</body>',inject+'</body>'))
print('已注入 ?play=1')
