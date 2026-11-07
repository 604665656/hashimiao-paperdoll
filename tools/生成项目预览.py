# -*- coding: utf-8 -*-
"""生成仓库首页预览图（README 用）
三块：素体 / 神乐配饰 / 八向帧，全部由本项目自有素材现场合成，不含第三方素材。
用法：python tools/生成项目预览.py
"""
import os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1600, 900
BG = (15, 17, 21)
CARD = (26, 30, 38)
LINE = (44, 50, 62)
TXT = (230, 233, 239)
DIM = (139, 147, 163)
GREEN = (125, 211, 160)

F = 'C:/Windows/Fonts/msyh.ttc'
FB = 'C:/Windows/Fonts/msyhbd.ttc'


def font(sz, bold=False):
    try:
        return ImageFont.truetype(FB if bold else F, sz)
    except Exception:
        return ImageFont.load_default()


def compose(suit=None, suit_pos=2):
    """按 app.js 的分层顺序合成正面图"""
    base = os.path.join(ROOT, 'assets', '单源版', '01_骨架层')
    man = json.load(open(os.path.join(base, 'manifest.json'), encoding='utf-8'))
    im = Image.new('RGBA', (1328, 1776), (0, 0, 0, 0))
    order = [l['file'] for l in man['layers']]
    suit_img = None
    if suit:
        p = os.path.join(ROOT, 'assets', '单源版', '02_配饰层', suit, '配饰_假发与衣身.png')
        if os.path.exists(p):
            suit_img = Image.open(p).convert('RGBA')
    for i, fn in enumerate(order):
        if suit and i == suit_pos and suit_img:
            im = Image.alpha_composite(im, suit_img)
        im = Image.alpha_composite(im, Image.open(os.path.join(base, fn)).convert('RGBA'))
    if suit and suit_pos >= len(order) and suit_img:
        im = Image.alpha_composite(im, suit_img)
    return im


def fit(im, box_w, box_h):
    s = min(box_w / im.width, box_h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def main():
    canvas = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(canvas)

    d.text((60, 46), '哈士喵 纸娃娃台', font=font(54, True), fill=TXT)
    d.text((62, 116), '本地运行的纸娃娃编辑器：11 层骨架合成 · 换装 · 八向帧 · 一键导出', font=font(22), fill=DIM)

    cards = [(60, '素体（11 层叠加）'), (560, '神乐套（配饰层）'), (1060, '八向帧（素体 · 8 向 × 4 帧）')]
    top, box_h = 210, 560
    for x, title in cards:
        d.rounded_rectangle([x, top, x + 460, top + box_h], radius=16, fill=CARD, outline=LINE, width=1)
        d.text((x + 24, top + 20), title, font=font(22, True), fill=TXT)

    body = compose(None)
    im_a = fit(body, 400, 470)
    canvas.paste(im_a, (90 + (400 - im_a.width) // 2, top + 70), im_a)

    body2 = compose('神乐')
    im_b = fit(body2, 400, 470)
    canvas.paste(im_b, (590 + (400 - im_b.width) // 2, top + 70), im_b)

    base = os.path.join(ROOT, 'assets', '八向资产', '03_裁切帧')
    frames = [('N', '板1_正面背面', '板1'), ('NE', '板3_前斜', '板3'),
              ('E', '板2_左右侧', '板2'), ('S', '板1_正面背面', '板1')]
    fw, fh = 200, 238
    for i, (k, folder, token) in enumerate(frames):
        p = os.path.join(base, folder, '%s_p1_%s.png' % (k, token))
        if not os.path.exists(p):
            continue
        f = Image.open(p).convert('RGBA')
        f = f.resize((fw, fh), Image.LANCZOS)
        fx = 1080 + (i % 2) * 210
        fy = top + 72 + (i // 2) * 250
        canvas.paste(f, (fx, fy), f)
        d.text((fx + 4, fy + fh + 6), k, font=font(16), fill=DIM)
    d.text((1082, top + box_h - 34), '帧为素体，用于动作结构；换装效果见左两栏', font=font(14), fill=DIM)

    d.line([(60, H - 96), (W - 60, H - 96)], fill=LINE, width=1)
    d.text((60, H - 78), '操作模型参照 纸娃娃4.0，未使用其图片与代码　·　素材为本项目自有资产', font=font(17), fill=DIM)
    d.text((60, H - 50), 'github.com/604665656/hashimiao-paperdoll', font=font(17), fill=GREEN)

    out = os.path.join(ROOT, 'docs', '预览.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out, optimize=True)
    print(out, canvas.size, os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
