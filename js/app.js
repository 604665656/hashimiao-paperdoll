/* 哈士喵 · 纸娃娃台
   操作模型参照 纸娃娃4.0（冒险岛小册子）：部件槽位 / 图层顺序 / 方向帧 / 缩放画布 / 存档导出
   素材：用户自有 哈士喵 八向资产 + 皮套单源版 */
(function () {
  'use strict';

  var A = window.ASSETS;
  var ART_W = A.artW, ART_H = A.artH;
  var FRAME_W = A.frameW, FRAME_H = A.frameH;
  var LS_KEY = 'ymz.zww.v1';
  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };

  /* ---------------- 状态 ---------------- */
  var state = {
    tab: 'dress',
    mode: 'front',              // front | dir
    layers: [],                 // {id,visible,opacity} 自下而上
    suit: null,
    suitPos: 2,
    dir: 'N', frame: 1, fps: 8, playing: true, loop: true,
    useDist: false, onion: false,
    mirror: false, hideBody: false, globalAlpha: 1,
    bg: 'checker', grid: false, gridSize: 64, border: true, pixel: true,
    zoom: 1, panX: 0, panY: 0,
    motion: { breath: true, blink: true, talk: false, tail: 0.55, tilt: 0 }
  };
  var cam = { fit: 1, scale: 1, ox: 0, oy: 0, artW: ART_W, artH: ART_H };
  var IMG = {};          // id -> Image（骨架层/配饰）
  var FRAMES = {};       // url -> Image
  var t0 = performance.now();
  var blink = { v: 0, next: 2200, closing: -1 };

  A.bones.forEach(function (b) { state.layers.push({ id: b.id, visible: true, opacity: 1 }); });

  /* ---------------- 载入图片 ---------------- */
  function loadImg(src) {
    if (FRAMES[src]) return FRAMES[src];
    var im = new Image();
    im.src = encodeURI(src);
    FRAMES[src] = im;
    return im;
  }
  function preloadAll() {
    A.bones.forEach(function (b) { IMG[b.id] = loadImg(A.boneDir + b.file); });
    A.suits.forEach(function (s) { IMG['suit:' + s.id] = loadImg(s.file); });
    // 预取当前向与 dist 帧
    A.dirs.forEach(function (d) {
      for (var i = 1; i <= 4; i++) loadImg(A.dirUrl(d.key, i, false));
    });
    A.distDirs.forEach(function (d) {
      for (var i = 1; i <= 4; i++) loadImg(A.dirUrl(d, i, true));
    });
  }

  /* ---------------- 画布 ---------------- */
  var stage = $('#stage'), cv = $('#cv'), ctx = cv.getContext('2d');

  function artSize() {
    return state.mode === 'dir' ? [FRAME_W, FRAME_H] : [ART_W, ART_H];
  }

  function headPivot() { return [652, 969]; }

  function applyHead(c) {
    var t = state.motion.tilt;
    if (!t) return;
    var p = headPivot();
    c.translate(p[0], p[1]); c.rotate(t * Math.PI / 180); c.translate(-p[0], -p[1]);
  }

  function boneById(id) {
    for (var i = 0; i < A.bones.length; i++) if (A.bones[i].id === id) return A.bones[i];
    return null;
  }

  function drawBone(c, layerState, now) {
    var b = boneById(layerState.id), img = IMG[layerState.id];
    if (!b || !img || !img.complete || !img.naturalWidth) return;
    if (!layerState.visible) return;
    if (state.hideBody && (b.id === 'L01' || b.id === 'L02' || b.id === 'L08' || b.id === 'L09')) return;

    var m = state.motion, mo = b.motion || '';
    c.save();
    c.globalAlpha = layerState.opacity;

    if (mo === 'head' || mo === 'eyes' || mo === 'mouth') applyHead(c);

    if (mo === 'eyes' && blink.v > 0.001) {
      var bx = b.box, cx = (bx[0] + bx[2]) / 2, cy = (bx[1] + bx[3]) / 2;
      c.translate(cx, cy); c.scale(1, 1 - blink.v * 0.92); c.translate(-cx, -cy);
    }
    if (mo === 'mouth' && state.motion.talk) {
      var mb = b.box, mx = (mb[0] + mb[2]) / 2, my = mb[1];
      var amp = 0.35 + 0.35 * Math.abs(Math.sin(now / 130));
      c.translate(mx, my); c.scale(1, 1 + amp); c.translate(-mx, -my);
    }
    if (mo === 'tail' && m.tail > 0) {
      var tb = b.box, px = tb[0] + 6, py = tb[1] + 80;
      c.translate(px, py); c.rotate(Math.sin(now / 640) * 0.075 * m.tail); c.translate(-px, -py);
    }
    c.drawImage(img, 0, 0, ART_W, ART_H);
    c.restore();
  }

  function drawSuit(c) {
    if (!state.suit) return;
    var img = IMG['suit:' + state.suit];
    if (!img || !img.complete || !img.naturalWidth) return;
    c.save();
    c.globalAlpha = state.globalAlpha;
    applyHead(c);
    c.drawImage(img, 0, 0, ART_W, ART_H);
    c.restore();
  }

  function drawFront(c, now) {
    var m = state.motion;
    var breath = m.breath ? Math.sin(now / 1900) * 4 : 0;
    c.save();
    c.translate(0, breath);
    var i, drawnSuit = false;
    for (i = 0; i < state.layers.length; i++) {
      if (!drawnSuit && i === state.suitPos) { drawSuit(c); drawnSuit = true; }
      drawBone(c, state.layers[i], now);
    }
    if (!drawnSuit) drawSuit(c);
    c.restore();
  }

  function frameImg(dir, idx) {
    var url = A.dirUrl(dir, idx, state.useDist);
    return url ? loadImg(url) : null;
  }

  function drawDir(c, now) {
    var im = frameImg(state.dir, state.frame);
    if (state.onion) {
      var p = frameImg(state.dir, state.frame === 1 ? 4 : state.frame - 1);
      var n = frameImg(state.dir, state.frame === 4 ? 1 : state.frame + 1);
      c.save(); c.globalAlpha = 0.22;
      if (p && p.complete) c.drawImage(p, 0, 0, FRAME_W, FRAME_H);
      if (n && n.complete) c.drawImage(n, 0, 0, FRAME_W, FRAME_H);
      c.restore();
    }
    if (im && im.complete && im.naturalWidth) {
      c.imageSmoothingEnabled = !state.pixel;
      c.drawImage(im, 0, 0, FRAME_W, FRAME_H);
    }
  }

  function render() {
    var now = performance.now() - t0;
    var box = stage.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    var w = Math.max(1, Math.round(box.width)), h = Math.max(1, Math.round(box.height));
    if (cv.width !== w * dpr || cv.height !== h * dpr) {
      cv.width = w * dpr; cv.height = h * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    var sz = artSize(), aw = sz[0], ah = sz[1];
    cam.artW = aw; cam.artH = ah;
    var pad = 48;
    cam.fit = Math.min((w - pad * 2) / aw, (h - pad * 2) / ah);
    cam.scale = cam.fit * state.zoom;
    cam.ox = (w - aw * cam.scale) / 2 + state.panX;
    cam.oy = (h - ah * cam.scale) / 2 + state.panY;

    // 画板底色（导出时不含）
    if (state.bg === 'solid' || state.bg === 'white') {
      ctx.fillStyle = state.bg === 'white' ? '#f4f5f7' : '#0d0f14';
      ctx.fillRect(cam.ox, cam.oy, aw * cam.scale, ah * cam.scale);
    }

    ctx.save();
    ctx.translate(cam.ox, cam.oy);
    ctx.scale(cam.scale, cam.scale);

    if (state.grid) {
      ctx.strokeStyle = 'rgba(255,255,255,.07)';
      ctx.lineWidth = 1 / cam.scale;
      for (var gx = 0; gx <= aw; gx += state.gridSize) {
        ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, ah); ctx.stroke();
      }
      for (var gy = 0; gy <= ah; gy += state.gridSize) {
        ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(aw, gy); ctx.stroke();
      }
    }

    if (state.mirror) { ctx.translate(aw, 0); ctx.scale(-1, 1); }
    ctx.imageSmoothingEnabled = !state.pixel;
    if (state.mode === 'dir') drawDir(ctx, now); else drawFront(ctx, now);
    ctx.restore();

    if (state.border) {
      ctx.save();
      ctx.strokeStyle = 'rgba(92,200,255,.45)';
      ctx.lineWidth = 1;
      ctx.strokeRect(cam.ox - .5, cam.oy - .5, aw * cam.scale + 1, ah * cam.scale + 1);
      ctx.restore();
    }

    // 眨眼
    if (state.motion.blink && state.mode === 'front') {
      if (blink.closing >= 0) {
        blink.closing += 16;
        blink.v = blink.closing < 90 ? blink.closing / 90 : Math.max(0, 1 - (blink.closing - 90) / 90);
        if (blink.closing > 180) { blink.closing = -1; blink.v = 0; blink.next = 1800 + Math.random() * 3200; }
      } else {
        blink.next -= 16;
        if (blink.next <= 0) blink.closing = 0;
      }
    } else blink.v = 0;

    // 播放
    if (state.playing && state.mode === 'dir') {
      playAcc += 16;
      var step = 1000 / state.fps;
      if (playAcc >= step) {
        playAcc = 0;
        var nf = state.frame + 1;
        if (nf > 4) { if (state.loop) nf = 1; else { nf = 4; state.playing = false; syncPlayBtn(); } }
        state.frame = nf; syncFrameUI();
      }
    }
    requestAnimationFrame(render);
  }
  var playAcc = 0;

  /* ---------------- 左侧部件库 ---------------- */
  function buildLib() {
    var lib = $('#lib');
    lib.innerHTML = '';
    var q = ($('#q').value || '').trim().toLowerCase();

    A.bones.forEach(function (b, idx) {
      var st = state.layers[idx];
      var row = document.createElement('div');
      row.className = 'slot' + (st.visible ? '' : ' off');
      row.dataset.id = b.id;
      row.innerHTML =
        '<img class="thumb" src="' + encodeURI('assets/thumbs/' + b.id + '.png') + '" alt="">' +
        '<div class="nm"><b>' + b.id + ' ' + b.name + '</b><span>图层 ' + (idx + 1) + ' / 11</span></div>' +
        '<div class="ops"><button data-op="up" title="上移">▲</button><button data-op="dn" title="下移">▼</button></div>' +
        '<span class="eye">' + (st.visible ? '👁' : '⌀') + '</span>';
      if (q && (b.name + ' ' + b.id).toLowerCase().indexOf(q) < 0) row.classList.add('hidden');
      row.addEventListener('click', function (e) {
        var op = e.target.getAttribute && e.target.getAttribute('data-op');
        if (op === 'up') { moveLayer(idx, -1); return; }
        if (op === 'dn') { moveLayer(idx, 1); return; }
        st.visible = !st.visible; buildLib(); persistSoon();
      });
      lib.appendChild(row);
    });

    var sep = document.createElement('div');
    sep.style.cssText = 'padding:8px 12px 4px;color:#8b93a3;font-size:11px;letter-spacing:.6px;border-top:1px solid #2a303c;margin-top:4px';
    sep.textContent = '配饰套装（替换 L07 发型位 / 衣身）';
    lib.appendChild(sep);

    var noneRow = document.createElement('div');
    noneRow.className = 'slot' + (state.suit ? ' off' : '');
    noneRow.innerHTML = '<div class="thumb" style="display:flex;align-items:center;justify-content:center;color:#5a6273">—</div>' +
      '<div class="nm"><b>无配饰（素体）</b><span>只显示骨架层</span></div><span class="eye">' + (state.suit ? '⌀' : '👁') + '</span>';
    noneRow.addEventListener('click', function () { state.suit = null; buildLib(); persistSoon(); });
    if (q && '无配饰 素体'.indexOf(q) < 0) noneRow.classList.add('hidden');
    lib.appendChild(noneRow);

    A.suits.forEach(function (s) {
      var card = document.createElement('div');
      card.className = 'suitcard' + (state.suit === s.id ? ' on' : '');
      card.innerHTML =
        '<img src="' + encodeURI('assets/thumbs/' + s.id + '.png') + '" alt="">' +
        '<div class="row"><b style="flex:1">' + s.name + '</b><span style="color:#8b93a3;font-size:11px">' +
        (state.suit === s.id ? '已装备' : '点击装备') + '</span></div>';
      if (q && s.name.toLowerCase().indexOf(q) < 0) card.classList.add('hidden');
      card.addEventListener('click', function () {
        state.suit = state.suit === s.id ? null : s.id;
        buildLib(); persistSoon();
      });
      lib.appendChild(card);
    });
    $('#slotCount').textContent = '11 槽位 + ' + A.suits.length + ' 配饰';
  }

  function moveLayer(idx, delta) {
    var to = idx + delta;
    if (to < 0 || to >= state.layers.length) return;
    var arr = state.layers;
    var tmp = arr[idx]; arr[idx] = arr[to]; arr[to] = tmp;
    buildLib(); persistSoon();
  }

  /* ---------------- 方向 / 帧按钮 ---------------- */
  function buildDirBtns() {
    var box = $('#dirBtns'); box.innerHTML = '';
    A.dirs.forEach(function (d) {
      var b = document.createElement('button');
      b.textContent = d.key;
      b.title = d.label;
      if (state.dir === d.key) b.classList.add('on');
      if (state.useDist && A.distDirs.indexOf(d.key) < 0) b.disabled = true;
      b.addEventListener('click', function () { state.dir = d.key; buildDirBtns(); updateHud(); persistSoon(); });
      box.appendChild(b);
    });
    var fb = $('#frameBtns'); fb.innerHTML = '';
    for (var i = 1; i <= 4; i++) {
      (function (n) {
        var b = document.createElement('button');
        b.textContent = 'p' + n;
        if (state.frame === n) b.classList.add('on');
        b.addEventListener('click', function () { state.frame = n; state.playing = false; syncPlayBtn(); syncFrameUI(); });
        fb.appendChild(b);
      })(i);
    }
  }

  function syncFrameUI() {
    $$('#frameBtns button').forEach(function (b, i) { b.classList.toggle('on', i + 1 === state.frame); });
    $$('#dots .dot').forEach(function (d, i) { d.classList.toggle('on', i + 1 === state.frame); });
  }
  function syncPlayBtn() {
    var b = $('#btnPlay');
    b.textContent = state.playing ? '❚❚' : '▶';
    b.classList.toggle('on', state.playing);
  }

  function updateHud() {
    var sz = artSize();
    var pct = Math.round(cam.fit * state.zoom * 100);
    if (state.mode === 'dir') {
      $('#hud').innerHTML = '模式 <b>八向帧</b> · ' + state.dir + ' p' + state.frame +
        ' · ' + state.fps + 'fps<br>' + sz[0] + '×' + sz[1] + ' · 视图 ' + pct + '%' +
        (state.useDist ? ' · dist候选' : ' · 裁切帧');
      $('#btnSheet').classList.remove('hidden');
    } else {
      var on = state.layers.filter(function (l) { return l.visible; }).length;
      $('#hud').innerHTML = '模式 <b>正面分层</b> · ' + on + '/11 层可见' +
        (state.suit ? ' · 配饰' + suitName(state.suit) : '') +
        '<br>' + sz[0] + '×' + sz[1] + ' · 视图 ' + pct + '%' + (state.mirror ? ' · 镜像' : '');
    }
    $('#zoomV').textContent = pct + '%';
    $('#zoomR').value = Math.round(state.zoom * 100);
    $('#fpsTag').textContent = state.fps + 'fps';
  }
  function suitName(id) {
    for (var i = 0; i < A.suits.length; i++) if (A.suits[i].id === id) return A.suits[i].name;
    return id;
  }

  /* ---------------- 导出 ---------------- */
  function sceneCanvas(scale, opt) {
    opt = opt || {};
    var sz = opt.size || artSize();
    var c = document.createElement('canvas');
    c.width = Math.round(sz[0] * scale); c.height = Math.round(sz[1] * scale);
    var x = c.getContext('2d');
    x.imageSmoothingEnabled = !state.pixel;
    x.scale(scale, scale);
    if (state.bg === 'solid' || state.bg === 'white') {
      x.fillStyle = state.bg === 'white' ? '#f4f5f7' : '#0d0f14';
      x.fillRect(0, 0, sz[0], sz[1]);
    }
    var savedMirror = state.mirror;
    if (opt.ignoreMirror) state.mirror = false;
    if (state.mirror) { x.translate(sz[0], 0); x.scale(-1, 1); }
    var now = performance.now() - t0;
    if (state.mode === 'dir' && !opt.forceFront) drawDir(x, now); else drawFront(x, now);
    state.mirror = savedMirror;
    return c;
  }

  function download(canvas, name) {
    canvas.toBlob(function (blob) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
    }, 'image/png');
  }

  function stamp() {
    var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; };
    return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '_' + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
  }

  function exportPng(scale) {
    var c = sceneCanvas(scale);
    download(c, '哈士喵_' + (state.mode === 'dir' ? state.dir + '_p' + state.frame : '正面分层') + '_' + stamp() + '.png');
    toast('已导出 PNG ×' + scale);
  }

  function exportSheet() {
    var s = 2, cols = A.dirs.length, rows = 4;
    var c = document.createElement('canvas');
    c.width = FRAME_W * cols * s; c.height = FRAME_H * rows * s;
    var x = c.getContext('2d');
    x.imageSmoothingEnabled = !state.pixel;
    var usedDist = state.useDist;
    state.useDist = false;
    A.dirs.forEach(function (d, ci) {
      for (var r = 0; r < rows; r++) {
        var im = frameImg(d.key, r + 1);
        if (im && im.complete && im.naturalWidth) {
          x.drawImage(im, ci * FRAME_W * s, r * FRAME_H * s, FRAME_W * s, FRAME_H * s);
        }
      }
    });
    state.useDist = usedDist;
    download(c, '哈士喵_八向雪碧图_8x4_' + stamp() + '.png');
    toast('已导出 8 向 × 4 帧雪碧图');
  }

  function exportStrip() {
    var s = 2, c = document.createElement('canvas');
    c.width = FRAME_W * 4 * s; c.height = FRAME_H * s;
    var x = c.getContext('2d');
    x.imageSmoothingEnabled = !state.pixel;
    for (var i = 1; i <= 4; i++) {
      var im = frameImg(state.dir, i);
      if (im && im.complete && im.naturalWidth) x.drawImage(im, (i - 1) * FRAME_W * s, 0, FRAME_W * s, FRAME_H * s);
    }
    download(c, '哈士喵_帧条_' + state.dir + '_' + stamp() + '.png');
    toast('已导出 ' + state.dir + ' 向 4 帧');
  }

  function exportLayers() {
    var i = 0;
    var list = A.bones.slice();
    (function next() {
      if (i >= list.length) { toast('已逐张下载 ' + list.length + ' 个图层'); return; }
      var b = list[i++];
      var img = IMG[b.id];
      if (!img || !img.complete) { next(); return; }
      var c = document.createElement('canvas');
      c.width = ART_W; c.height = ART_H;
      c.getContext('2d').drawImage(img, 0, 0);
      download(c, 'layer_' + b.id + '_' + b.name + '.png');
      setTimeout(next, 420);
    })();
  }

  /* ---------------- 存档 ---------------- */
  function snapshot() {
    return {
      v: 1, mode: state.mode,
      layers: state.layers.map(function (l) { return [l.id, l.visible ? 1 : 0, +l.opacity.toFixed(2)]; }),
      suit: state.suit, suitPos: state.suitPos,
      dir: state.dir, frame: state.frame, fps: state.fps, useDist: state.useDist, onion: state.onion,
      mirror: state.mirror, hideBody: state.hideBody, globalAlpha: state.globalAlpha,
      bg: state.bg, grid: state.grid, gridSize: state.gridSize, border: state.border, pixel: state.pixel,
      motion: state.motion
    };
  }

  function apply(cfg) {
    if (!cfg) return;
    state.mode = cfg.mode || 'front';
    if (cfg.layers && cfg.layers.length === A.bones.length) {
      state.layers = cfg.layers.map(function (a) { return { id: a[0], visible: !!a[1], opacity: a[2] == null ? 1 : a[2] }; });
    }
    state.suit = cfg.suit || null;
    if (cfg.suitPos != null) state.suitPos = cfg.suitPos;
    state.dir = cfg.dir || 'N'; state.frame = cfg.frame || 1; state.fps = cfg.fps || 8;
    state.useDist = !!cfg.useDist; state.onion = !!cfg.onion;
    state.mirror = !!cfg.mirror; state.hideBody = !!cfg.hideBody;
    state.globalAlpha = cfg.globalAlpha == null ? 1 : cfg.globalAlpha;
    state.bg = cfg.bg || 'checker'; state.grid = !!cfg.grid;
    state.gridSize = cfg.gridSize || 64; state.border = cfg.border !== false; state.pixel = cfg.pixel !== false;
    if (cfg.motion) state.motion = Object.assign({}, state.motion, cfg.motion);
    syncAllUI();
  }

  function readStore() {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}'); } catch (e) { return {}; }
  }
  function writeStore(o) {
    try { localStorage.setItem(LS_KEY, JSON.stringify(o)); } catch (e) {}
  }
  var saveTimer = null;
  function persistSoon() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      var s = readStore(); s.last = snapshot(); writeStore(s); updateHud();
    }, 350);
  }

  function renderSaves() {
    var s = readStore(), list = s.saves || [];
    var box = $('#saveList'); box.innerHTML = '';
    $('#saveEmpty').style.display = list.length ? 'none' : 'block';
    list.slice().reverse().forEach(function (item) {
      var i = list.indexOf(item);
      var row = document.createElement('div');
      row.className = 'saveitem';
      row.innerHTML = '<span class="nm">' + item.name + '</span><span class="tm">' +
        new Date(item.ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) +
        '</span><button data-a="del" class="danger" style="padding:1px 6px">删</button>';
      row.addEventListener('click', function (e) {
        if (e.target.getAttribute('data-a') === 'del') {
          list.splice(i, 1); s.saves = list; writeStore(s); renderSaves(); toast('已删除'); return;
        }
        apply(item.cfg); renderSaves(); toast('已载入「' + item.name + '」');
      });
      box.appendChild(row);
    });
  }

  function b64(str) { return btoa(unescape(encodeURIComponent(str))); }
  function unb64(str) { return decodeURIComponent(escape(atob(str))); }

  function copyCode() {
    var code = b64(JSON.stringify(snapshot()));
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code).then(function () { toast('搭配码已复制（' + code.length + ' 字符）'); },
        function () { window.prompt('复制这段搭配码：', code); });
    } else window.prompt('复制这段搭配码：', code);
  }

  function pasteCode() {
    if (!navigator.clipboard || !navigator.clipboard.readText) { toast('浏览器不支持读取剪贴板'); return; }
    navigator.clipboard.readText().then(function (t) {
      try { apply(JSON.parse(unb64(t.trim()))); toast('已从搭配码载入'); }
      catch (e) { toast('搭配码无法识别'); }
    }, function () { toast('读取剪贴板被拒绝'); });
  }

  /* ---------------- UI 同步 ---------------- */
  function syncAllUI() {
    $('#modeFront').classList.toggle('on', state.mode === 'front');
    $('#modeDir').classList.toggle('on', state.mode === 'dir');
    $('#mirror').checked = state.mirror;
    $('#hideBody').checked = state.hideBody;
    $('#globalAlpha').value = Math.round(state.globalAlpha * 100);
    $('#globalAlphaV').textContent = Math.round(state.globalAlpha * 100) + '%';
    $('#suitPos').value = String(state.suitPos);
    $('#mBreath').checked = state.motion.breath;
    $('#mBlink').checked = state.motion.blink;
    $('#mTalk').checked = state.motion.talk;
    $('#mTail').value = Math.round(state.motion.tail * 100);
    $('#mTailV').textContent = Math.round(state.motion.tail * 100);
    $('#mTilt').value = state.motion.tilt;
    $('#mTiltV').textContent = state.motion.tilt + '°';
    $('#gridOn').checked = state.grid;
    $('#gridSize').value = state.gridSize;
    $('#gridSizeV').textContent = state.gridSize;
    $('#borderOn').checked = state.border;
    $('#pixelOn').checked = state.pixel;
    $('#useDist').checked = state.useDist;
    $('#onionOn').checked = state.onion;
    $('#loopOn').checked = state.loop;
    $('#fpsR').value = state.fps;
    $('#fpsV').textContent = state.fps;
    $$('[data-bg]').forEach(function (b) { b.classList.toggle('on', b.dataset.bg === state.bg); });
    stage.className = 'stage' + (state.bg === 'white' ? ' white' : state.bg === 'solid' ? ' solid' : '');
    buildLib(); buildDirBtns(); renderSaves(); updateHud();
  }

  /* ---------------- 事件 ---------------- */
  function bind() {
    $('#tabs').addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      setTab(b.dataset.tab);
    });
    function setTab(tab) {
      state.tab = tab;
      $$('#tabs button').forEach(function (b) { b.classList.toggle('on', b.dataset.tab === tab); });
      ['dress', 'canvas', 'action', 'save'].forEach(function (k) {
        $('#pane-' + k).classList.toggle('hidden', k !== tab);
      });
    }
    window.__setTab = setTab;

    $('#q').addEventListener('input', buildLib);
    $('#btnLib').addEventListener('click', function () {
      document.body.classList.toggle('lib-open');
      document.body.classList.remove('ctl-open');
    });
    $('#btnCtl').addEventListener('click', function () {
      document.body.classList.toggle('ctl-open');
      document.body.classList.remove('lib-open');
    });
    $('#btnRandom').addEventListener('click', randomize);
    $('#btnAllOn').addEventListener('click', function () { state.layers.forEach(function (l) { l.visible = true; }); buildLib(); persistSoon(); });
    $('#btnAllOff').addEventListener('click', function () { state.layers.forEach(function (l) { l.visible = false; }); buildLib(); persistSoon(); });

    $('#mirror').addEventListener('change', function (e) { state.mirror = e.target.checked; persistSoon(); });
    $('#hideBody').addEventListener('change', function (e) { state.hideBody = e.target.checked; persistSoon(); });
    $('#globalAlpha').addEventListener('input', function (e) { state.globalAlpha = e.target.value / 100; $('#globalAlphaV').textContent = e.target.value + '%'; persistSoon(); });
    $('#suitPos').addEventListener('change', function (e) { state.suitPos = +e.target.value; persistSoon(); });

    $('#mBreath').addEventListener('change', function (e) { state.motion.breath = e.target.checked; persistSoon(); });
    $('#mBlink').addEventListener('change', function (e) { state.motion.blink = e.target.checked; persistSoon(); });
    $('#mTalk').addEventListener('change', function (e) { state.motion.talk = e.target.checked; persistSoon(); });
    $('#mTail').addEventListener('input', function (e) { state.motion.tail = e.target.value / 100; $('#mTailV').textContent = e.target.value; persistSoon(); });
    $('#mTilt').addEventListener('input', function (e) { state.motion.tilt = +e.target.value; $('#mTiltV').textContent = e.target.value + '°'; persistSoon(); });

    $$('[data-bg]').forEach(function (b) {
      b.addEventListener('click', function () {
        state.bg = b.dataset.bg;
        $$('[data-bg]').forEach(function (x) { x.classList.toggle('on', x === b); });
        stage.className = 'stage' + (state.bg === 'white' ? ' white' : state.bg === 'solid' ? ' solid' : '');
        persistSoon();
      });
    });
    $('#gridOn').addEventListener('change', function (e) { state.grid = e.target.checked; persistSoon(); });
    $('#gridSize').addEventListener('input', function (e) { state.gridSize = +e.target.value; $('#gridSizeV').textContent = e.target.value; persistSoon(); });
    $('#borderOn').addEventListener('change', function (e) { state.border = e.target.checked; persistSoon(); });
    $('#pixelOn').addEventListener('change', function (e) { state.pixel = e.target.checked; persistSoon(); });

    $('#modeFront').addEventListener('click', function () { state.mode = 'front'; setTab('dress'); $('#modeFront').classList.add('on'); $('#modeDir').classList.remove('on'); updateHud(); persistSoon(); });
    $('#modeDir').addEventListener('click', function () { state.mode = 'dir'; $('#modeDir').classList.add('on'); $('#modeFront').classList.remove('on'); updateHud(); persistSoon(); });
    $('#useDist').addEventListener('change', function (e) { state.useDist = e.target.checked; buildDirBtns(); updateHud(); persistSoon(); });
    $('#fpsR').addEventListener('input', function (e) { state.fps = +e.target.value; $('#fpsV').textContent = e.target.value; $('#fpsTag').textContent = e.target.value + 'fps'; persistSoon(); });
    $('#loopOn').addEventListener('change', function (e) { state.loop = e.target.checked; persistSoon(); });
    $('#onionOn').addEventListener('change', function (e) { state.onion = e.target.checked; persistSoon(); });

    $('#btnPlay').addEventListener('click', function () {
      if (state.mode !== 'dir') { toast('播放只在八向帧模式生效'); return; }
      state.playing = !state.playing; syncPlayBtn();
    });
    $('#btnPng').addEventListener('click', function () { exportPng(1); });
    $('#btnPng2').addEventListener('click', function () { exportPng(1); });
    $('#btnPngX2').addEventListener('click', function () { exportPng(2); });
    $('#btnSheet').addEventListener('click', exportSheet);
    $('#btnSheet2').addEventListener('click', exportSheet);
    $('#btnStrip').addEventListener('click', exportStrip);
    $('#btnLayers').addEventListener('click', exportLayers);

    $('#btnSave').addEventListener('click', function () {
      var name = ($('#saveName').value || '').trim() || ('方案 ' + new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
      var s = readStore(); s.saves = s.saves || [];
      s.saves.push({ name: name, ts: Date.now(), cfg: snapshot() });
      if (s.saves.length > 60) s.saves.shift();
      writeStore(s); renderSaves(); $('#saveName').value = ''; toast('已保存「' + name + '」');
    });
    $('#btnExportJson').addEventListener('click', function () {
      var blob = new Blob([JSON.stringify(snapshot(), null, 2)], { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = '哈士喵_方案_' + stamp() + '.json';
      a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 3000);
    });
    $('#btnImportJson').addEventListener('click', function () { $('#fileJson').click(); });
    $('#fileJson').addEventListener('change', function (e) {
      var f = e.target.files[0]; if (!f) return;
      var r = new FileReader();
      r.onload = function () {
        try { apply(JSON.parse(r.result)); toast('已导入方案'); } catch (err) { toast('文件不是有效方案'); }
      };
      r.readAsText(f);
      e.target.value = '';
    });
    $('#btnCopy').addEventListener('click', copyCode);
    $('#btnCopy2').addEventListener('click', copyCode);
    $('#btnPaste').addEventListener('click', pasteCode);

    $('#btnRefSheet').addEventListener('click', function () { window.open(encodeURI('assets/八向资产/八向候选_精灵表.png'), '_blank'); });
    $('#btnRefCompare').addEventListener('click', function () { window.open(encodeURI('assets/八向资产/02_预览/32帧_声称vs实测方向.png'), '_blank'); });

    // 缩放
    function setZoom(z) { state.zoom = Math.min(4, Math.max(0.1, z)); updateHud(); }
    $('#zIn').addEventListener('click', function () { setZoom(state.zoom * 1.25); });
    $('#zOut').addEventListener('click', function () { setZoom(state.zoom / 1.25); });
    $('#zFit').addEventListener('click', function () { state.zoom = 1; state.panX = 0; state.panY = 0; updateHud(); });
    $('#z100').addEventListener('click', function () { state.zoom = 1 / cam.fit; state.panX = 0; state.panY = 0; updateHud(); });
    $('#zoomR').addEventListener('input', function (e) { setZoom(e.target.value / 100); });
    $('#btnResetView').addEventListener('click', function () { state.zoom = 1; state.panX = 0; state.panY = 0; updateHud(); });
    $('#btnCenter').addEventListener('click', function () { state.panX = 0; state.panY = 0; });

    stage.addEventListener('wheel', function (e) {
      e.preventDefault();
      setZoom(state.zoom * (e.deltaY < 0 ? 1.1 : 0.9));
    }, { passive: false });

    // 拖拽
    var drag = null;
    cv.addEventListener('pointerdown', function (e) {
      drag = { x: e.clientX, y: e.clientY, px: state.panX, py: state.panY };
      cv.classList.add('drag'); cv.setPointerCapture(e.pointerId);
    });
    cv.addEventListener('pointermove', function (e) {
      if (!drag) return;
      state.panX = drag.px + (e.clientX - drag.x);
      state.panY = drag.py + (e.clientY - drag.y);
    });
    cv.addEventListener('pointerup', function () { drag = null; cv.classList.remove('drag'); });
    cv.addEventListener('pointercancel', function () { drag = null; cv.classList.remove('drag'); });

    // 键盘
    window.addEventListener('keydown', function (e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
      var k = e.key.toLowerCase();
      if (k === ' ') { e.preventDefault(); state.playing = !state.playing; syncPlayBtn(); }
      else if (k === 'f') { state.zoom = 1; state.panX = 0; state.panY = 0; updateHud(); }
      else if (k === 'm') { state.mirror = !state.mirror; $('#mirror').checked = state.mirror; }
      else if (k === 'r') randomize();
      else if (k === '1') window.__setTab('dress');
      else if (k === '2') window.__setTab('canvas');
      else if (k === '3') window.__setTab('action');
      else if (k === '4') window.__setTab('save');
      else if (k === 'arrowleft' || k === 'arrowright') {
        state.playing = false; syncPlayBtn();
        var d = k === 'arrowright' ? 1 : -1;
        state.frame = ((state.frame - 1 + d + 4) % 4) + 1;
        syncFrameUI();
      }
    });

    document.querySelectorAll('#dots').forEach(function () {});
  }

  function randomize() {
    var keep = { L01: 1, L02: 1, L04: 1, L05: 1 };
    state.layers.forEach(function (l) {
      l.visible = keep[l.id] ? true : (Math.random() > 0.12);
      l.opacity = 1;
    });
    var opts = [null].concat(A.suits.map(function (s) { return s.id; }));
    state.suit = opts[Math.floor(Math.random() * opts.length)];
    state.motion.tilt = Math.round((Math.random() * 8 - 4));
    state.suitPos = [2, 8, 11][Math.floor(Math.random() * 3)];
    syncAllUI();
    toast('已随机一套');
  }

  var toastTimer = null;
  function toast(msg) {
    var el = $('#toast');
    el.textContent = msg; el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('show'); }, 1900);
  }

  /* ---------------- 启动 ---------------- */
  function boot() {
    preloadAll();
    $('#dots').innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    var store = readStore();
    if (store.last) apply(store.last); else syncAllUI();
    bind();
    // 深链：index.html?tab=action&mode=dir&dir=E&frame=2
    try {
      var q = new URLSearchParams(location.search);
      if (q.get('mode') === 'dir') { state.mode = 'dir'; }
      if (q.get('dir')) state.dir = q.get('dir').toUpperCase();
      if (q.get('frame')) state.frame = Math.min(4, Math.max(1, parseInt(q.get('frame'), 10) || 1));
      if (q.get('suit')) state.suit = q.get('suit');
      if (q.get('tab')) window.__setTab(q.get('tab'));
      syncAllUI();
    } catch (e) {}
    requestAnimationFrame(render);
    setTimeout(function () { syncFrameUI(); updateHud(); syncPlayBtn(); }, 200);
    window.addEventListener('resize', updateHud);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
