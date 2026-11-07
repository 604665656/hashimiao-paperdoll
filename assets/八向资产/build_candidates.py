#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 32 张原始候选里挑出可用子集，做毛色归一化与合法镜像，产出 16 帧 4 向候选。

不做的：不把 3 张重复板的帧硬塞进 8 向、不把镜像帧冒充模型独立绘制、不把候选转正。
"""
import os,json,csv,shutil
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
ROOT='/data/workspace';B=os.path.join(ROOT,'八向资产')
OUT=os.path.join(B,'04_候选dist');PREV=os.path.join(B,'02_预览');CHK=os.path.join(B,'05_校验')
for d in (OUT,PREV,CHK):os.makedirs(d,exist_ok=True)
FONT='/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
def f(s):return ImageFont.truetype(FONT,s)
CW,CH=160,190
ORDER=['N','NE','E','SE','S','SW','W','NW']
LAB=dict(N='正面',NE='右前斜',E='右侧',SE='右后斜',S='背面',SW='左后斜',W='左侧',NW='左前斜')
PHASE=['并脚站立','迈左腿','双腿交错','迈右腿']
src=json.load(open(os.path.join(CHK,'候选自检.json'),encoding='utf-8'))
items=src['items']
def get(board,row,col):
    return next(r for r in items if r['board']==board and r['row']==row and r['col']==col)
def load(r):return Image.open(os.path.join(ROOT,r['file'])).convert('RGBA')
def fgmean(im):
    a=np.array(im);m=a[...,3]>60
    return a[...,:3][m].mean(0)
# 目标肤色 = 板1（图生图，身份锚那张）整体前景均值
boards1=[load(get('板1_正面背面',1,c)) for c in range(1,5)]+[load(get('板1_正面背面',2,c)) for c in range(1,5)]
TARGET=np.mean([fgmean(x) for x in boards1],0)
def normalize(im):
    a=np.array(im).astype(np.float32)
    s=fgmean(im)
    gain=np.clip(TARGET/np.maximum(s,1),0.80,1.20)
    a[...,:3]=np.clip(a[...,:3]*gain,0,255)
    return Image.fromarray(a.astype(np.uint8),'RGBA')
print('目标肤色',[round(x,1) for x in TARGET])
# ---------- 16 帧 ----------
REC=[]
# N / S：板1，原样（图生图身份锚那批）
for d,row in [('N',1),('S',2)]:
    for c in range(1,5):
        r=get('板1_正面背面',row,c);im=load(r)
        REC.append(dict(dir8=d,phase=c-1,src=r['id'],method='图生图原始',im=im))
# E：板2 上排（朝右走路），做毛色归一化
for c in range(1,5):
    r=get('板2_左右侧',1,c);im=normalize(load(r))
    REC.append(dict(dir8='E',phase=c-1,src=r['id'],method='毛色归一化',im=im))
# W：E 水平镜像（等距变换，不是形变）
for c in range(1,5):
    e=next(x for x in REC if x['dir8']=='E' and x['phase']==c-1)
    im=e['im'].transpose(Image.FLIP_LEFT_RIGHT)
    REC.append(dict(dir8='W',phase=c-1,src=e['src'],method='E 水平镜像',im=im))
# 落盘 + 量化
rows=[]
for x in REC:
    aid=f"{x['dir8']}_p{x['phase']+1}"
    p=os.path.join(OUT,aid+'.png');x['im'].save(p,optimize=True)
    a=np.array(x['im']);al=a[...,3]
    m=al>60
    rows.append(dict(id=aid,dir8=x['dir8'],dir_cn=LAB[x['dir8']],phase=PHASE[x['phase']],
        source=x['src'],method=x['method'],status='candidate',
        file=os.path.relpath(p,ROOT),alpha_px=int((al>18).sum()),
        fg_rgb=[round(float(v),1) for v in a[...,:3][m].mean(0)],
        green_left=int(((a[...,1].astype(int)>a[...,0].astype(int)+30)&
                        (a[...,1].astype(int)>a[...,2].astype(int)+30)&(al>18)).sum())))
# 相位差异（每向 4 帧）
for d in ['N','E','S','W']:
    ids=[x for x in REC if x['dir8']==d]
    sig=[]
    for a,b in zip(ids,ids[1:]):
        m1=np.array(a['im'])[...,3]>18;m2=np.array(b['im'])[...,3]>18
        sig.append(float(np.logical_xor(m1,m2).sum()/max(1,m1.sum())))
    for r in rows:
        if r['dir8']==d:r['phase_diff_mean']=round(sum(sig)/len(sig),4)
# 色统一性：4 向前景 RGB 两两欧氏距离
fg={d:np.mean([np.array(x['im'])[...,:3][np.array(x['im'])[...,3]>60].mean(0)
               for x in REC if x['dir8']==d],0) for d in ['N','E','S','W']}
colordiff={a+'|'+b:round(float(np.linalg.norm(fg[a]-fg[b])),2)
           for i,a in enumerate(['N','E','S','W']) for b in ['N','E','S','W'][i+1:]}
# ---------- 8 列 × 4 行候选精灵表（斜向 4 格留空，透明） ----------
SC,SR=8,4
sheet=Image.new('RGBA',(SC*CW,SR*CH),(0,0,0,0));sheet_rows=[]
for ci,d in enumerate(ORDER):
    for pi in range(4):
        rec=next((x for x in REC if x['dir8']==d and x['phase']==pi),None)
        if rec:sheet.alpha_composite(rec['im'],(ci*CW,pi*CH))
        sheet_rows.append(dict(index=pi*SC+ci,dir8=d,phase=PHASE[pi],
            id=f'{d}_p{pi+1}' if rec else None,
            rect=[ci*CW,pi*CH,CW,CH],row=pi+1,col=ci+1,
            status='candidate' if rec else 'not_generated'))
sheet.save(os.path.join(B,'八向候选_精灵表_4向.png'))
json.dump(dict(cell=[CW,CH],cols=SC,rows=SR,status='candidate',
               directions=ORDER,labels=LAB,phases=PHASE,
               covered=['N','E','S','W'],not_generated=['NE','SE','SW','NW'],
               frames=sheet_rows),
          open(os.path.join(CHK,'候选精灵表_manifest.json'),'w',encoding='utf-8'),
          ensure_ascii=False,indent=2)
# ---------- 预览 ----------
cellw,cellh=132,158
pv=Image.new('RGB',(8*cellw+20,4*(cellh+24)+46),(240,237,231));dd=ImageDraw.Draw(pv)
dd.text((10,8),'16 帧候选（4 向 × 4 相位）· 斜向 4 列留空 = 本轮未生成 · 全部 status=candidate',font=f(17),fill=(36,50,40))
for pi in range(4):
    for ci,d in enumerate(ORDER):
        x,y=10+ci*cellw,34+pi*(cellh+24)
        bg=Image.new('RGBA',(cellw-6,cellh-6),(236,232,225,255));p=bg.load()
        for yy in range(0,bg.height,12):
            for xx in range(0,bg.width,12):
                if (xx//12+yy//12)%2:p[xx,yy]=(206,200,192,255)
        rec=next((a for a in REC if a['dir8']==d and a['phase']==pi),None)
        if rec:
            v=rec['im'].copy();v.thumbnail((cellw-14,cellh-26),Image.LANCZOS)
            bg.alpha_composite(v,((bg.width-v.width)//2,bg.height-v.height-10))
        else:
            dr=ImageDraw.Draw(bg);dr.rectangle([6,6,bg.width-7,bg.height-7],outline=(196,186,174),width=2)
            dr.text((bg.width//2-30,bg.height//2-8),'未生成',font=f(12),fill=(170,150,140))
        pv.paste(bg.convert('RGB'),(x,y))
        dd.text((x+2,y+cellh-14),f'{d} {LAB[d]}',font=f(10),fill=(60,54,46))
pv.save(os.path.join(PREV,'16帧候选_四向总览.png'))
# 色归一前后对比
cmp=Image.new('RGB',(4*180+20,2*220+40),(240,237,231));cd=ImageDraw.Draw(cmp)
cd.text((10,8),'毛色归一化前后（左=原始暖黄，右=统一到板1 灰白奶油）',font=f(15),fill=(36,50,40))
for c in range(4):
    r=get('板2_左右侧',1,c+1);raw=load(r);norm=next(x['im'] for x in REC if x['dir8']=='E' and x['phase']==c)
    for j,im in enumerate([raw,norm]):
        bg=Image.new('RGBA',(170,200),(236,232,225,255))
        v=im.copy();v.thumbnail((150,180),Image.LANCZOS)
        bg.alpha_composite(v,((bg.width-v.width)//2,10))
        cmp.paste(bg.convert('RGB'),(10+c*180,30+j*220))
    cd.text((10+c*180,30+2*220-16),f'相位{c+1}',font=f(11),fill=(60,54,46))
cmp.save(os.path.join(PREV,'毛色归一化_前后对比.png'))
# ---------- 更新主 manifest（只加候选段，不改资产帧 direction） ----------
MP=os.path.join(ROOT,'参考图_素体网格/02_精灵表/manifest.json')
man=json.load(open(MP,encoding='utf-8'))
man['candidates']=dict(
    status='candidate_not_approved',
    sheet='/data/workspace/八向资产/八向候选_精灵表_4向.png',
    cell=[CW,CH],cols=SC,rows=SR,
    covered=['N','E','S','W'],not_generated=['NE','SE','SW','NW'],
    frames=sheet_rows,
    method=dict(N='板1 上排，图生图（厚涂身份锚 + 正/背姿态卡）',
                S='板1 下排，同上',
                E='板2 上排，毛色归一化到板1 肤色',
                W='E 水平镜像（等距变换，非形变，非模型独立绘制）'),
    rejected=dict(board1_phases='正/背 4 相位差异仅 0.0446，几乎静止',
                  boards_2_4='三张板彼此轮廓相似度 0.11~0.18，模型收敛到同一个朝右走路姿态，未画出前斜/后斜',
                  direction_claim='32 帧中 30 帧与 prompt 声称方向不符；Hu 矩对无五官光头角色判别力有限，结论以目视为准',
                  original_32='保留在 八向资产/03_裁切帧/，不进 dist'),
    note='这些帧全部未转正；asset frames 的 direction 仍全部为 N，gaps 不变')
man['gaps']['candidate_coverage']=['N','E','S','W']
man['gaps']['candidate_note']='候选层 4/8 可演示，但未经人眼挑选，不计入可装配资产；8 向资产层仍只有 N 的 64 帧'
json.dump(man,open(MP,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
# ---------- 报告 ----------
md=f'''# 8 向厚涂候选 · 本轮自检（未转正）

## 先说结论：这批生成**没达标**，不冒充 8 向资产

用户上一轮确认「8 个方向都有了」的是**参考层**（13 张 3D 白模网格 / 412 帧）。这轮尝试把**资产层**从 1/8 往前推，结果是：

| 项 | 结果 |
|---|---|
| 4 张拼板 → 32 帧 | 全部裁出，绿残留 **0** / 硬切边 **0** / alpha 内部洞 **0** / 孤立连通域 **0** |
| 多手少手 | **0**（人形 2 手 2 脚，结构上治住了） |
| 绿色 | **0**（纯米白底，源头没有绿幕） |
| 声称 8 向 | **30 / 32 帧与声称方向不符**（目视复核：实际只画出「正面 / 背面 / 朝右走路」3 类） |
| 板2 / 3 / 4 | 三张板轮廓两两 Hu 距离 **0.11~0.18**，模型收敛到同一个朝右姿态，上下排也没镜像 |
| 画风 | 板1 灰白厚涂（前景 RGB {[round(float(v),1) for v in TARGET]}）；板2~4 暖黄淡彩（约 238/225/207），**两套笔触** |
| 相位 | 侧面走路 4 相位差异 0.088~0.105（真有迈腿）；板1 正/背 4 相位仅 0.0446（几乎静止） |

**Hu 矩判读只作相对参考**：这批角色光头无五官、轮廓圆润，Hu 矩对正/背、左右镜像不敏感，判出的「N 21 帧」不等于真的都是正面。最终以 `02_预览/32帧_声称vs实测方向.png` 的目视为准。

## 做了什么补救（都是工程处理，不是掩盖）

1. **毛色归一化**：把板2~4 的前景 RGB 按逐通道增益映射到板1 的灰白奶油色（增益约 0.91/0.90/0.91），保留笔触明暗关系。这正好是你要的「毛色可以替换」，不是修图掩盖。前后对比见 `02_预览/毛色归一化_前后对比.png`。
2. **合法镜像补 W**：把 E（朝右走路）水平翻转得到 W（朝左走路）。镜像是等距变换，不是你否掉的「拉动 / 形变 / 橡皮式伸缩」；但 manifest 里如实标 `method='E 水平镜像'`，**不冒充模型独立绘制**。
3. **只挑可用子集**：N / S 取板1，E 取板2 归一化，W 由 E 镜像 → **16 帧 / 4 向**。板3、板4 的重复帧和 4 个斜向全部不塞进表，精灵表里那 4 列直接留空写「未生成」。

## 交付的候选（全部 status=candidate）

- `04_候选dist/` 16 张透明 PNG，160×190，接地点 y=178
- `八向候选_精灵表_4向.png` 8 列 × 4 行，配 `05_校验/候选精灵表_manifest.json`（每帧 rect / row / col / dir8 / status）
- 主 `manifest.json` 只**新增** `candidates` 段与 `gaps.candidate_coverage`；**64 个资产帧的 direction 仍是 N，一个没改**，gaps 仍列 7 向缺口
- 原始 32 帧保留在 `03_裁切帧/`，不进 dist

## 从失败里得到的具体改法（下一轮照这个做）

- **一张板只画一个方向**：这轮每张板塞了 2 个方向，模型把两排都画成同一个姿态。改成 8 张板 × 每板 1 方向 × 4 相位，方向靠单独一张姿态卡锁死。
- **全部走图生图**：板1（图生图，传了厚涂身份锚）画风最准；板2~4 因输入图额度用满改走文生图，直接漂成暖黄淡彩。下一轮 8 板都传身份锚 + 单方向姿态卡。
- **正/背要加区分信号**：光头无五官时正背几乎一样，得在姿态卡里保留耳突与肩背线，或允许素体带极淡的背部中线。

## 如实说的限制

1. **4 个斜向 NE / SE / SW / NW 本轮 0 帧**，不是「画了但没挑」，是模型根本没画出来。
2. **W 是镜像**，不是独立绘制；左右对称部件（耳突、描边高光）会跟着翻，严格设定稿仍需原画补画。
3. 16 帧全是候选，**没人眼挑过就不转正**；网页里的挑图标记就是为这一步做的。
4. 生成时单次请求的输入图额度用满（10 张），所以板2~4 改走文生图，这是画风漂移的直接原因，不是模型能力定论。
5. 仍是整图序列帧，不是 PSD/ORA 分层；换装是叠层预览，做不到骨骼级联动。

## 文件

```
八向资产/
  00_生成输入/    厚涂身份锚 + 4 张方向姿态卡
  01_拼板原图/    4 张 2048×1152 纯米底拼板
  02_预览/        四板总览 / 32 帧声称vs实测 / 16 帧候选 / 色归一前后
  03_裁切帧/      32 张原始候选透明帧（未转正）
  04_候选dist/    16 张 4 向候选帧（色归一 + 镜像）
  05_校验/        候选自检 json/csv、候选精灵表 manifest、本报告
  八向候选_精灵表_4向.png
  cut_check.py / build_candidates.py
```
'''
open(os.path.join(CHK,'候选自检报告.md'),'w',encoding='utf-8').write(md)
with open(os.path.join(CHK,'16帧候选清单.csv'),'w',newline='',encoding='utf-8-sig') as fp:
    w=csv.DictWriter(fp,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
json.dump(dict(target_rgb=[round(float(v),1) for v in TARGET],colordiff=colordiff,
               phase_diff={d:next(r['phase_diff_mean'] for r in rows if r['dir8']==d) for d in ['N','E','S','W']},
               rows=rows),open(os.path.join(CHK,'16帧候选清单.json'),'w',encoding='utf-8'),
          ensure_ascii=False,indent=2)
print('16 帧已出；4 向覆盖 N/E/S/W；色差',colordiff)
print('相位差异',{d:next(r['phase_diff_mean'] for r in rows if r['dir8']==d) for d in ['N','E','S','W']})
print('主 manifest 已加 candidates 段；资产帧 direction 未改')
