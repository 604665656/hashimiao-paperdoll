# -*- coding: utf-8 -*-
"""生成两张结构参考卡（原创绘制，不含任何第三方 IP 素材）
  90_结构参考_比例与衣褶.png  头身比 / 衣褶类型 / 重心与动态线
  91_八向骨架比例卡.png        哈士喵自有八向帧 → 剪影 + 中轴 + 刻度
用法：python tools/参考卡生成.py
"""
import os, math, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, '参考卡')
os.makedirs(OUT, exist_ok=True)

PAPER = (244, 241, 234)
INK = (54, 50, 44)
INK2 = (108, 101, 90)
RED = (176, 74, 58)
BLUE = (70, 104, 142)
GREEN = (86, 122, 92)

F = 'C:/Windows/Fonts/msyh.ttc'
FB = 'C:/Windows/Fonts/msyhbd.ttc'
def font(sz, bold=False):
    try: return ImageFont.truetype(FB if bold else F, sz)
    except Exception: return ImageFont.load_default()

def dashed(d, p1, p2, fill, width=1, dash=7, gap=6):
    x1, y1 = p1; x2, y2 = p2
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1: return
    n = int(L // (dash + gap)) + 1
    for i in range(n):
        a = i * (dash + gap) / L
        b = min(1, (i * (dash + gap) + dash) / L)
        d.line([(x1 + (x2 - x1) * a, y1 + (y2 - y1) * a),
                (x1 + (x2 - x1) * b, y1 + (y2 - y1) * b)], fill=fill, width=width)

def bez(p0, p1, p2, n=28):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out

# ---------------------------------------------------------------- 90 结构参考
def card_struct():
    W, H = 1800, 1500
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)

    d.text((60, 40), '结构参考卡 · 比例 / 衣褶 / 重心', font=font(38, True), fill=INK)
    d.text((62, 92), '用于 img2img 结构约束：只提供骨架比例与褶皱逻辑，不含角色特征', font=font(19), fill=INK2)
    d.line([(60, 128), (W - 60, 128)], fill=INK, width=2)

    # ---------- A 头身比 ----------
    d.text((60, 150), 'A  头身比（chibi 3 头 / 卡通 4 头 / 少年 6 头）', font=font(24, True), fill=INK)
    base_y = 660
    specs = [(3, 110, 200), (4, 95, 480), (6, 76, 770)]
    for units, head, cx in specs:
        top = base_y - units * head
        d.ellipse([cx - head * 0.42, top, cx + head * 0.42, top + head], outline=INK, width=3, fill=(255, 255, 255))
        ty0 = top + head
        ty1 = top + head * (units - 1.15)
        d.polygon([(cx - head * 0.34, ty0 + 6), (cx + head * 0.34, ty0 + 6),
                   (cx + head * 0.26, ty1), (cx - head * 0.26, ty1)], outline=INK, fill=(252, 250, 246))
        d.line([(cx - head * 0.34, ty0 + 6), (cx + head * 0.34, ty0 + 6)], fill=INK, width=3)
        knee = ty1 + (base_y - ty1) * 0.45
        for s in (-1, 1):
            d.line([(cx + s * head * 0.16, ty1), (cx + s * head * 0.19, knee)], fill=INK, width=8)
            d.line([(cx + s * head * 0.19, knee), (cx + s * head * 0.17, base_y)], fill=INK, width=7)
        for s in (-1, 1):
            d.line([(cx + s * head * 0.32, ty0 + 10), (cx + s * head * 0.5, ty1 - 2)], fill=INK, width=6)
        for u in range(units + 1):
            y = top + u * head
            dashed(d, (cx - 150, y), (cx + 110, y), (203, 197, 187), 1, 5, 7)
            d.text((cx - 172, y - 9), str(u), font=font(13), fill=INK2)
        d.text((cx - 44, base_y + 18), '%d 头身' % units, font=font(21, True), fill=INK)
        d.text((cx - 78, base_y + 48), '头高 %dpx 为基准' % head, font=font(14), fill=INK2)
    d.text((60, 748), '规则：先定头高，再乘头身数得全身高；肩宽≈1.2 头宽，腰宽≈0.8 头宽，膝在总高 0.28 处。',
           font=font(16), fill=INK2)

    # ---------- B 衣褶 ----------
    bx = 1000
    d.text((bx, 150), 'B  衣褶四型（褶皱永远跟着重力与支点走）', font=font(24, True), fill=INK)
    cell_w, cell_h = 396, 250
    types = ['管状褶', '之字褶', '放射褶', '悬垂褶']
    tips = ['布被两点拉扯时的圆柱状折痕', '宽松布料的连续 Z 形堆叠', '从肩/腰一个支点向外散开', '两点悬挂形成的下垂弧线']
    for i in range(4):
        cx = bx + (i % 2) * cell_w
        cy = 196 + (i // 2) * cell_h
        d.rectangle([cx, cy, cx + cell_w - 24, cy + cell_h - 26], outline=(214, 208, 198), width=2)
        d.text((cx + 16, cy + 10), types[i], font=font(21, True), fill=INK)
        d.text((cx + 16, cy + 40), tips[i], font=font(14), fill=INK2)
        if i == 0:
            for k in range(5):
                x = cx + 60 + k * 54
                d.line(bez((x, cy + 84), (x + 18, cy + 150), (x - 12, cy + 204)), fill=INK, width=3)
        elif i == 1:
            for j, x0 in enumerate((cx + 46, cx + 176)):
                pts = [(x0, cy + 92)]
                for k in range(6):
                    pts.append((x0 + (k % 2) * 46 + 10, cy + 116 + k * 18))
                d.line(pts, fill=INK if j == 0 else INK2, width=3 if j == 0 else 2, joint='curve')
        elif i == 2:
            ox, oy = cx + 168, cy + 82
            for a in range(28, 162, 16):
                r = math.radians(a)
                d.line([(ox, oy), (ox + math.cos(r) * 148, oy + math.sin(r) * 138)], fill=INK, width=2)
            d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=RED)
        else:
            d.line(bez((cx + 66, cy + 90), (cx + 186, cy + 200), (cx + 300, cy + 94)), fill=INK, width=3)
            d.line(bez((cx + 82, cy + 94), (cx + 186, cy + 214), (cx + 286, cy + 98)), fill=INK2, width=2)
            d.line(bez((cx + 98, cy + 98), (cx + 186, cy + 226), (cx + 272, cy + 102)), fill=INK2, width=1)

    # ---------- C 重心与动态线 ----------
    cy0 = 800
    d.line([(60, cy0 - 18), (W - 60, cy0 - 18)], fill=(214, 208, 198), width=2)
    d.text((60, cy0), 'C  重心 / 动态线 / 支点', font=font(24, True), fill=INK)
    poses = [('站直', 0), ('S 形', 1), ('走姿', 2)]
    top, bot = cy0 + 80, cy0 + 440
    for i, (nm, mode) in enumerate(poses):
        cx = 260 + i * 300
        hh = (bot - top) * 0.26
        d.ellipse([cx - hh * .42, top, cx + hh * .42, top + hh], outline=INK, width=3, fill=(255, 255, 255))
        if mode == 0:
            pts = [(cx, top + hh), (cx, bot)]
        elif mode == 1:
            pts = [(cx + 26, top + hh), (cx - 18, (top + bot) / 2), (cx + 20, bot - 40)]
        else:
            pts = [(cx - 10, top + hh), (cx + 14, (top + bot) / 2), (cx - 22, bot - 30)]
        d.line(pts, fill=INK, width=12, joint='curve')
        d.line([(pts[-1][0], pts[-1][1] - 10), (pts[0][0] + (18 if mode == 1 else -6), pts[0][1] + hh * .4)],
               fill=BLUE, width=2)
        gx = pts[1][0]
        dashed(d, (gx, top + hh * .5), (gx, bot + 40), RED, 2, 9, 7)
        if mode == 0:
            d.line([(gx - 58, bot + 40), (gx + 58, bot + 40)], fill=GREEN, width=4)
        elif mode == 2:
            d.line([(gx - 66, bot + 40), (gx + 30, bot + 40)], fill=GREEN, width=4)
        else:
            d.ellipse([gx - 24, bot + 34, gx + 24, bot + 46], outline=GREEN, width=3)
        d.text((cx - 22, bot + 62), nm, font=font(19, True), fill=INK)

    d.text((1120, cy0 + 78), '三条通用的线', font=font(20, True), fill=INK)
    notes = [('红虚线', '重心线：从胸骨上端垂直下落，必须落在支撑面内'),
             ('蓝实线', '动态线：脊柱到承重脚的连续弧线，别画成直的'),
             ('绿实线', '支撑面：脚底受力区域，重心出界就是“要摔”'),
             ('球+柱', '关节一律先当球体，四肢当圆柱，再包肌肉与布料')]
    for i, (k, v) in enumerate(notes):
        y = cy0 + 120 + i * 48
        d.text((1120, y), k, font=font(16, True), fill=RED if i == 0 else (BLUE if i == 1 else (GREEN if i == 2 else INK)))
        d.text((1200, y), v, font=font(16), fill=INK2)

    d.text((60, H - 40), '哈士喵纸娃娃台 · 结构参考卡（原创绘制，可自由用于本项目）', font=font(15), fill=INK2)
    p = os.path.join(OUT, '90_结构参考_比例与衣褶.png')
    im.save(p, optimize=True)
    return p

