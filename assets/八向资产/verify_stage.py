#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os,json,asyncio
from playwright.async_api import async_playwright
ROOT='/data/workspace';P='file://'+os.path.join(ROOT,'八向资产/04_网页/八向导演台.html')
async def main():
    r={};errs=[]
    async with async_playwright() as pw:
        br=await pw.chromium.launch(headless=True,executable_path='/usr/local/bin/chromium',
                                    args=['--no-sandbox','--allow-file-access-from-files'])
        pg=await br.new_page(viewport={'width':1360,'height':900})
        pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
        pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)))
        await pg.goto(P,wait_until='load',timeout=120000);await pg.wait_for_timeout(2000)
        r['imgs']=await pg.evaluate('Object.keys(IMG).length')
        r['badge']=await pg.inner_text('#badge')
        r['dirbtns']=await pg.evaluate("document.querySelectorAll('#dirbtns button').length")
        r['now_N']=await pg.inner_text('#nowInfo')
        r['capC_N']=await pg.inner_text('#capC')
        r['capA_N']=await pg.inner_text('#capA')
        r['gap']=await pg.inner_text('#gapInfo')
        # 切到 NE（未生成）
        await pg.click('#dirbtns button[data-d="NE"]');await pg.wait_for_timeout(200)
        r['capC_NE']=await pg.inner_text('#capC')
        r['now_NE']=await pg.inner_text('#nowInfo')
        await pg.screenshot(path=os.path.join(ROOT,'八向资产/02_预览/网页验证_导演台_NE未生成.png'))
        # 切到 E（候选 + 镜像 W）
        await pg.click('#dirbtns button[data-d="E"]');await pg.wait_for_timeout(200)
        r['capC_E']=await pg.inner_text('#capC')
        r['capA_E']=await pg.inner_text('#capA')
        await pg.click('#dirbtns button[data-d="W"]');await pg.wait_for_timeout(200)
        r['capC_W']=await pg.inner_text('#capC')
        await pg.screenshot(path=os.path.join(ROOT,'八向资产/02_预览/网页验证_导演台_W镜像.png'))
        # 播放
        await pg.click('#play');await pg.wait_for_timeout(650)
        r['playing']=await pg.evaluate('S.playing')
        r['i_after_play']=await pg.evaluate('S.i')
        await pg.click('#play')
        # 挑图
        await pg.click('#dirbtns button[data-d="N"]');await pg.wait_for_timeout(150)
        await pg.click('#markOk');await pg.wait_for_timeout(150)
        r['mark']=await pg.evaluate("JSON.parse(localStorage.getItem('husmeow8_marks'))")
        r['markInfo']=await pg.inner_text('#markInfo')
        # rect 页
        await pg.click('.tab[data-t="rect"]');await pg.wait_for_timeout(300)
        r['rectInfo0']=await pg.inner_text('#rectInfo')
        r['hl']=await pg.evaluate("(()=>{const e=document.querySelector('#rectHL');return [e.style.left,e.style.top,e.style.width,e.style.height]})()")
        await pg.click('#rectNext');await pg.wait_for_timeout(150)
        r['rectInfo1']=await pg.inner_text('#rectInfo')
        await pg.select_option('#rectDir','NE');await pg.wait_for_timeout(150)
        r['rectInfo_NE']=await pg.inner_text('#rectInfo')
        await pg.click('#rectPlay');await pg.wait_for_timeout(650)
        r['rectIdx_after_play']=await pg.evaluate('S.rectIdx')
        await pg.click('#rectPlay')
        await pg.screenshot(path=os.path.join(ROOT,'八向资产/02_预览/网页验证_导演台_rect.png'))
        # 换装页
        await pg.click('.tab[data-t="dress"]');await pg.wait_for_timeout(300)
        r['dInfo']=await pg.inner_text('#dInfo')
        r['dChips']=await pg.inner_text('#dChips')
        await pg.select_option('#dDir','E');await pg.select_option('#dHair','hair_twin');
        await pg.select_option('#dEye','eye_star');await pg.wait_for_timeout(200)
        r['dInfo_E']=await pg.inner_text('#dInfo')
        r['dress_px']=await pg.evaluate("(()=>{const c=document.querySelector('#cD'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>0)n++;return n})()")
        await pg.click('#dBare');await pg.wait_for_timeout(150)
        r['bare_chips']=await pg.inner_text('#dChips')
        await pg.screenshot(path=os.path.join(ROOT,'八向资产/02_预览/网页验证_导演台_换装.png'))
        # 挑图/自检页
        await pg.click('.tab[data-t="review"]');await pg.wait_for_timeout(300)
        r['reviewStat']=await pg.inner_text('#reviewStat')
        r['tbl_rows']=await pg.evaluate("document.querySelectorAll('#tbl tr').length")
        await pg.click('.pvbtn');await pg.wait_for_timeout(200)
        r['big']=await pg.evaluate("getComputedStyle(document.querySelector('#big')).display")
        await pg.click('#big button');await pg.wait_for_timeout(120)
        r['big_closed']=await pg.evaluate("getComputedStyle(document.querySelector('#big')).display")
        await pg.screenshot(path=os.path.join(ROOT,'八向资产/02_预览/网页验证_导演台_挑图.png'))
        # 文档页
        await pg.click('.tab[data-t="docs"]');await pg.wait_for_timeout(250)
        r['doc_len']=len(await pg.inner_text('#docBox'))
        await pg.click('.docbtn[data-k="manifest"]');await pg.wait_for_timeout(150)
        r['doc_manifest_len']=len(await pg.inner_text('#docBox'))
        # play=1
        await pg.goto(P+'?play=1',wait_until='load',timeout=120000);await pg.wait_for_timeout(900)
        r['fs']=await pg.evaluate("document.body.classList.contains('fullscreen')")
        await br.close()
    r['errors']=errs
    print(json.dumps(r,ensure_ascii=False,indent=2))
    json.dump(r,open(os.path.join(ROOT,'八向资产/05_校验/导演台回归.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
asyncio.run(main())
