window.ASSETS = {
  artW: 1328,
  artH: 1776,
  boneDir: 'assets/单源版/01_骨架层/',
  bones: [
    { id: 'L00', name: '尾巴',      file: 'L00_尾巴.png',      motion: 'tail',  box: [1006, 1013, 1187, 1450] },
    { id: 'L01', name: '身体与双脚', file: 'L01_身体与双脚.png', motion: 'body' },
    { id: 'L02', name: '头部素体',   file: 'L02_头部素体.png',   motion: 'head' },
    { id: 'L03', name: '嘴与舌',     file: 'L03_嘴与舌.png',     motion: 'mouth', box: [580, 812, 736, 988] },
    { id: 'L04', name: '左眼',       file: 'L04_左眼.png',       motion: 'eyes',  box: [388, 585, 588, 785] },
    { id: 'L05', name: '右眼',       file: 'L05_右眼.png',       motion: 'eyes',  box: [742, 585, 942, 785] },
    { id: 'L06', name: '圆框眼镜',   file: 'L06_圆框眼镜.png',   motion: 'head' },
    { id: 'L07', name: '发型位',     file: 'L07_发型位.png',     motion: 'head' },
    { id: 'L08', name: '左手',       file: 'L08_左手.png' },
    { id: 'L09', name: '右手',       file: 'L09_右手.png' },
    { id: 'L10', name: '腰挂位',     file: 'L10_腰挂位.png' }
  ],
  suits: [
    { id: 'hijikata', name: '土方十四郎',
      file: 'assets/单源版/02_配饰层/土方十四郎/配饰_假发与衣身.png',
      preview: 'assets/单源版/02_配饰层/土方十四郎/合成预览.png' },
    { id: 'kagura', name: '神乐',
      file: 'assets/单源版/02_配饰层/神乐/配饰_假发与衣身.png',
      preview: 'assets/单源版/02_配饰层/神乐/合成预览.png' }
  ],
  dirs: [
    { key: 'N',  label: '正前 N', board: '板1_正面背面', token: '板1' },
    { key: 'S',  label: '正后 S', board: '板1_正面背面', token: '板1' },
    { key: 'NE', label: '前斜 NE', board: '板3_前斜',    token: '板3' },
    { key: 'NW', label: '前斜 NW', board: '板3_前斜',    token: '板3' },
    { key: 'E',  label: '右侧 E',  board: '板2_左右侧',  token: '板2' },
    { key: 'W',  label: '左侧 W',  board: '板2_左右侧',  token: '板2' },
    { key: 'SE', label: '后斜 SE', board: '板4_后斜',    token: '板4' },
    { key: 'SW', label: '后斜 SW', board: '板4_后斜',    token: '板4' }
  ],
  distDirs: ['N', 'S', 'E', 'W'],
  frameW: 160,
  frameH: 190,
  framesPerDir: 4
};

(function () {
  var A = window.ASSETS;
  A.dirUrl = function (dir, frame, useDist) {
    if (useDist) {
      if (A.distDirs.indexOf(dir) < 0) return null;
      return 'assets/八向资产/04_候选dist/' + dir + '_p' + frame + '.png';
    }
    var d = A.dirs.filter(function (x) { return x.key === dir; })[0];
    if (!d) return null;
    return 'assets/八向资产/03_裁切帧/' + d.board + '/' + dir + '_p' + frame + '_' + d.token + '.png';
  };
})();
