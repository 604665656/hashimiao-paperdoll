#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4 张 8 格拼板 → 32 张候选透明帧；自适应裁切 + 绿/手数/相位差异/方向判读自检。

诚实原则：生成帧一律标 status=candidate，不冒充可装配资产；
方向以「轮廓与 8 向白模代表帧的 Hu 矩相似度」实测为准，不采信 prompt 声称的方向。
"""
import os, json, csv, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT='/data/workspace'; B=os.path.join(ROOT,'八向资产')
BOARDS=os.path.join(B,'01_拼板原图'); OUT=os.path.join(B,'03_裁切帧')
PREV=os.path.join(B,'02_预览'); CHK=os.path.join(B,'05_校验')
for d in (OUT,PREV,CHK): os.makedirs(d,exist_ok=True)
FONT='/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
def f(s): return ImageFont.truetype(FONT,s)

CW,CH,FOOT=160,190,178
ORDER=['N','NE','E','SE','S','SW','W','NW']
LAB=dict(N='正面',NE='右前斜',E='右侧',SE='右后斜',S='背面',SW='左后斜',W='左侧',NW='左前斜')
# 每板上排/下排的「声称方向」（prompt 里要求的）
CLAIM={
 '板1_正面背面':(['N']*4, ['S']*4),
 '板2_左右侧'  :(['E']*4, ['W']*4),
 '板3_前斜'    :(['NE']*4,['NW']*4),
 '板4_后斜'    :(['SE']*4,['SW']*4),
}
PHASE=['并脚站立','迈左腿','双腿交错','迈右腿']
REF=os.path.join(ROOT,'参考图_素体网格/01_解读/3D参考帧')
REFBOARD=dict(N='H6',NE='H2',E='H3',SE='H7',S='H8',SW='H5',W='H4',NW='H1')

# ---------- 复用历史自检 ----------
def skeletonize(binary):
    img=binary.astype(np.uint8).copy()
    for _ in range(60):
        prev=img.copy()
        for step in (0,1):
            P=np.pad(img,1);p2,p3,p4,p5=P[:-2,1:-1],P[:-2,2:],P[1:-1,2:],P[2:,2:]
            p6,p7,p8,p9=P[2:,1:-1],P[2:,:-2],P[1:-1,:-2],P[:-2,:-2]
            nb=p2+p3+p4+p5+p6+p7+p8+p9
            seq=[p2,p3,p4,p5,p6,p7,p8,p9,p2]
            trans=sum(((seq[i]==0)&(seq[i+1]==1)).astype(np.uint8) for i in range(8))
            cond=(p2*p4*p6==0)&(p4*p6*p8==0) if step==0 else (p2*p4*p8==0)&(p2*p6*p8==0)
            img[(img==1)&(nb>=2)&(nb<=6)&(trans==1)&cond]=0
        if np.array_equal(img,prev):break
    return img.astype(bool)

def bg_color(rgb):
    h,w=rgb.shape[:2]
    c=np.concatenate([rgb[:50,:50].reshape(-1,3),rgb[:50,-50:].reshape(-1,3),
                      rgb[-50:,:50].reshape(-1,3),rgb[-50:,-50:].reshape(-1,3)])
    return np.median(c,0)

def foreground(rgb,thr=15):
    bg=bg_color(rgb)
    diff=np.abs(rgb.astype(np.float32)-bg).sum(2)
    m=(diff>thr).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    # 全板右下角 AI 水印
    h,w=m.shape;m[int(h*.87):,int(w*.86):]=0
    return m

def cells_from_mask(m,H,W):
    """自适应找 8 个小人：先用行投影分 2 行，每行再按列投影找 4 个峰。"""
    rowsig=m.sum(1).astype(float)
    rsm=cv2.GaussianBlur(rowsig.reshape(-1,1),(1,0),0).ravel() if False else rowsig
    on=rowsig>H*0.004
    seg=[];s=None
    for k,z in enumerate(on):
        if z and s is None:s=k
        if not z and s is not None:
            if k-s>H*0.10:seg.append((s,k-1))
            s=None
    if s is not None:seg.append((s,len(on)-1))
    # 合并过近、取最高两行
    if len(seg)>2:
        seg=sorted(seg,key=lambda q:(q[1]-q[0]),reverse=True)[:2]
        seg=sorted(seg)
    if len(seg)<2: return []
    out=[]
    for ri,(y0,y1) in enumerate(seg):
        band=m[y0:y1+1]
        colsig=band.sum(0).astype(float)
        con=colsig>W*0.002
        xs=[];s=None
        for k,z in enumerate(con):
            if z and s is None:s=k
            if not z and s is not None:
                if k-s>W*0.025:xs.append((s,k-1))
                s=None
        if s is not None:xs.append((s,len(con)-1))
        # 合并相邻峰（一个角色内部可能断开）
        merged=[]
        for a,b in xs:
            if merged and a-merged[-1][1]<W*0.02:merged[-1]=(merged[-1][0],b)
            else:merged.append((a,b))
        if len(merged)>4:
            merged=sorted(merged,key=lambda q:(q[1]-q[0]),reverse=True)[:4]
            merged=sorted(merged)
        if len(merged)<4:return []
        for ci,(x0,x1) in enumerate(merged[:4]):
            out.append((ri,ci,x0,y0,x1,y1))
    return out

def alpha_from_cell(crop):
    bg=bg_color(crop)
    diff=np.abs(crop.astype(np.float32)-bg).sum(2)
    m=(diff>13).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    h,w=m.shape;m[int(h*.88):,int(w*.86):]=0
    n,lab,st,_=cv2.connectedComponentsWithStats(m,8)
    if n<=1:return np.zeros_like(m,np.uint8)
    k=1+np.argmax(st[1:,4])
    out=(lab==k).astype(np.uint8)*255
    out=cv2.morphologyEx(out,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    cnts=cv2.findContours(out,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
    fill=np.zeros_like(out)
    for c in cnts:
        if cv2.contourArea(c)>120:cv2.drawContours(fill,[c],-1,255,-1)
    a=cv2.GaussianBlur(fill.astype(np.float32),(0,0),0.9)
    return np.clip(a,0,255).astype(np.uint8)

def fit(rgba):
    im=Image.fromarray(rgba,'RGBA')
    x0,y0,x1,y1=im.getbbox()[0],im.getbbox()[1],im.getbbox()[2],im.getbbox()[3]
    im=im.crop((x0,y0,x1+1,y1+1))
    s=min((CH-14)/im.height,(CW-12)/im.width,1.0)
    nw,nh=max(1,int(im.width*s)),max(1,int(im.height*s))
    im=im.resize((nw,nh),Image.LANCZOS)
    out=Image.new('RGBA',(CW,CH),(0,0,0,0))
    out.paste(im,((CW-nw)//2,FOOT-nh),im)
    return out

def endpoints(a):
    m=cv2.GaussianBlur((a>18).astype(np.uint8)*255,(0,0),1.5)
    m=(m>110).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    sk=skeletonize(m>0)
    nb=cv2.filter2D(sk.astype(np.uint8),-1,np.ones((3,3),np.uint8))-sk.astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(((sk)&(nb==1)).astype(np.uint8),8)
    return max(0,n-1)

def bbox(a):
    ys,xs=np.where(a>18)
    return (int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())) if len(xs) else (0,0,0,0)

# ---------- 方向判读：轮廓 Hu 矩匹配 8 向白模代表帧 ----------
def ref_contours():
    out={}
    for d in ORDER:
        p=os.path.join(REF,f'{REFBOARD[d]}_r2c2.png')
        a=np.array(Image.open(p).convert('RGBA'))[...,3]
        m=(a>18).astype(np.uint8)*255
        m=cv2.resize(m,(CW,CH),interpolation=cv2.INTER_NEAREST)
        cs=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
        c=max(cs,key=cv2.contourArea) if cs else None
        out[d]=c
    return out
REFC=ref_contours()
def guess_dir(a):
    m=(a>18).astype(np.uint8)*255
    cs=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
    if not cs:return '?',{}
    c=max(cs,key=cv2.contourArea)
    sc={d:cv2.matchShapes(c,REFC[d],cv2.CONTOURS_MATCH_I1,0) for d in ORDER if REFC[d] is not None}
    best=min(sc,key=sc.get)
    return best,{k:round(v,4) for k,v in sc.items()}

def main():
    rows=[];frames={}
    for bn in ['板1_正面背面','板2_左右侧','板3_前斜','板4_后斜']:
        p=os.path.join(BOARDS,bn+'.png')
        rgb=np.array(Image.open(p).convert('RGB'));H,W=rgb.shape[:2]
        m=foreground(rgb)
        cs=cells_from_mask(m,H,W)
        print(bn,'检出格',len(cs),[(c[0],c[1],c[2],c[4]) for c in cs])
        claim=CLAIM[bn]
        od=os.path.join(OUT,bn);os.makedirs(od,exist_ok=True)
        for ri,ci,x0,y0,x1,y1 in cs:
            d_claim=claim[0][ci] if ri==0 else claim[1][ci]
            ph=PHASE[ci]
            pad=8
            crop=rgb[max(0,y0-pad):min(H,y1+pad+1),max(0,x0-pad):min(W,x1+pad+1)]
            a=alpha_from_cell(crop)
            rgba=np.dstack([crop,a])
            im=fit(rgba)
            arr=np.array(im);al=arr[...,3]
            green=int(((arr[...,1].astype(int)>arr[...,0].astype(int)+30)&
                       (arr[...,1].astype(int)>arr[...,2].astype(int)+30)&(al>18)).sum())
            x,y,x2,y2=bbox(al)
            hard=int(x<=0 or y<=0 or x2>=CW-1 or y2>=CH-1)
            n,lab,st,_=cv2.connectedComponentsWithStats((al>18).astype(np.uint8),8)
            inv=(al<=18).astype(np.uint8);n2,l2,s2,_=cv2.connectedComponentsWithStats(inv,8)
            holes=sum(1 for k in range(1,n2) if 0<s2[k,0] and 0<s2[k,1]
                      and s2[k,0]+s2[k,2]<CW and s2[k,1]+s2[k,3]<CH and 20<s2[k,4]<2000)
            gd,scores=guess_dir(al)
            aid=f'{d_claim}_p{ci+1}_{bn[:2]}'
            fp=os.path.join(od,aid+'.png');im.save(fp,optimize=True)
            frames[aid]=im
            rows.append(dict(id=aid,board=bn,row=ri+1,col=ci+1,phase=ph,
                claimed_dir=d_claim,measured_dir=gd,dir_scores=scores,
                status='candidate',file=os.path.relpath(fp,ROOT),
                alpha_px=int((al>18).sum()),green_left=green,hard_edge=hard,
                blobs=n-1,holes=holes,skeleton_endpoints=endpoints(al),
                bbox=[x,y,x2,y2],src_box=[x0,y0,x1,y1]))
    # 相位差异（同板同行 4 帧两两 alpha XOR）
    for bn in CLAIM:
        for ri in (1,2):
            ids=[r['id'] for r in rows if r['board']==bn and r['row']==ri]
            if len(ids)<4:continue
            sig=[]
            for a,b in zip(ids,ids[1:]):
                m1=np.array(frames[a])[...,3]>18;m2=np.array(frames[b])[...,3]>18
                sig.append(round(float(np.logical_xor(m1,m2).sum()/max(1,m1.sum())),4))
            for r in rows:
                if r['board']==bn and r['row']==ri:r['phase_diff_mean']=round(sum(sig)/len(sig),4)
    # 板间重复：各板第 1 帧互相 Hu 距离
    firsts=[r['id'] for r in rows if r['col']==1 and r['row']==1]
    cross={}
    for i,a in enumerate(firsts):
        for b in firsts[i+1:]:
            m1=(np.array(frames[a])[...,3]>18).astype(np.uint8)*255
            m2=(np.array(frames[b])[...,3]>18).astype(np.uint8)*255
            c1=max(cv2.findContours(m1,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],key=cv2.contourArea)
            c2=max(cv2.findContours(m2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],key=cv2.contourArea)
            cross[a+'|'+b]=round(cv2.matchShapes(c1,c2,cv2.CONTOURS_MATCH_I1,0),4)
    # 实测方向覆盖
    cover={d:sum(1 for r in rows if r['measured_dir']==d) for d in ORDER}
    # ---------- 候选精灵表：8 列（方向）× 4 行（相位），按声称方向填 ----------
    SC,SR=8,4
    sheet=Image.new('RGBA',(SC*CW,SR*CH),(0,0,0,0))
    sheet_rows=[]
    for ci,d in enumerate(ORDER):
        cand=[r for r in rows if r['claimed_dir']==d]
        cand=sorted(cand,key=lambda r:r['col'])
        for pi in range(4):
            rec=cand[pi] if pi<len(cand) else None
            if rec:
                sheet.alpha_composite(frames[rec['id']],(ci*CW,pi*CH))
            sheet_rows.append(dict(index=pi*SC+ci,dir8=d,phase=PHASE[pi],
                id=rec['id'] if rec else None,
                measured_dir=rec['measured_dir'] if rec else None,
                rect=[ci*CW,pi*CH,CW,CH],row=pi+1,col=ci+1,
                status='candidate' if rec else 'missing'))
    sheet.save(os.path.join(B,'八向候选_精灵表.png'))
    # ---------- 诊断总览 ----------
    cellw,cellh=130,155
    pv=Image.new('RGB',(8*cellw+20,4*(cellh+22)+44),(240,237,231));d=ImageDraw.Draw(pv)
    d.text((10,8),'32 张候选帧 · 列=声称方向 行=走路相位 · 红字=实测方向与声称不符',font=f(18),fill=(36,50,40))
    for pi,ph in enumerate(PHASE):
        for ci,dd in enumerate(ORDER):
            rec=next((r for r in sheet_rows if r['dir8']==dd and r['phase']==ph),None)
            x,y=10+ci*cellw,34+pi*(cellh+22)
            bg=Image.new('RGBA',(cellw-6,cellh-6),(236,232,225,255));p=bg.load()
            for yy in range(0,bg.height,12):
                for xx in range(0,bg.width,12):
                    if (xx//12+yy//12)%2:p[xx,yy]=(206,200,192,255)
            if rec and rec['id']:
                v=frames[rec['id']].copy();v.thumbnail((cellw-14,cellh-24),Image.LANCZOS)
                bg.alpha_composite(v,((bg.width-v.width)//2,bg.height-v.height-10))
            pv.paste(bg.convert('RGB'),(x,y))
            mis=rec and rec['measured_dir'] and rec['measured_dir']!=dd
            col=(190,60,60) if mis else (60,54,46)
            d.text((x+2,y+cellh-14),f'{dd}→{rec["measured_dir"] if rec and rec["measured_dir"] else "—"}',font=f(10),fill=col)
    pv.save(os.path.join(PREV,'32帧_声称vs实测方向.png'))

    # ---------- 输出 ----------
    summary=dict(total=len(rows),canvas=[CW,CH],foot_y=FOOT,
        status='candidate',generation_notes=dict(
            board1='图生图，输入=厚涂Q版纯素体身份锚 + 正/背白模姿态卡',
            board2_4='文生图（同 seed=5，无输入图）：因单次请求输入图额度已用满',
            all_pure_cream_bg=True,green_ratio=0.0),
        measured_direction_coverage=cover,
        claimed_direction_coverage={d:sum(1 for r in rows if r['claimed_dir']==d) for d in ORDER},
        mismatch=sum(1 for r in rows if r['measured_dir']!=r['claimed_dir']),
        cross_board_similarity=cross,
        items=rows,sheet=sheet_rows)
    json.dump(summary,open(os.path.join(CHK,'候选自检.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    with open(os.path.join(CHK,'候选自检.csv'),'w',newline='',encoding='utf-8-sig') as fp:
        keys=['id','board','row','col','phase','claimed_dir','measured_dir','status',
              'alpha_px','green_left','hard_edge','blobs','holes','skeleton_endpoints','phase_diff_mean','file']
        w=csv.DictWriter(fp,fieldnames=keys,extrasaction='ignore');w.writeheader()
        for r in rows:w.writerow(r)
    print('总帧',len(rows),'实测覆盖',cover,'不符',summary['mismatch'])
    print('跨板相似度',cross)
    print('绿残留',sum(r['green_left'] for r in rows),'硬边',sum(r['hard_edge'] for r in rows),
          '洞',sum(r['holes'] for r in rows),'孤立域',sum(r['blobs']-1 for r in rows))
    print('相位差异均值',{bn:round(float(np.mean([r.get('phase_diff_mean',0) for r in rows if r['board']==bn])),4) for bn in CLAIM})
    return summary

if __name__=='__main__':main()
