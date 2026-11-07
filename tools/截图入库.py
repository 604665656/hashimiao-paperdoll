# -*- coding: utf-8 -*-
"""截图入库流水线
把你自己截的整屏 / 精灵表截图，自动切成单只素材：去背 → 切图 → 归一化 → 命名 → 索引 → 总览图。

用法（在 哈士喵纸娃娃台 目录下）：
  python tools/截图入库.py                     # 处理 素材入库/_inbox 下所有图，自动切图
  python tools/截图入库.py --tol 30            # 背景容差调大（JPEG 噪点多时用）
  python tools/截图入库.py --min-area 800      # 过滤小碎块
  python tools/截图入库.py --grid 4x4 --dirs N,NE,E,SE,S,SW,W,NW --frames 4
                                               # 已知网格时按格切，直接命名成 方向_p帧
  python tools/截图入库.py --no-normalize      # 不做统一画布归一化，保留原始裁切尺寸

输出：
  素材入库/out/<前缀>_<方向>_p<帧>_<序号>.png
  素材入库/out/index.json     每个素材的原始坐标、尺寸、面积
  素材入库/out/_总览.png      一页看完，带文件名
注意：只处理你自己获取的截图，不下载、不搬运第三方素材。
"""
import os, sys, json, argparse, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = 'C:/Windows/Fonts/msyh.ttc'


def log(*a):
    print(*a)


