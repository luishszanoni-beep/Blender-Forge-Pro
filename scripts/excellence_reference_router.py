#!/usr/bin/env python3
"""3DERL v1.9: select licensed 3D quality exemplars without confusing them for user reference evidence.

    python scripts/excellence_reference_router.py validate
    python scripts/excellence_reference_router.py select --goal 'dragao bloxy com rig' --style bloxy --focus anatomy --focus rigging --out planning/gcb/excellence
    python scripts/excellence_reference_router.py select --goal 'mesas 3d' --style realistic --focus furniture --out planning/gcb/excellence

Selection, listing, metadata validation and HTML creation are offline/std-lib only.
Preview images are remote by default; caching requires an explicit --allow-network switch.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
import urllib.request
import urllib.parse
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CATALOG=ROOT/'references'/'3d-excellence-library-v19.json'
ALLOWED_PAGE_HOSTS={'kenney.nl','www.kenney.nl','quaternius.com','www.quaternius.com','polyhaven.com','www.polyhaven.com'}
ALLOWED_IMAGE_HOSTS=ALLOWED_PAGE_HOSTS|{'cdn.polyhaven.com'}
STAGES={'G0','G1','G1.5','G2','G3','G4','G5','G6','G7','G8'}
ALIASES={
 'dragao':'dragon','dragoes':'dragon','criatura':'creature','criaturas':'creature','monstro':'monster',
 'planta':'plant','plantas':'plant','folha':'foliage','folhas':'foliage','arvore':'tree','arvores':'tree',
 'personagem':'character','personagens':'character','anatomia':'anatomy','quadrupede':'quadruped',
 'animacao':'animation','animacoes':'animation','animado':'animation','rigging':'rig',
 'rocha':'rock','pedra':'rock','movel':'furniture','moveis':'furniture','mesa':'table','cadeira':'furniture',
 'estrutura':'assembly','encaixe':'assembly','modularidade':'modular','pecas':'modular','primitiva':'geometry',
 'estilizado':'stylized','estilizada':'stylized','realista':'realistic','modelo':'model','modelagem':'modeling',
 'bloquinho':'bloxy','blocos':'bloxy','roblox':'roblox','superficie':'surface','materiais':'material',
 'textura':'pbr','texturas':'pbr','maquina':'mechanical','topologia':'topology', 'asas':'wing','asa':'wing',
 'cauda':'tail','mandibula':'jaw','corpo':'anatomy','membros':'anatomy','juntas':'joint','pivo':'joint',
 'cena':'environment','cenario':'environment','cenario3d':'environment',
}

def terms(value):
    raw=value if isinstance(value,str) else ' '.join(map(str,value))
    raw=unicodedata.normalize('NFKD',raw.lower())
    raw=''.join(c for c in raw if not unicodedata.combining(c))
    return {ALIASES.get(t,t) for t in re.findall(r'[a-z0-9_]+',raw)}

def load_catalog(path=DEFAULT_CATALOG):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def host_is_allowed(url,whitelist):
    try:
        p=urllib.parse.urlsplit(url)
        return p.scheme=='https' and p.hostname in whitelist and p.username is None and p.password is None and not p.fragment
    except (ValueError,TypeError):
        return False

def validate_catalog(cat):
    errors=[]
    if not isinstance(cat,dict) or not isinstance(cat.get('entries'),list):return ['catalog entries missing']
    entries=cat['entries']
    if cat.get('count')!=len(entries):errors.append('count mismatch')
    if len(entries)<12 or len(entries)>24:errors.append('expected curated set of 12-24 exemplars')
    seen=set()
    for i,e in enumerate(entries):
        p=f'entries[{i}]'
        if not isinstance(e,dict):errors.append(p+' not object');continue
        k=e.get('id')
        if not isinstance(k,str) or not re.fullmatch(r'[a-z][a-z0-9_]{3,80}',k):errors.append(p+': invalid id')
        if k in seen:errors.append(p+': duplicate id '+str(k))
        seen.add(k)
        for f in ['title','provider','creator','asset_type','preview_url','source_url','license_url','license']:
            if not isinstance(e.get(f),str) or not e[f].strip(): errors.append(f'{p}: missing {f}')
        if e.get('license')!='CC0-1.0':errors.append(p+': license must be CC0')
        if e.get('asset_type') not in {'pack','model'}:errors.append(p+': invalid asset_type')
        if not host_is_allowed(e.get('source_url'),ALLOWED_PAGE_HOSTS):errors.append(p+': bad source host')
        if not host_is_allowed(e.get('preview_url'),ALLOWED_IMAGE_HOSTS):errors.append(p+': bad preview host')
        for key in ['styles','topics','gates','learning_points','cannot_prove_from_preview']:
            if not isinstance(e.get(key),list) or not e[key] or not all(isinstance(v,str) and v.strip() for v in e[key]):errors.append(f'{p}: invalid {key}')
        if any(g not in STAGES for g in e.get('gates',[])):errors.append(p+': invalid gate')
        if e.get('preview_status')!='REMOTE_URL_NOT_BUNDLED':errors.append(p+': preview status must disclose remote link')
        if e.get('source_evidence')!='official_asset_page_and_public_license':errors.append(p+': missing source evidence note')
    return errors

def relevance(e,goal,style,focus,stage,target):
    t=terms(goal);f=terms(focus);styles=terms(e['styles']);topics=terms(e['topics']);name=terms(e['title'])
    match=t & (topics|styles|name)
    # Generic terms alone do not justify replacing user artwork with exemplary inspiration.
    score=sum(2.25 if x in topics else 1.4 for x in match)
    if t and len(match)==0:score-=6
    if f:score+=sum(5 if x in topics else (2 if x in styles else 0) for x in f)
    if style and style!='any':
        if style in e['styles']: score+=8
        elif style=='bloxy' and 'stylized' in e['styles']:score+=2
        else:score-=6
    if stage and stage in e['gates']:score+=2
    if target=='roblox':
        if 'game_ready' in topics or 'bloxy' in styles:score+=2
        if 'realistic' in styles and style in {'bloxy','stylized'}:score-=2
    return round(score,3),sorted(match)

def select(cat,goal='',style='any',focus=(),stage=None,target=None,limit=3):
    if validate_catalog(cat):raise ValueError('invalid catalog')
    if not 1<=limit<=3:raise ValueError('limit must be 1..3: protect context and prevent unwanted style contamination')
    if style not in {'any','bloxy','stylized','realistic'}:raise ValueError('unknown style')
    if stage not in STAGES|{None}:raise ValueError('unknown stage')
    weighted=[]
    for e in cat['entries']:
        score, matched=relevance(e,goal,style,focus,stage,target)
        if score>=4 and (matched or focus or (style!='any' and style in e['styles'])):
            weighted.append((score,e['id'],e,matched))
    weighted.sort(key=lambda x:(-x[0],x[1]))
    selected=[]; providers=Counter()
    for score,_,e,matched in weighted:
        if providers[e['provider']]>=2:continue
        selected.append({**e,'score':score,'matched_topics':matched,'role':'quality_exemplar_not_user_source','visual_proof':'NOT_VERIFIED_BEYOND_PREVIEW'})
        providers[e['provider']]+=1
        if len(selected)>=limit:break
    return {'status':'ADVISORY_EXEMPLARS_NOT_SOURCE_EVIDENCE','library_version':cat['library_version'],
            'goal':goal,'style':style,'focus':list(focus),'stage':stage,'target':target,
            'selected_count':len(selected),'selected':selected,
            'user_source_precedence':True,'automatically_fetched_previews':False,
            'notes':['Do not infer object topology, joints or measurements from provider thumbnails.',
                     'Reference images provided by the user override artistic styling from this library.',
                     'Only inspect remote previews when accessible and justified; never report them as directly checked if not opened.',
                     'No model, material, UV, animation, or export QA is established by selection.']}

def to_markdown(plan):
    lines=['# 3DERL | Biblioteca 3D de excelência | Referências comparativas (v1.9)','',
      f"**Consulta:** {plan.get('goal','')} | estilo={plan.get('style','any')} | etapa={plan.get('stage') or 'n/a'}",
      '', '**Importante:** este material é consultivo. A arte original do usuário e `gcb_spec.json` definem, respectivamente, fidelidade visual e medidas de montagem. Nenhum render aqui comprova topologia ou rig.','']
    if not plan['selected']:lines+=['Nenhuma referência suficientemente pertinente. Prosseguir com a referência do usuário sem forçar exemplos.','']
    for x in plan['selected']:
        lines += [f"## {x['title']} — {x['provider']} ({x['asset_type']})",
          f"[Página oficial]({x['source_url']}) | [Prévia visual]({x['preview_url']}) | Licença: {x['license']}",
          '', '**O que observar:**']
        lines += [f'- {v}' for v in x['learning_points']]
        lines += ['','**O que não concluir apenas pela imagem:**']
        lines += [f'- {v}' for v in x['cannot_prove_from_preview']]
        lines += ['',f"*ID de referência: `{x['id']}`; fonte: `{x['creator']}`. Visual remoto não armazenado no plugin.*",'']
    return '\n'.join(lines)

def to_html(plan):
    cards=[]
    for x in plan['selected']:
        t=html.escape(x['title']);prov=html.escape(x['provider']);url=html.escape(x['source_url'],quote=True);img=html.escape(x['preview_url'],quote=True)
        lessons=''.join('<li>'+html.escape(s)+'</li>' for s in x['learning_points'][:3])
        cards.append(f'<article><a href="{url}" target="_blank" rel="noopener noreferrer"><img src="{img}" alt="Prévia remota: {t}, {prov}" loading="lazy"></a><div class="pad"><small>CC0 · {prov} · Prévia remota</small><h2>{t}</h2><ul>{lessons}</ul><a href="{url}">Ver fonte oficial ↗</a></div></article>')
    c=''.join(cards) or '<p>Nenhuma referência adequada à consulta atual. Não inventar exemplos.</p>'
    return '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>3DERL — Exemplares 3D</title><style>body{font:15px system-ui,sans-serif;background:#111820;color:#e9eef3;margin:0;padding:32px;max-width:1220px}h1{font-size:29px;letter-spacing:-.03em}.sub{color:#a5b8c9}.notice{padding:14px 17px;border:1px solid #4c5969;border-radius:10px;margin:20px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}article{background:#1c2934;border:1px solid #304150;border-radius:14px;overflow:hidden}article img{width:100%;height:235px;object-fit:contain;background:#24323c}article .pad{padding:15px}small{color:#a9b9c6}h2{font-size:19px;margin:6px 0}a{color:#9cd8ff}li{margin:6px 0}</style><h1>Biblioteca de Excelência 3D</h1><p class="sub">' + html.escape(plan.get('goal','')) + '</p><div class="notice"><b>Exemplos auxiliares, não a arte-base do projeto.</b> As imagens são servidas pelas fontes oficiais via Internet e não provam rigging, UV ou topologia. Se estiver offline, use os links e descrições em Markdown.</div><section class="grid">'+c+'</section></html>'

def _download_no_redirect(url,size_limit=3*1024*1024):
    # Reject off-domain redirects, large downloads and non-images. This is an explicit optional user action.
    class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if not host_is_allowed(newurl,ALLOWED_IMAGE_HOSTS):raise ValueError('Redirect to untrusted preview host')
            return super().redirect_request(req,fp,code,msg,headers,newurl)
    req=urllib.request.Request(url,headers={'User-Agent':'BlenderForgeProReferenceCache/1.0'})
    opener=urllib.request.build_opener(RestrictedRedirect())
    with opener.open(req,timeout=20) as resp:
        if not host_is_allowed(resp.geturl(),ALLOWED_IMAGE_HOSTS):raise ValueError('Untrusted response URL')
        kind=resp.headers.get('Content-Type','').split(';')[0].strip().lower()
        if kind not in {'image/png','image/jpeg','image/webp'}:raise ValueError('Image content type required')
        blob=resp.read(size_limit+1)
        if len(blob)>size_limit:raise ValueError('Image too large')
        magic=(blob.startswith(b'\x89PNG\r\n\x1a\n') or blob.startswith(b'\xff\xd8\xff') or blob.startswith(b'RIFF') and blob[8:12]==b'WEBP')
        if not magic:raise ValueError('Invalid image bytes')
        ext={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp'}[kind]
        return blob,ext

def cache(plan,out,allow_network):
    if not allow_network:raise ValueError('Network download requires explicit --allow-network')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for e in plan['selected']:
        if not host_is_allowed(e['preview_url'],ALLOWED_IMAGE_HOSTS):rows.append({'id':e['id'],'status':'BLOCKED_BAD_HOST'});continue
        try:
            b,ext=_download_no_redirect(e['preview_url'])
            filename=e['id']+ext; (out/filename).write_bytes(b)
            rows.append({'id':e['id'],'status':'CACHED','file':filename,'sha256':hashlib.sha256(b).hexdigest(),'size_bytes':len(b)})
        except (OSError,ValueError) as err:
            rows.append({'id':e['id'],'status':'UNAVAILABLE','reason':str(err)[:250]})
    manifest={'status':'CACHE_PARTIAL_OR_COMPLETE_NO_VISUAL_PROOF','items':rows}
    (out/'preview_cache_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    return manifest

def main(argv=None):
    p=argparse.ArgumentParser(description='3DERL v1.9 curated CC0 reference router')
    p.add_argument('command',choices=['validate','select','cache'])
    p.add_argument('--catalog',type=Path,default=DEFAULT_CATALOG)
    p.add_argument('--goal',default='')
    p.add_argument('--style',choices=['any','bloxy','stylized','realistic'],default='any')
    p.add_argument('--focus',action='append',default=[])
    p.add_argument('--stage',choices=sorted(STAGES),default=None)
    p.add_argument('--target',choices=['roblox','render','web_glb','general'],default=None)
    p.add_argument('--max',type=int,default=3)
    p.add_argument('--out',type=Path,default=None)
    p.add_argument('--plan',type=Path,default=None)
    p.add_argument('--allow-network',action='store_true')
    a=p.parse_args(argv)
    try:
        cat=load_catalog(a.catalog); errors=validate_catalog(cat)
        if errors:print(json.dumps({'status':'INVALID','errors':errors},ensure_ascii=False,indent=2));return 2
        if a.command=='validate':
            print(json.dumps({'status':'VALID_METADATA_ONLY','entries':len(cat['entries']),'providers':list(sorted({e['provider'] for e in cat['entries']})),'images_downloaded':False},ensure_ascii=False,indent=2));return 0
        if a.command=='cache':
            if not a.plan or not a.out:raise ValueError('cache needs --plan and --out')
            plan=json.loads(a.plan.read_text(encoding='utf-8'))
            if plan.get('status')!='ADVISORY_EXEMPLARS_NOT_SOURCE_EVIDENCE' or len(plan.get('selected',[]))>3:raise ValueError('bad selection plan')
            cache_result=cache(plan,a.out,a.allow_network)
            print(json.dumps(cache_result,ensure_ascii=False,indent=2));return 0 if all(x['status']=='CACHED' for x in cache_result['items']) else 3
        if a.out is None:raise ValueError('select requires --out')
        plan=select(cat,a.goal,a.style,a.focus,a.stage,a.target,a.max)
        a.out.mkdir(parents=True,exist_ok=True)
        (a.out/'selected_references.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
        (a.out/'selected_references.md').write_text(to_markdown(plan),encoding='utf-8')
        (a.out/'reference_gallery.html').write_text(to_html(plan),encoding='utf-8')
        print(json.dumps({'status':plan['status'],'count':plan['selected_count'],'ids':[e['id'] for e in plan['selected']],'html_gallery_images':'REMOTE_NOT_DOWNLOADED'},ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as err:
        print(json.dumps({'status':'FAILED','error':str(err)},ensure_ascii=False));return 2

if __name__=='__main__':sys.exit(main())
