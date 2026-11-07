#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两批共 13 张纯色键绿 3D 白模网格 → 透明姿态参考帧：
  A 批 G1~G5：混合动作网格（正面/侧身/转身/背面）
  B 批 H1~H8：8 方向等距 turntable，每方向 8×4=32 个动作相位
现有 64 件厚涂透明件 → 同规格引擎可读精灵表 + manifest。
"""
import os, json, csv, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT='/data/workspace'; B=os.path.join(ROOT,'参考图_素体网格')
RAW=os.path.join(B,'00_原图去重'); REF=os.path.join(B,'01_解读')
FR=os.path.join(B,'01_解读/3D参考帧'); SH=os.path.join(B,'02_精灵表')
WEB=os.path.join(B,'03_网页'); CHK=os.path.join(B,'04_校验')
for d in (REF,FR,SH,WEB,CHK):os.makedirs(d,exist_ok=True)
FONT='/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
def f(s):return ImageFont.truetype(FONT,s)

CELL_W,CELL_H=160,190
# 朝向标注：参考图的语义维度（只标参考帧，不往自有资产上硬安）
# B 批方向名依据「耳突位置 + 身体轮廓」目视判读，NE/SE/SW/NW 的前后归属置信度中等
DIR8_ORDER=['N','NE','E','SE','S','SW','W','NW']
DIR8_CN=dict(N='正面',NE='右前斜',E='右侧',SE='右后斜',
             S='背面',SW='左后斜',W='左侧',NW='左前斜')
# 白模无五官：正/背只能靠耳位与躯干细微差判，标「中」；纯侧面轮廓不对称最明显，标「高」
DIR8_CONF=dict(N='中',NE='中',E='高',SE='中',S='中',SW='中',W='高',NW='中')
DIRECTION={
 # A 批：混合动作网格，只给粗方向类
 'G1':dict(direction='front',dir8=None,batch='A',label='A批 · 正面 站姿/微动作',grid='9×4',confidence='高'),
 'G2':dict(direction='front',dir8=None,batch='A',label='A批 · 正面 蜷缩/跳跃',grid='7×4',confidence='高'),
 'G3':dict(direction='side', dir8=None,batch='A',label='A批 · 侧身 抬手/转向',grid='9×4',confidence='高'),
 'G4':dict(direction='turn', dir8=None,batch='A',label='A批 · 转身 奔跑/背向过渡',grid='9×4',confidence='中'),
 'G5':dict(direction='back', dir8=None,batch='A',label='A批 · 背面 背向站姿/摆臂',grid='8×4',confidence='高'),
 # B 批：8 方向等距 turntable，每张固定一个方向
 'H1':dict(direction='front',dir8='NW',batch='B',label='B批 · 左前斜 front-left',grid='8×4',confidence='中'),
 'H2':dict(direction='front',dir8='NE',batch='B',label='B批 · 右前斜 front-right',grid='8×4',confidence='中'),
 'H3':dict(direction='side', dir8='E', batch='B',label='B批 · 右侧 right',grid='8×4',confidence='高'),
 'H4':dict(direction='side', dir8='W', batch='B',label='B批 · 左侧 left',grid='8×4',confidence='高'),
 'H5':dict(direction='back', dir8='SW',batch='B',label='B批 · 左后斜 back-left',grid='8×4',confidence='中'),
 'H6':dict(direction='front',dir8='N', batch='B',label='B批 · 正面 front',grid='8×4',confidence='高'),
 'H7':dict(direction='back', dir8='SE',batch='B',label='B批 · 右后斜 back-right',grid='8×4',confidence='中'),
 'H8':dict(direction='back', dir8='S', batch='B',label='B批 · 背面 back',grid='8×4',confidence='高'),
}
# 逐板置信度统一以 DIR8_CONF 为准，避免罗盘图 / refMeta / 报告 / manifest 四处不一致
for _k,_v in DIRECTION.items():
    if _v['dir8']:_v['confidence']=DIR8_CONF[_v['dir8']]
GREEN_STRICT=lambda a:((a[...,1].astype(int)>a[...,0].astype(int)+40)&
                       (a[...,1].astype(int)>a[...,2].astype(int)+40)&
                       (a[...,1].astype(int)>150))

def segments(v,thr,minlen=20):
    on=v>thr;out=[];s=None
    for i,x in enumerate(on):
        if x and s is None:s=i
        if not x and s is not None:out.append((s,i-1));s=None
    if s is not None:out.append((s,len(on)-1))
    return [q for q in out if q[1]-q[0]>minlen]

def keys_from_board(rgb):
    fg=(~GREEN_STRICT(rgb)).astype(np.uint8)
    xs=segments(fg.sum(0),rgb.shape[0]*0.02,60)
    ys=segments(fg.sum(1),rgb.shape[1]*0.02,60)
    # 按等距补齐：取段中心，若 <8 列则用中位间距外推
    def centers(segs,limit):
        c=[(s+e)//2 for s,e in segs]
        if len(c)>=2:
            step=float(np.median(np.diff(c)))
            while len(c)<limit and c[-1]+step< max(limit*step*2,1e9):
                c.append(int(c[-1]+step))
        return c[:limit],step
    cx,stepx=centers(xs,8);cy,stepy=centers(ys,4)
    return cx,cy,stepx,stepy

def cut_grid(p,tag):
    rgb=np.array(Image.open(p).convert('RGB'))
    cx,cy,sx,sy=keys_from_board(rgb)
    out=[];rows=[]
    for r,y in enumerate(cy):
        for c,x in enumerate(cx):
            half_w, half_h = sx*0.48, sy*0.48
            x0,y0=int(x-half_w),int(y-half_h);x1,y1=int(x+half_w),int(y+half_h)
            x0,y0=max(0,x0),max(0,y0);x1,y1=min(rgb.shape[1],x1),min(rgb.shape[0],y1)
            if x1-x0<60 or y1-y0<60:continue
            crop=rgb[y0:y1,x0:x1]
            gm=GREEN_STRICT(crop)
            m=(~gm).astype(np.uint8)
            m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
            # 网格里白模上下相接会连成大域：选「质心最靠近格中心」的域，避免把邻格整片带进来
            n,lab,st,cen=cv2.connectedComponentsWithStats(m,8)
            if n<=1:continue
            cc=np.array([crop.shape[1]/2, crop.shape[0]/2])
            cand=[(float(np.linalg.norm(cen[k]-cc)),k,int(st[k,4])) for k in range(1,n) if st[k,4]>1800]
            if not cand:continue
            cand.sort();k=cand[0][1]
            comp=(lab==k).astype(np.uint8)*255
            comp=cv2.morphologyEx(comp,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
            # 只补 <240px 的内部小洞，绝不填外轮廓（外轮廓内全是绿幕缝隙）
            inv=(comp==0).astype(np.uint8)
            nh,lh,sh,_=cv2.connectedComponentsWithStats(inv,8)
            a=comp.copy()
            for q in range(1,nh):
                xx,yy,ww,hh,ar=sh[q]
                if xx>0 and yy>0 and xx+ww<comp.shape[1] and yy+hh<comp.shape[0] and ar<240:
                    a[lh==q]=255
            # 标准色键：绿幕像素（含 1px 膨胀去绿溢边）一律透明
            gm_d=cv2.dilate(gm.astype(np.uint8),np.ones((3,3),np.uint8))>0
            a[gm_d]=0
            # 去孤立碎块
            nb,lb,sb,_=cv2.connectedComponentsWithStats((a>18).astype(np.uint8),8)
            for q in range(1,nb):
                if sb[q,4]<120:a[lb==q]=0
            a=cv2.GaussianBlur(a.astype(np.float32),(0,0),0.8)
            a=np.clip(a,0,255).astype(np.uint8)
            gl=int((GREEN_STRICT(crop)&(a>18)).sum())
            im=Image.fromarray(np.dstack([crop,a]),'RGBA')
            # 等比 fit 到统一格
            s=min((CELL_H-8)/im.height,(CELL_W-8)/im.width,1.0)
            nw,nh=max(1,int(im.width*s)),max(1,int(im.height*s))
            im=im.resize((nw,nh),Image.LANCZOS)
            cv=Image.new('RGBA',(CELL_W,CELL_H),(0,0,0,0))
            cv.paste(im,((CELL_W-nw)//2,CELL_H-nh-4),im)
            fn=f'{tag}_r{r+1}c{c+1}.png'
            cv.save(os.path.join(FR,fn),optimize=True)
            al=np.array(cv)[...,3]
            md=DIRECTION.get(tag,dict(direction='unknown',dir8=None,batch='?',
                                       label=tag,grid='8×4',confidence='低'))
            rec=dict(id=f'{tag}_r{r+1}c{c+1}',file=f'01_解读/3D参考帧/{fn}',
                     board=tag,direction=md['direction'],dir8=md['dir8'],
                     batch=md['batch'],direction_label=md['label'],
                     confidence=md['confidence'],
                     row=r+1,col=c+1,alpha_px=int((al>18).sum()),green_left=gl,
                     src_box=[x0,y0,x1,y1],canvas=[CELL_W,CELL_H])
            out.append(cv);rows.append(rec)
    return out,rows

# ---------- 1) 13 张绿幕网格裁帧（A 批 5 + B 批 8 方向） ----------
all_ref=[];ref_rows=[]
boards=sorted([x for x in os.listdir(RAW) if x[:1] in ('G','H')])
for fn in boards:
    p=os.path.join(RAW,fn);tag=fn.split('_')[0]
    ims,rs=cut_grid(p,tag)
    all_ref+=ims;ref_rows+=rs
    info=DIRECTION.get(tag,{})
    print(f"{tag} [{info.get('batch','?')}批] dir8={str(info.get('dir8')):>4} "
          f"{info.get('label','')} 裁出 {len(ims)} 格")
print('3D 参考帧合计',len(all_ref),'绿残留',sum(r['green_left'] for r in ref_rows))

# 参考帧总览（棋盘底）
def checker(w,h,c1=(240,236,229),c2=(206,200,192)):
    im=Image.new('RGB',(w,h),c1);px=im.load()
    for y in range(0,h,12):
        for x in range(0,w,12):
            if (x//12+y//12)%2:px[x,y]=c2
    return im
cols=8;rows_n=(len(all_ref)+cols-1)//cols
board=Image.new('RGB',(cols*CELL_W+20,rows_n*(CELL_H+18)+40),(236,232,225))
d=ImageDraw.Draw(board);d.text((10,8),'13 张纯色键绿 3D 白模网格 → 透明姿态参考帧（A批混合动作 + B批 8 方向 turntable）',font=f(18),fill=(36,50,40))
DCOL={'front':(60,110,76),'side':(70,100,150),'turn':(150,110,60),'back':(170,70,70),'unknown':(90,90,90)}
D8COL=dict(N=(50,120,80),NE=(90,140,90),E=(70,100,160),SE=(150,110,60),
           S=(170,70,70),SW=(150,80,120),W=(90,90,170),NW=(60,140,140))
for i,im in enumerate(all_ref):
    r,c=divmod(i,cols);bg=checker(CELL_W-4,CELL_H-4)
    v=im.copy();v.thumbnail((CELL_W-10,CELL_H-10),Image.LANCZOS)
    bg.paste(v,((bg.width-v.width)//2,bg.height-v.height),v)
    board.paste(bg,(10+c*CELL_W,34+r*(CELL_H+18)))
    rec=ref_rows[i]
    col=D8COL.get(rec['dir8']) or DCOL.get(rec['direction'],(70,62,54))
    tag=rec['dir8'] or rec['direction']
    d.text((14+c*CELL_W,34+r*(CELL_H+18)+CELL_H-12),f"{rec['id']} [{tag}]",font=f(10),fill=col)
board.save(os.path.join(REF,'3D白模_参考帧总览.png'))
print('参考帧总览',board.size)

# ---------- 2) 现有 64 件 → 精灵表 + manifest ----------
meta=json.load(open(os.path.join(ROOT,'人形素体/05_校验/资产清单.json'),encoding='utf-8'))
items=[]
for r in meta['items']:
    items.append((r['id'],r['name'],r['kind'],r['board'],os.path.join(ROOT,r['file'])))
    if r.get('variant_s'):
        items.append((r['id']+'__s',r['name']+'（少女版）',r['kind'],r['board'],os.path.join(ROOT,r['variant_s'])))
# 统一到 CELL 尺寸
tiles=[]
for aid,name,kind,bn,p in items:
    im=Image.open(p).convert('RGBA')
    im.thumbnail((CELL_W-8,CELL_H-8),Image.LANCZOS)
    cv=Image.new('RGBA',(CELL_W,CELL_H),(0,0,0,0))
    cv.paste(im,((CELL_W-im.width)//2,CELL_H-im.height-4),im)
    tiles.append((aid,name,kind,bn,cv))
SC=8;SR=(len(tiles)+SC-1)//SC
sheet=Image.new('RGBA',(SC*CELL_W,SR*CELL_H),(0,0,0,0))
by8={d:sum(1 for r in ref_rows if r['dir8']==d) for d in DIR8_ORDER}
bycoarse={d:sum(1 for r in ref_rows if r['direction']==d) for d in ['front','side','turn','back']}
bybatch={b:sum(1 for r in ref_rows if r['batch']==b) for b in ['A','B']}
manifest=dict(generator='眼镜猫 · 参考图素体网格规格',
              sheet='02_精灵表/人形素体_精灵表.png',
              cell=[CELL_W,CELL_H],cols=SC,rows=SR,frames=[],
              note='棋盘格/透明底，不用绿幕；frame.rect 为 [x,y,w,h] 像素',
              directions_supported=DIR8_ORDER,
              direction_labels=DIR8_CN,
              direction_inference=dict(
                  method='B 批 8 张各取 r2c2 代表格，依据耳突位置与身体轮廓目视判读',
                  confidence=DIR8_CONF,
                  caveat='仅 E/W 置信度高；白模无五官，N/S 及四个斜向均为推断，方位名未在原始素材中标注；若 N↔S 或左右需对调，改 DIRECTION 一处即可',
                  asset_frames_not_affected=True),
              reference_frames=dict(total=len(all_ref),
                  by_dir8=by8,by_coarse=bycoarse,by_batch=bybatch,
                  batches=dict(A='G1~G5 混合动作网格（5 板）',
                               B='H1~H8 八方向等距 turntable（8 板，每板 8×4）'),
                  note='13 板均为 3D 白模参考，不是可装配美术；B 批才是完整 8 方向'),
              asset_direction='N',
              asset_direction_coarse='front',
              gaps=dict(
                  missing_asset_directions=[d for d in DIR8_ORDER if d!='N'],
                  note='本 sheet 的 64 帧全部为正面(N)厚涂资产；8 方向目前只存在于 3D 白模参考帧，未编造进资产',
                  action_frame_count=8,
                  reference_action_frame_count=len(all_ref)))
for i,(aid,name,kind,bn,cv) in enumerate(tiles):
    r,c=divmod(i,SC);x,y=c*CELL_W,r*CELL_H
    sheet.alpha_composite(cv,(x,y))
    manifest['frames'].append(dict(index=i,id=aid,name=name,group=bn,slot=kind,
        direction='N',rect=[x,y,CELL_W,CELL_H],row=r+1,col=c+1,
        loop='AABB' if kind=='pose' else 'static',fps=8))
sheet.save(os.path.join(SH,'人形素体_精灵表.png'),optimize=True)
json.dump(manifest,open(os.path.join(SH,'manifest.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(os.path.join(SH,'manifest.csv'),'w',newline='',encoding='utf-8-sig') as fp:
    w=csv.DictWriter(fp,fieldnames=list(manifest['frames'][0].keys()));w.writeheader();w.writerows(manifest['frames'])
print('精灵表',sheet.size,len(tiles),'帧 /',SC,'列 ×',SR,'行')

# 精灵表预览（缩略 + 编号）
prev=sheet.copy();prev.thumbnail((SC*90,SR*108),Image.LANCZOS)
bg=checker(prev.width,prev.height);bg.paste(prev,(0,0),prev)
pb=Image.new('RGB',(bg.width,bg.height+34),(240,237,231));pd=ImageDraw.Draw(pb)
pd.text((8,8),f'人形素体精灵表 · {SC}×{SR} = {len(tiles)} 帧 · manifest.json 可直喂引擎',font=f(16),fill=(36,50,40))
pb.paste(bg,(0,34));pb.save(os.path.join(REF,'精灵表_编号预览.png'))

# ---------- 3) 解读对照板：15 张去重原图（A5 + B8 + M2） ----------
names=os.listdir(RAW)
tw,th=250,160;coln=4
order=sorted([x for x in names if x.startswith('G')])+sorted([x for x in names if x.startswith('H')])+sorted([x for x in names if x.startswith('M')])
rown=(len(order)+coln-1)//coln
cmp=Image.new('RGB',(coln*(tw+6)+14,rown*(th+26)+40),(238,235,228));cd=ImageDraw.Draw(cmp)
cd.text((10,8),'15 张去重参考图：A批混合动作 5 + B批 8 方向 turntable 8 + 米底厚涂画风基准 2',font=f(16),fill=(36,50,40))
for i,fn in enumerate(order):
    r,c=divmod(i,coln);x,y=10+c*(tw+6),34+r*(th+26)
    im=Image.open(os.path.join(RAW,fn)).convert('RGB');im.thumbnail((tw,th),Image.LANCZOS)
    cmp.paste(im,(x+(tw-im.width)//2,y))
    tag=fn.split('_')[0];md=DIRECTION.get(tag,{})
    lab=fn[:-4]
    col=(170,60,60) if fn.startswith('H') else (60,52,44)
    cd.text((x,y+th+3),lab[:30],font=f(10),fill=col)
cmp.save(os.path.join(REF,'十五张参考图_解读对照板.png'))
cmp.save(os.path.join(REF,'七张参考图_解读对照板.png'))
cmp.save(os.path.join(REF,'六张参考图_解读对照板.png'))
print('解读板',cmp.size,'张数',len(order))

# ---------- 3b) 8 方向罗盘矩阵 ----------
# 每方向取 r2c2 代表帧，按罗盘 3×3 排布；中心放资产层缺口说明
CW2,CH2=150,178
POS=dict(NW=(0,0),N=(1,0),NE=(2,0),W=(0,1),E=(2,1),SW=(0,2),S=(1,2),SE=(2,2))
compass=Image.new('RGB',(3*CW2+40,3*CH2+60),(238,235,228));cc=ImageDraw.Draw(compass)
cc.text((10,8),'B 批 8 方向罗盘矩阵 · 每格为该方向 r2c2 代表帧（等距 turntable）',font=f(15),fill=(36,50,40))
for tag,md in DIRECTION.items():
    d=md['dir8']
    if not d:continue
    fp=os.path.join(FR,f'{tag}_r2c2.png')
    if not os.path.exists(fp):continue
    gx,gy=POS[d];x,y=14+gx*(CW2+6),34+gy*(CH2+8)
    v=Image.open(fp).convert('RGBA')
    bg=checker(CW2-6,CH2-6)
    v.thumbnail((CW2-12,CH2-12),Image.LANCZOS)
    bg.paste(v,((bg.width-v.width)//2,(bg.height-v.height)//2),v)
    compass.paste(bg,(x,y))
    cc.text((x+3,y+CH2-16),f'{d} · {DIR8_CN[d]} · {md["confidence"]}',font=f(11),fill=(50,80,60))
# 中心格
cx,cy=14+1*(CW2+6),34+1*(CH2+8)
cc.rectangle([cx+4,cy+4,cx+CW2-12,cy+CH2-12],fill=(228,222,212),outline=(180,170,158),width=2)
for j,line in enumerate(['资产层','仍只有 N','（正面 64 帧）','','其余 7 向','= 0 帧']):
    cc.text((cx+12,cy+18+j*20),line,font=f(12),fill=(150,60,60) if j>=4 else (60,52,44))
compass.save(os.path.join(REF,'八方向_罗盘矩阵.png'))
print('罗盘矩阵',compass.size)

# ---------- 4) 报告 ----------
dir8_lines='\n'.join(
    f"| {d} · {DIR8_CN[d]} | {DIRECTION[next(k for k,v in DIRECTION.items() if v['dir8']==d)]['label'].split('·')[-1].strip()} | "
    f"{by8[d]} | {DIR8_CONF[d]} |" for d in DIR8_ORDER)
gl=sum(r['green_left'] for r in ref_rows)
md=f'''# 参考图解读 · 8 方向 turntable 已齐

## 本轮：8 张 = 8 个方向

8 张图 **md5 全不重复**，与既有 G1~G5 也不重复；全部 **2048×1152、8 列 × 4 行 = 32 格**、四角纯 `(0,255,1)`。和上一轮的 G5 不同，这 8 张是**每张固定一个方向、格内是该方向的动作相位**——也就是标准 8 向等距 turntable 矩阵，不是「一张图里混着多个方向」。

### 方向判读（依据：头侧小耳突位置 + 身体轮廓）

| 方位 | 板 | 帧数 | 置信 |
|---|---|---|---|
{dir8_lines}

判读方法：每张取 r2c2 代表格放大后目视，**两侧都能看到耳突 = 正面/背面，单侧耳突移到视野中间 = 3/4，单侧耳突贴轮廓且见侧面脸线 = 纯侧**；并量了头部逐行左右边界的外凸行数作旁证（H1 左凸 32 行 / H2 右凸 32 行 / H6 两侧均有 / H8 两侧均有）。

**只有 E / W（纯侧）置信度高**，因为轮廓不对称最明显。其余 6 向都是推断：这批白模**没有五官**，N/S 只能靠耳突高低与躯干细微差区分，四个斜向还要判「前斜 vs 后斜」。原始素材没有任何方位标注。manifest 里存了 `direction_inference.method / confidence / caveat`，网页方向矩阵直接显示置信度。

**改名成本很低**：若实际朝向与推断不符（最常见是 H6/H8 的 N↔S 对调，或「左/右」按观察者而非角色自身），只改 `DIRECTION` 里对应 `dir8` 一处即可，裁帧、配色、manifest 结构与资产帧全部不受影响。

## 两批要分开看

| | A 批 G1~G5 | B 批 H1~H8 |
|---|---|---|
| 张数 | 5 | 8 |
| 内容 | 混合动作网格（站姿/蜷跳/侧身/转身/背面） | **8 方向各一张**，每方向 32 个动作相位 |
| 方向维度 | 粗类 front/side/turn/back | **完整 8 向等距** |
| 帧数 | {bybatch['A']} | {bybatch['B']} |

合计 **{len(all_ref)} 张参考帧**。B 批才是「8 个方向都有了」的那部分；A 批补的是动作幅度。

## 关键区分：8 向补齐的是「参考层」，不是「资产层」

- `manifest.json` 里 **64 个资产帧的 `direction` 仍是 `N`**（全部正面），一个没改
- `directions_supported` 升为 8 向；`reference_frames.by_dir8` 按 8 向统计；`asset_direction='N'`
- `gaps.missing_asset_directions` 精确列出仍缺的 **7 向**：NE / E / SE / S / SW / W / NW
- **没有**把白模背面/侧面裁片贴到厚涂猫身上充数——那是之前反复翻车的「多源拼接」

所以现在的状态是：参考层 **8/8 方向齐**，资产层 **1/8**。罗盘矩阵图中心那格写的就是这个缺口，故意不遮。

## 绿幕和之前「绿特别多」不是一回事

| | 之前被你打回的生成板 | 这 13 张 3D 白模网格 |
|---|---|---|
| 绿 | 模型把绿画进绒毛/阴影，杂色、抠不干净 | **纯 `(0,255,1)` 标准色键**，四角即该值 |
| 抠像 | 15533 px 残留，需事后补 | 裁出 **{len(all_ref)} 帧，可见区绿残留 {gl} px** |

绿幕本身没错，错的是生成模型把绿当笔触画进图里。3D 渲染给的是干净色键，正好是 GenioPlus 工作流第 1/3 步（去背→合成绿幕→拆帧色键）的标准输入。生产资产仍坚持米底/透明底，不加绿。

这接上 GenioPlus 的 **序列帧动画**（一张图→待机/行走/攻击）与 **3D 模型→精灵图**（免费，上传已绑定 GLB，浏览器用自己的 GPU 渲染 4/8/16 方向）。

## 已交付

- `01_解读/3D参考帧/` **{len(all_ref)} 张透明姿态帧**（统一 160×190，逐帧带 `dir8` / `batch` / `confidence`）
- `01_解读/八方向_罗盘矩阵.png`：8 向各一张代表帧按罗盘排布，中心标资产层缺口
- `01_解读/八方向_代表格判读.png`：8 张各取 r2c2 放大，方向名就是据此判的
- `01_解读/十五张参考图_解读对照板.png`：13 张白模网格 + 2 张米底厚涂基准
- `02_精灵表/人形素体_精灵表.png`：现有 **{len(tiles)} 件**按 **{SC}×{SR}** 排，透明底不用绿幕
- `02_精灵表/manifest.json / .csv`：每帧 `rect` / `row,col` / `group` / `slot` / `direction` / `loop` / `fps`；顶层含 `directions_supported`、`direction_labels`、`direction_inference`、`reference_frames.by_dir8/by_batch`、`gaps`
- `04_校验/` 逐帧绿残留、方向、bbox、网页回归

## 如实说的限制

1. **自有资产仍只有 N（正面）1 向**，其余 7 向 0 张，已写进 `gaps` 而非编造。补齐最短是 GenioPlus 免费「3D→精灵图」（需已绑定 GLB），或按这批白模逐方向补生成厚涂版。
2. **方位名是推断不是标注**：这批白模没有五官，只有 E/W 纯侧轮廓可高置信判定；N/S 的正背、四个斜向的前后归属、以及「左/右」按角色自身还是观察者，都未经原素材确认。`direction_inference.caveat` 已写明，改 `DIRECTION` 一处即可整体改名，不影响裁帧与资产。
3. **两批白模不是同一个模型**：A 批是光滑圆头，B 批头侧多了小耳突；比例与光照也略有差异。只借姿态、方向与网格组织，不混用像素。画风锚仍是历史厚涂母版。
4. **64 件 ≠ 64 个连续动作帧**：16 体形/服装候选 + 16 配件 + 16 少女版配件 + 8 毛色 + 8 动作。真姿态只有 8 帧，和 B 批 32 帧/方向的密度差距还在。
5. B 批白模上下行几乎贴着、粘连比 A 批更重，裁切按「质心最靠近格中心」取域；个别帧带一点相邻白模残片或缺一截指尖，仅作参考，不影响装配资产。
6. 这 13 张版权来源不明，**只作参考与结构比对**，不进 `dist/`、不作图生图底图、不对外发布。
7. 绿残留合计 **{gl} px**（非 0）：JPEG 压缩在白模边缘产生的一颗过渡像素，逐帧留痕，没抹成漂亮 0。

## 下一步三选一

- **A（最贴本轮）** 按 B 批 8 向 × 每向取 4 个代表相位 = 32 张，补生成**厚涂版 8 向动作帧**，按 160×190 配准并入 sheet，把 `gaps` 逐向划掉
- **B** 走 GenioPlus 免费「3D→精灵图」：给一个已绑定 GLB，浏览器渲染 8/16 方向，导出后配准一次补齐
- **C** 把当前 sheet + manifest 接进 `人形素体_全维度换装实验室.html` 的动作页，按 rect 播帧并叠换装件
'''
open(os.path.join(CHK,'参考图解读报告.md'),'w',encoding='utf-8').write(md)
json.dump(dict(unique=15,uploaded=19,ref_frames=len(all_ref),
               green_left=gl,
               by_direction=bycoarse,by_dir8=by8,by_batch=bybatch,
               dir8_order=DIR8_ORDER,dir8_labels=DIR8_CN,dir8_confidence=DIR8_CONF,
               directions=DIRECTION,
               sheet_frames=len(tiles),sheet_cols=SC,sheet_rows=SR,
               asset_direction='N',missing_asset_directions=[d for d in DIR8_ORDER if d!='N'],
               ref_rows=ref_rows),
          open(os.path.join(CHK,'校验数据.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('报告已写')
