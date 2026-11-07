#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os,json,asyncio
from playwright.async_api import async_playwright
ROOT='/data/workspace'
P='file://'+os.path.join(ROOT,'参考图_素体网格/03_网页/素体姿态网格_参考与精灵表.html')
async def main():
    errs=[];r={}
    async with async_playwright() as pw:
        br=await pw.chromium.launch(headless=True,executable_path='/usr/local/bin/chromium',
                                    args=['--no-sandbox','--allow-file-access-from-files'])
        pg=await br.new_page(viewport={'width':1280,'height':820})
        pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
        pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)))
        await pg.goto(P,wait_until='load',timeout=120000);await pg.wait_for_timeout(3600)
        r['imgs']=await pg.evaluate('Object.keys(IMG).length')
        r['ref']=await pg.evaluate('Object.keys(D.ref).length')
        r['assets']=await pg.evaluate('Object.keys(D.assets).length')
        r['boards']=await pg.evaluate('Object.keys(D.boards).length')
        r['badge']=await pg.inner_text('#badge')
        r['cmp']=await pg.inner_text('#cmpInfo')
        r['spec']=await pg.inner_text('#specInfo')
        # 参考板切换
        await pg.select_option('#selRefBoard','G4');await pg.wait_for_timeout(200)
        r['ref_g4']=await pg.evaluate('S.ref')
        r['ref_opts_g4']=await pg.evaluate("document.querySelectorAll('#selRef option').length")
        # 本轮新增：G5 背面
        await pg.select_option('#selRefBoard','G5');await pg.wait_for_timeout(250)
        r['ref_g5']=await pg.evaluate('S.ref')
        r['ref_opts_g5']=await pg.evaluate("document.querySelectorAll('#selRef option').length")
        r['g5_direction']=await pg.evaluate("D.refMeta.find(x=>x.id===S.ref).direction")
        r['dir_matrix']=await pg.inner_text('#dirInfo')
        r['board_label_G5']=await pg.evaluate("[...document.querySelectorAll('#selRefBoard option')].find(o=>o.value==='G5').text")
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_背面G5.png'))
        r['ref_opts']=r['ref_opts_g5']
        # 本轮新增：B 批 8 方向（下拉按批次分组）
        r['optgroups']=await pg.evaluate("document.querySelectorAll('#selRefBoard optgroup').length")
        await pg.select_option('#selRefBoard','H6');await pg.wait_for_timeout(250)
        r['ref_h6']=await pg.evaluate('S.ref')
        r['h6_dir8']=await pg.evaluate("D.refMeta.find(x=>x.id===S.ref).dir8")
        r['h6_batch']=await pg.evaluate("D.refMeta.find(x=>x.id===S.ref).batch")
        await pg.select_option('#selRefBoard','H3');await pg.wait_for_timeout(250)
        r['h3_dir8']=await pg.evaluate("D.refMeta.find(x=>x.id===S.ref).dir8")
        r['dir8_matrix']=await pg.inner_text('#dirInfo')
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_八方向双栏.png'))
        # 8 方向罗盘页
        await pg.click('.tab[data-t="dir8"]');await pg.wait_for_timeout(300)
        r['d8_cells']=await pg.evaluate("document.querySelectorAll('#d8Grid .d8cell').length")
        r['d8_info_N']=await pg.inner_text('#d8Info')
        await pg.click('#d8Grid .d8cell[data-d="S"]');await pg.wait_for_timeout(250)
        r['d8_after_S']=await pg.evaluate('S.dir8')
        r['d8_info_S']=await pg.inner_text('#d8Info')
        await pg.click('#btnD8Next');await pg.wait_for_timeout(150)
        r['d8_idx']=await pg.evaluate('S.d8idx')
        await pg.click('#btnD8Play');await pg.wait_for_timeout(500)
        r['d8_playing']=await pg.evaluate('S.d8playing')
        await pg.click('#btnD8Play')
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_八方向罗盘.png'))
        await pg.click('.tab[data-t="cmp"]');await pg.wait_for_timeout(150)
        # 资产组切换
        await pg.select_option('#selGroup','板C_头部配件');await pg.wait_for_timeout(200)
        r['asset_group']=await pg.evaluate('S.asset')
        # 同步
        await pg.click('#btnSync');await pg.wait_for_timeout(200)
        r['after_sync']=await pg.evaluate('[S.ref,S.asset,S.tab]')
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_双栏对照.png'))
        # 精灵表
        await pg.click('.tab[data-t="sheet"]');await pg.wait_for_timeout(250)
        r['sheet_info']=await pg.inner_text('#sInfo')
        await pg.click('#btnNext');await pg.wait_for_timeout(150)
        r['sheet_next']=await pg.inner_text('#sInfo')
        await pg.click('#btnPoseLoop');await pg.wait_for_timeout(300)
        r['pose_loop']=await pg.inner_text('#sInfo')
        r['seq_len']=await pg.evaluate('S.seq?S.seq.length:0')
        await pg.select_option('#selFilter','板E_毛色变体');await pg.wait_for_timeout(200)
        r['filter']=await pg.inner_text('#sInfo')
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_精灵表.png'))
        # 换装叠加
        await pg.click('.tab[data-t="dress"]');await pg.wait_for_timeout(250)
        r['dress_info']=await pg.inner_text('#dInfo')
        await pg.select_option('#selPose','act_wave');await pg.select_option('#selHair','hair_twin')
        await pg.wait_for_timeout(200)
        r['dress_chips']=await pg.inner_text('#dChips')
        r['dress_canvas']=await pg.evaluate("(()=>{const c=document.querySelector('#cD'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>0)n++;return n})()")
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_换装.png'))
        # 原图总览 + 弹窗
        await pg.click('.tab[data-t="board"]');await pg.wait_for_timeout(250)
        r['board_cells']=await pg.evaluate("document.querySelectorAll('#bGrid .cell').length")
        await pg.click('#bGrid .cell');await pg.wait_for_timeout(200)
        r['big']=await pg.evaluate("getComputedStyle(document.querySelector('#big')).display")
        await pg.click('#big button');await pg.wait_for_timeout(150)
        r['big_closed']=await pg.evaluate("getComputedStyle(document.querySelector('#big')).display")
        # 文档
        await pg.click('.tab[data-t="doc"]');await pg.wait_for_timeout(250)
        r['doc_len']=len(await pg.inner_text('#docReport'))
        r['json_len']=len(await pg.inner_text('#docJson'))
        # play=1
        await pg.goto(P+'?play=1',wait_until='load',timeout=120000);await pg.wait_for_timeout(1100)
        r['play_tab']=await pg.evaluate('S.tab')
        r['fs']=await pg.evaluate("document.body.classList.contains('fullscreen')")
        # 轻量速览页（手机向 1.5MB 单文件）
        L='file://'+os.path.join(ROOT,'参考图_素体网格/03_网页/八方向_速览.html')
        await pg.goto(L,wait_until='load',timeout=120000);await pg.wait_for_timeout(1600)
        r['lite_cells']=await pg.evaluate("document.querySelectorAll('#grid .cell').length")
        r['lite_tbl']=await pg.evaluate("document.querySelectorAll('#tbl tr').length")
        r['lite_info']=await pg.inner_text('#info')
        await pg.click('#grid .cell[data-d="E"]');await pg.wait_for_timeout(200)
        r['lite_after_E']=await pg.evaluate('S.d')
        r['lite_info_E']=await pg.inner_text('#info')
        await pg.screenshot(path=os.path.join(ROOT,'参考图_素体网格/01_解读/网页验证_速览.png'),full_page=True)
        await br.close()
    r['errors']=errs
    print(json.dumps(r,ensure_ascii=False,indent=2))
    json.dump(r,open(os.path.join(ROOT,'参考图_素体网格/04_校验/网页回归报告.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
asyncio.run(main())
