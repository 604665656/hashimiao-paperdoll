# 哈士喵 纸娃娃台

角色定名：**哈士喵**。把 纸娃娃4.0 的操作模型搬成本地工具，素材用本项目自有资产。

仓库：https://github.com/604665656/hashimiao-paperdoll　｜　改动记录见 [`开发日记/`](开发日记/)

## 快速开始

1. 双击 `启动.bat` → 浏览器开 `http://127.0.0.1:8777/index.html`
2. 顶栏四个标签：**装扮 / 画布 / 动作 / 存档**（快捷键 1-4）
3. 装扮里点槽位切换显隐，配饰卡片换装；动作里切八向 + 播帧；存档里存方案、复制搭配码

## 目录

```
index.html          主界面
css/app.css         样式（深色，窄屏侧栏自动收成抽屉）
js/app.js           渲染与交互：图层合成、微动、相机、导出、存档
js/parts.js         槽位表 / 配饰表 / 方向表 —— 加部件改这里
assets/单源版/       11 层骨架（1328×1776 同画布）+ 2 套配饰
assets/八向资产/     8 向 × 4 帧（160×190）+ 候选 dist 帧 + 预览校验图
assets/thumbs/      槽位缩略图（脚本生成）
参考卡/              结构参考卡（原创绘制 + 自有剪影）
素材交付/            交付目录骨架 + 素材清单.md + 体检报告.md
素材入库/            截图批处理流水线（inbox → out）
开发日记/            按天记录的改动、决策与坑
tools/               python 脚本与双击入口
操作模式_对照表.md    纸娃娃4.0 能力 → 本地实现 的全量映射
```

## 快捷键

`空格` 播放/暂停 · `F` 适配 · `1-4` 标签 · `←/→` 逐帧 · `M` 镜像 · `R` 随机

## 两条注意

- `assets/` 里是 114MB 原图，换目录要整包一起移动，`js/parts.js` 里是相对路径。
- 本工具没有复制参考站点的任何图片或代码，只复刻了交互模型。

## 克隆后怎么跑

只依赖 Python 标准库和 Pillow / numpy / scipy（只跑网页不需要这些）。

```bash
git clone <repo>
cd 哈士喵纸娃娃台
python -m http.server 8777      # 或直接双击 启动.bat
# 浏览器开 http://127.0.0.1:8777/index.html
```

不要用 `file://` 直接开 `index.html`，中文路径下的图片会加载失败。

## 首次发布（只做一次）

本机没有 `gh`，远端仓库要你在 GitHub Desktop 里点一下创建：

1. GitHub Desktop → File → **Add local repository** → 选这个文件夹
2. 左上出现 **Publish repository** → 点开，**取消勾选 Keep this code private**
3. Publish

之后本机 git 凭据已可用，命令行推送不需要再登录。

## 改完怎么同步

1. 改代码，顺手在 `开发日记/YYYY-MM-DD.md` 追加一条（格式见 `开发日记/README.md`）
2. 双击 `推送.bat "一句话说明"`，自动 add / commit / push

## 许可

代码 MIT。`assets/`、`参考卡/` 里的角色美术保留版权，未许可不单独取用。详见 `LICENSE`。