def bg_color(im):
    """从四周取样估计背景色（中位数，抗噪）"""
    w, h = im.size
    pts = []
    for x in range(0, w, max(1, w // 24)):
        pts.append(im.getpixel((x, 1)))
        pts.append(im.getpixel((x, h - 2)))
    for y in range(0, h, max(1, h // 24)):
        pts.append(im.getpixel((1, y)))
        pts.append(im.getpixel((w - 2, y)))
    arr = np.array([[p[0], p[1], p[2]] for p in pts])
    return np.median(arr, axis=0)


def fg_mask(im, tol):
    """前景判定：先从边缘泛洪找真背景，再取反。
       这样角色内部和背景同色的区域（奶油色身体 / 白底）不会被挖空。"""
    rgb = np.asarray(im.convert('RGB'), dtype=np.int16)
    bg = bg_color(im).astype(np.int16)
    near = np.abs(rgb - bg).max(axis=2) <= tol
    lab, n = ndimage.label(near)
    if n == 0:
        return ~near
    border = np.zeros_like(near, dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    ids = np.unique(lab[border & near])
    ids = ids[ids != 0]
    if len(ids) == 0:
        return ~near
    bgmask = np.isin(lab, ids)
    if bgmask.mean() > 0.985:      # 泛洪几乎吃掉整张图 → 退回纯色差判定
        return ~near
    return ~bgmask


def split_auto(im, tol, min_area, merge_gap):
    """自动切图：先闭运算合并碎块，再连通域"""
    m = fg_mask(im, tol)
    st = np.ones((3, 3), bool)
    grown = ndimage.binary_dilation(m, st, iterations=merge_gap)
    lab, n = ndimage.label(grown)
    boxes = []
    for sl in ndimage.find_objects(lab):
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        sub = m[y0:y1, x0:x1]
        area = int(sub.sum())
        if area < min_area:
            continue
        ys, xs = np.where(sub)
        if len(xs) == 0:
            continue
        bx0, bx1 = x0 + xs.min(), x0 + xs.max() + 1
        by0, by1 = y0 + ys.min(), y0 + ys.max() + 1
        if bx1 - bx0 < 6 or by1 - by0 < 6:
            continue
        boxes.append((int(bx0), int(by0), int(bx1), int(by1), area))
    return boxes


def split_grid(im, cols, rows, tol, min_area, merge_gap):
    """已知网格切图：每格单独做一次自动切图，避免格子间串图"""
    w, h = im.size
    cw, ch = w / cols, h / rows
    out = []
    for r in range(rows):
        for c in range(cols):
            cx0, cy0 = int(c * cw), int(r * ch)
            cx1, cy1 = int((c + 1) * cw), int((r + 1) * ch)
            cell = im.crop((cx0, cy0, cx1, cy1))
            boxes = split_auto(cell, tol, min_area, merge_gap)
            if not boxes:
                continue
            bx0 = min(b[0] for b in boxes); by0 = min(b[1] for b in boxes)
            bx1 = max(b[2] for b in boxes); by1 = max(b[3] for b in boxes)
            area = sum(b[4] for b in boxes)
            out.append((cx0 + bx0, cy0 + by0, cx0 + bx1, cy0 + by1, area, r, c))
    return out


def row_major_order(boxes):
    """按行优先排序（同一行的 y 容差取中位高度的一半）"""
    if not boxes:
        return boxes
    hs = sorted(b[3] - b[1] for b in boxes)
    tol = max(8, hs[len(hs) // 2] * 0.55)
    ordered = sorted(boxes, key=lambda b: ((b[1] + b[3]) / 2, (b[0] + b[2]) / 2))
    rows, cur, cy = [], [], None
    for b in ordered:
        y = (b[1] + b[3]) / 2
        if cy is None or abs(y - cy) <= tol:
            cur.append(b)
            cy = y if cy is None else (cy * (len(cur) - 1) + y) / len(cur)
        else:
            rows.append(sorted(cur, key=lambda t: t[0])); cur = [b]; cy = y
    if cur:
        rows.append(sorted(cur, key=lambda t: t[0]))
    return [b for r in rows for b in r], rows


def cut(im, box, pad=4, tol=18):
    x0, y0, x1, y1, area = box[:5]
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(im.width, x1 + pad); y1 = min(im.height, y1 + pad)
    crop = im.crop((x0, y0, x1, y1)).convert('RGBA')
    m = Image.fromarray((fg_mask(crop, tol) * 255).astype(np.uint8))
    crop.putalpha(m)
    bb = crop.getbbox()
    if bb:
        crop = crop.crop(bb)
    return crop


def normalize(sprites):
    """统一画布：底边对齐、水平居中，方便直接叠到骨骼位上"""
    W = max(s.width for s in sprites)
    H = max(s.height for s in sprites)
    out = []
    for s in sprites:
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        c.paste(s, ((W - s.width) // 2, H - s.height), s)
        out.append(c)
    return out, (W, H)


def contact_sheet(items, path, cell=180, cols=8):
    if not items:
        return
    rows = math.ceil(len(items) / cols)
    W, H = cols * cell, rows * (cell + 18)
    im = Image.new('RGB', (W, H), (28, 30, 36))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype(FONT, 11)
    except Exception:
        f = ImageFont.load_default()
    for i, (name, sp) in enumerate(items):
        cx = (i % cols) * cell; cy = (i // cols) * (cell + 18)
        s = min((cell - 12) / sp.width, (cell - 12) / sp.height)
        t = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.LANCZOS)
        im.paste(t, (cx + (cell - t.width) // 2, cy + (cell - t.height) // 2), t)
        d.text((cx + 4, cy + cell + 2), name[:26], font=f, fill=(160, 168, 180))
    im.save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inbox', default=os.path.join(ROOT, '素材入库', '_inbox'))
    ap.add_argument('--out', default=os.path.join(ROOT, '素材入库', 'out'))
    ap.add_argument('--prefix', default='素材')
    ap.add_argument('--tol', type=int, default=24, help='背景容差，JPEG 噪点多就调到 30-40')
    ap.add_argument('--min-area', type=int, default=600)
    ap.add_argument('--merge-gap', type=int, default=3, help='同一只的碎块合并距离')
    ap.add_argument('--grid', default='', help='已知网格，如 4x4')
    ap.add_argument('--dirs', default='N,NE,E,SE,S,SW,W,NW')
    ap.add_argument('--frames', type=int, default=4)
    ap.add_argument('--no-normalize', action='store_true')
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    if not os.path.isdir(a.inbox):
        os.makedirs(a.inbox, exist_ok=True)
        log('已创建 %s，把截图丢进去再跑一次。' % a.inbox)
        return

    files = [f for f in sorted(os.listdir(a.inbox))
             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))]
    if not files:
        log('inbox 里没有图片：%s' % a.inbox)
        return

    dirs = [d.strip() for d in a.dirs.split(',') if d.strip()]
    grid = None
    if a.grid:
        try:
            c, r = a.grid.lower().split('x')
            grid = (int(c), int(r))
        except Exception:
            log('--grid 格式应为 4x4，已忽略'); grid = None

    all_index, sheet_items, total = [], [], 0
    for fn in files:
        p = os.path.join(a.inbox, fn)
        try:
            im = Image.open(p).convert('RGBA')
        except Exception as e:
            log('跳过（打不开）', fn, e); continue

        if grid:
            boxes = split_grid(im, grid[0], grid[1], a.tol, a.min_area, a.merge_gap)
            names = []
            for b in boxes:
                r, c = b[5], b[6]
                if grid[0] == len(dirs):          # 列=方向，行=帧
                    names.append('%s_%s_p%d' % (a.prefix, dirs[c], r + 1))
                elif grid[1] == len(dirs):        # 行=方向，列=帧
                    names.append('%s_%s_p%d' % (a.prefix, dirs[r], c + 1))
                else:
                    names.append('%s_r%dc%d' % (a.prefix, r + 1, c + 1))
            log('%s  网格 %dx%d → %d 格' % (fn, grid[0], grid[1], len(boxes)))
        else:
            boxes = split_auto(im, a.tol, a.min_area, a.merge_gap)
            boxes, rows = row_major_order(boxes)
            names = []
            ri = 0
            for bi, b in enumerate(boxes):
                names.append('%s_%02d' % (a.prefix, bi + 1))
            log('%s  %d×%d → 切出 %d 个（%d 行）' % (fn, im.width, im.height, len(boxes), len(rows)))

        sprites = [cut(im, b, tol=a.tol) for b in boxes]
        keep = [(n, s, b) for n, s, b in zip(names, sprites, boxes) if s.width > 5 and s.height > 5]
        if not keep:
            log('  没切出东西，调小 --min-area 或调大 --tol')
            continue
        names = [k[0] for k in keep]
        sprites = [k[1] for k in keep]

        if not a.no_normalize:
            sprites, canvas = normalize(sprites)
        else:
            canvas = (0, 0)

        base = os.path.splitext(fn)[0]
        for n, s, b in zip(names, sprites, [k[2] for k in keep]):
            out_name = ('%s.png' % n) if (len(files) == 1 or grid) else ('%s_%s.png' % (base, n))
            s.save(os.path.join(a.out, out_name))
            all_index.append({
                'file': out_name, 'source': fn,
                'box': [b[0], b[1], b[2], b[3]],
                'w': s.width, 'h': s.height,
                'area': b[4],
                'normalized_canvas': list(canvas)
            })
            sheet_items.append((out_name, s))
            total += 1

    with open(os.path.join(a.out, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump({'count': total, 'canvas': list(canvas) if not a.no_normalize else None,
                   'items': all_index}, f, ensure_ascii=False, indent=2)
    contact_sheet(sheet_items, os.path.join(a.out, '_总览.png'))
    log('完成：%d 个素材 → %s' % (total, a.out))
    log('索引：index.json   总览：_总览.png')


if __name__ == '__main__':
    main()