# ---------------------------------------------------------------- 91 八向剪影
def card_silhouette():
    A_DIRS = [('N', '板1_正面背面', '板1'), ('S', '板1_正面背面', '板1'),
              ('NE', '板3_前斜', '板3'), ('NW', '板3_前斜', '板3'),
              ('E', '板2_左右侧', '板2'), ('W', '板2_左右侧', '板2'),
              ('SE', '板4_后斜', '板4'), ('SW', '板4_后斜', '板4')]
    base = os.path.join(ROOT, 'assets', '八向资产', '03_裁切帧')
    cell_w, cell_h = 330, 520
    cols, rows = 4, 2
    W, H = cell_w * cols + 120, cell_h * rows + 190
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.text((60, 34), '八向骨架比例卡', font=font(36, True), fill=INK)
    d.text((62, 84), '剪影 + 中轴 + 十等分刻度：只约束外形轮廓与重心，不含五官与配色', font=font(18), fill=INK2)
    d.line([(60, 116), (W - 60, 116)], fill=INK, width=2)

    meta = []
    for i, (key, folder, token) in enumerate(A_DIRS):
        p = os.path.join(base, folder, '%s_p1_%s.png' % (key, token))
        cell_x = 60 + (i % cols) * cell_w
        cell_y = 132 + (i // cols) * cell_h
        if not os.path.exists(p):
            d.rectangle([cell_x, cell_y, cell_x + cell_w - 30, cell_y + cell_h - 40], outline=(220, 120, 120), width=2)
            d.text((cell_x + 12, cell_y + 12), key + ' 缺帧', font=font(18), fill=RED)
            continue
        src = Image.open(p).convert('RGBA')
        a = src.split()[3]
        bbox = a.getbbox()
        if not bbox:
            continue
        crop = src.crop(bbox)
        mask = a.crop(bbox)
        # 缩放到统一高度，边缘先平滑再二值化，轮廓不毛刺
        target_h = 400
        s = target_h / crop.height
        nw, nh = max(1, int(crop.width * s)), target_h
        m2 = mask.resize((nw, nh), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
        m2 = m2.point(lambda v: 255 if v > 118 else 0)
        sil = Image.new('RGBA', (nw, nh), (0, 0, 0, 0))
        sil.paste(Image.new('RGBA', (nw, nh), (232, 226, 214, 255)), (0, 0), m2)
        ox = cell_x + (cell_w - 40) // 2 - nw // 2
        oy = cell_y + 40
        im.paste(sil, (ox, oy), sil)
        # 轮廓：原掩膜减去腐蚀后的掩膜 = 1px 干净边线
        inner = m2.filter(ImageFilter.MinFilter(3))
        edge = ImageChops.subtract(m2, inner)
        im.paste(Image.new('RGBA', (nw, nh), INK + (255,)), (ox, oy), edge)
        # 中轴
        cx = ox + nw // 2
        dashed(d, (cx, oy - 14), (cx, oy + nh + 14), RED, 1, 6, 6)
        # 刻度
        for k in range(11):
            y = oy + nh * k / 10
            d.line([(ox - 8, y), (ox - 2, y)], fill=INK2, width=1)
            if k % 2 == 0:
                d.text((ox - 30, y - 8), str(k * 10), font=font(11), fill=INK2)
        d.line([(ox, oy + nh), (ox + nw, oy + nh)], fill=GREEN, width=2)
        d.text((cell_x + 12, cell_y + 8), '%s  %s' % (key, '朝前' if key in ('N', 'NE', 'NW') else '朝后' if key in ('S', 'SE', 'SW') else '侧面'),
               font=font(20, True), fill=INK)
        d.text((cell_x + 12, cell_y + cell_h - 34), '%d×%d 源  宽高比 %.2f' % (crop.width, crop.height, crop.width / crop.height),
               font=font(12), fill=INK2)
        meta.append({'dir': key, 'w': crop.width, 'h': crop.height, 'ratio': round(crop.width / crop.height, 3)})

    p = os.path.join(OUT, '91_八向骨架比例卡.png')
    im.save(p, optimize=True)
    with open(os.path.join(OUT, '91_八向骨架比例卡.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return p

if __name__ == '__main__':
    print(card_struct())
    print(card_silhouette())
