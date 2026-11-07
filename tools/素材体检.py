# -*- coding: utf-8 -*-
"""素材体检：检查 素材交付/ 里的东西能不能直接用
只报不猜：尺寸不对、没抠透明、名字不匹配、位置可疑，全部单独列出来。

用法：
  python tools/素材体检.py             # 体检，出 素材交付/体检报告.md
  python tools/素材体检.py --install   # 体检通过的直接装进 assets/
  python tools/素材体检.py --canvas 1328x1776
"""
import os, sys, json, re, shutil, argparse
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DELIVER = os.path.join(ROOT, '素材交付')

EYES = ['E1_平静', 'E2_眨眼', 'E3_笑眼', 'E4_闭眼', 'E5_惊讶']
MOUTHS = ['M1_闭嘴', 'M2_微笑', 'M3_张嘴', 'M4_大笑', 'M5_惊讶圆嘴', 'M6_吐舌']
SUITS = ['神乐', '银时']
PROPS = ['木牌', '手_举起']
DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
FRAMES = 4

SPEC = [
    ('01_表情_眼', EYES, '眼睛层（1328×1776 透明，与 L04+L05 重合）'),
    ('02_表情_嘴', MOUTHS, '嘴层（1328×1776 透明，与 L03 重合）'),
    ('03_配饰_整图', SUITS, '配饰整图（假发+衣身，其余透明）'),
    ('05_道具', PROPS, '道具层（牌子 / 举手替换）'),
]


def imgs(folder):
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(('.png', '.webp', '.tga', '.tif', '.tiff')))


def check_one(path, canvas):
    """返回 (ok, 问题列表, 信息 dict)"""
    problems, info = [], {}
    try:
        im = Image.open(path)
    except Exception as e:
        return False, ['打不开: %s' % e], info
    info['size'] = im.size
    info['mode'] = im.mode
    if im.size != canvas:
        problems.append('尺寸 %d×%d ≠ %d×%d' % (im.size + canvas))
    if im.mode not in ('RGBA', 'LA', 'PA'):
        problems.append('没有 alpha 通道（%s），说明没抠透明' % im.mode)
    else:
        a = im.convert('RGBA').split()[3]
        lo, hi = a.getextrema()
        if lo > 250:
            problems.append('整张不透明（alpha 最小 %d），底没抠掉' % lo)
        info['alpha'] = (lo, hi)
        hist = a.histogram()
        opaque = sum(hist[250:])
        total = im.width * im.height
        info['opaque_ratio'] = round(opaque / total, 4)
        if opaque / total > 0.98:
            problems.append('不透明像素占 %.1f%%，基本是一整块，可能是带底图' % (opaque / total * 100))
        if opaque / total < 0.002:
            problems.append('几乎是空图（不透明 < 0.2%），确认是不是交错了')
        bbox = im.convert('RGBA').getbbox()
        info['bbox'] = bbox
        if bbox:
            w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
            info['content'] = (w, h)
            if bbox[0] <= 1 or bbox[1] <= 1 or bbox[2] >= canvas[0] - 1 or bbox[3] >= canvas[1] - 1:
                problems.append('内容贴到画布边缘，可能被裁过（应保留整块画布）')
    return len(problems) == 0, problems, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--canvas', default='1328x1776')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--src', default=DELIVER)
    a = ap.parse_args()
    cw, ch = [int(x) for x in a.canvas.lower().split('x')]
    canvas = (cw, ch)

    if not os.path.isdir(a.src):
        print('没有交付目录：', a.src); return

    report = ['# 素材体检报告', '', '画布基准：%d×%d' % canvas, '']
    summary = {'ok': 0, 'bad': 0, 'missing': 0}
    installs = []

    # ---- 分层类 ----
    for folder, names, desc in SPEC:
        fdir = os.path.join(a.src, folder)
        files = imgs(fdir)
        report.append('## %s　%s' % (folder, desc))
        if not files:
            report.append('> 空目录。' + ('需 %d 个：%s' % (len(names), '、'.join(names))))
            report.append('')
            summary['missing'] += len(names)
            continue
        by_norm = {os.path.splitext(f)[0]: f for f in files}
        rows = ['| 期望 | 文件 | 尺寸 | 结论 |', '|---|---|---|---|']
        for n in names:
            hit = None
            for k, v in by_norm.items():
                if k == n or k.startswith(n):
                    hit = v; break
            if not hit:
                rows.append('| %s | — | — | ❌ 缺 |' % n)
                summary['missing'] += 1
                continue
            p = os.path.join(fdir, hit)
            ok, probs, info = check_one(p, canvas)
            if ok:
                summary['ok'] += 1
                rows.append('| %s | %s | %s | ✅ |' % (n, hit, '%d×%d' % info['size']))
                installs.append((folder, p, hit))
            else:
                summary['bad'] += 1
                rows.append('| %s | %s | %s | ❌ %s |' % (n, hit, '%d×%d' % info['size'], '；'.join(probs)))
        report += rows + ['']
        extra = [f for f in files if not any(f.startswith(n) for n in names)]
        if extra:
            report.append('未匹配文件（确认要不要改名）：' + '、'.join(extra))
            report.append('')

    # ---- 八向帧 ----
    fdir = os.path.join(a.src, '04_八向帧')
    files = imgs(fdir)
    report.append('## 04_八向帧　8 方向 × 4 帧')
    if not files:
        report.append('> 空目录。需 %d 张：`N_p1.png` … `SW_p4.png`' % (len(DIRS) * FRAMES))
        report.append('（现成可用：`assets/八向资产/03_裁切帧`，可直接搬）')
        report.append('')
        summary['missing'] += len(DIRS) * FRAMES
    else:
        pat = re.compile(r'^(N|NE|E|SE|S|SW|W|NW)_p([1-4])$')
        good, sizes, badnames = [], set(), []
        for f in files:
            k = os.path.splitext(f)[0]
            m = pat.match(k)
            if not m:
                badnames.append(f); continue
            im = Image.open(os.path.join(fdir, f))
            sizes.add(im.size)
            good.append(k)
        report.append('| 项 | 结果 |')
        report.append('|---|---|')
        report.append('| 帧数 | %d / %d |' % (len(good), len(DIRS) * FRAMES))
        report.append('| 尺寸集合 | %s |' % ('、'.join('%d×%d' % s for s in sizes) or '—'))
        if badnames:
            report.append('| 命名不合规 | %s |' % '、'.join(badnames[:8]))
        if len(sizes) > 1:
            report.append('| 结论 | ❌ 尺寸不统一，工具会错位 |')
            summary['bad'] += 1
        elif len(good) == len(DIRS) * FRAMES:
            report.append('| 结论 | ✅ 满帧 |')
            summary['ok'] += 1
        else:
            report.append('| 结论 | ⚠ 缺 %d 帧 |' % (len(DIRS) * FRAMES - len(good)))
            summary['missing'] += len(DIRS) * FRAMES - len(good)
        report.append('')

    # ---- 参考图 ----
    ref = imgs(os.path.join(a.src, '06_参考'))
    report.append('## 06_参考　参考原图')
    report.append('列了 %d 张：%s' % (len(ref), '、'.join(ref[:6]) + ('…' if len(ref) > 6 else '')) if ref else '> 空目录（可选）')
    report.append('')

    # ---- 汇总 ----
    verdict = '✅ 可以装' if summary['bad'] == 0 and summary['missing'] == 0 else \
              ('⚠ 有缺件' if summary['bad'] == 0 else '❌ 有问题件')
    report.insert(4, '**结论：%s**　通过 %d，有问题 %d，缺件 %d' %
                  (verdict, summary['ok'], summary['bad'], summary['missing']))
    report.insert(5, '')

    out = os.path.join(a.src, '体检报告.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print('结论：%s　通过 %d / 有问题 %d / 缺件 %d' % (verdict, summary['ok'], summary['bad'], summary['missing']))
    print('报告：', out)

    # ---- 安装 ----
    if a.install:
        dst = {
            '01_表情_眼': os.path.join(ROOT, 'assets', '单源版', '03_表情层', '眼'),
            '02_表情_嘴': os.path.join(ROOT, 'assets', '单源版', '03_表情层', '嘴'),
            '05_道具': os.path.join(ROOT, 'assets', '单源版', '04_道具层'),
        }
        n = 0
        for folder, p, name in installs:
            if folder in dst:
                tdir = dst[folder]
            elif folder == '03_配饰_整图':
                tdir = os.path.join(ROOT, 'assets', '单源版', '02_配饰层', os.path.splitext(name)[0])
                os.makedirs(tdir, exist_ok=True)
                shutil.copy2(p, os.path.join(tdir, '配饰_假发与衣身.png'))
                n += 1
                continue
            else:
                continue
            os.makedirs(tdir, exist_ok=True)
            shutil.copy2(p, os.path.join(tdir, name))
            n += 1
        print('已装入 %d 个文件。' % n)
        if n:
            print('下一步：在 js/parts.js 的 suits 里加新配饰；表情下拉见 操作模式_对照表.md')


if __name__ == '__main__':
    main()
