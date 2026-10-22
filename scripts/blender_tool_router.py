#!/usr/bin/env python3
"""Read-only selector for 407 PDF-atlas tools. Advisory, never executes Blender.

Tool names and descriptions are indexed from the PDF in assets/blender-atlas.
An indexed UI command is not necessarily a bpy operator or supported engine feature.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'references/blender-atlas-index-v18.json'
STAGE_CHAPTERS={
 'G0':{1,16}, 'G1':{1,5,16}, 'G1.5':{1,2,5,16},
 'G2':{2,3,5,9}, 'G3':{3,5,6}, 'G4':{7,8},
 'G5':{2,3,7,16}, 'G6':{11,12}, 'G7':{2,14,16}, 'G8':{7,12,16}}
STAGE_DEFAULT={
 'G1.5':[132,386,387], 'G2':[32,70,68], 'G3':[143,156,162],
 'G4':[189,191,206], 'G5':[31,171,395], 'G6':[401,402,398],
 'G7':[396,397,398], 'G8':[392,393,403]}
# Small curated keyword->tool hints grounded in specific atlas fichas; not an API map.
TOPICS=[
 (('asa','wing','membrana','folha fina','thin membrane'), [72,119,121,396]),
 (('cauda','tail','tentaculo','galho','horn','chifre','curva'), [119,121,93,74]),
 (('hard surface','mecanico','prop','bloco','bloxy','angular','placa','armadura'), [32,68,69,70,87]),
 (('simetria','espelhar','mirror'), [70,17]),
 (('escultura','sculpt','organic','organico','musculo'), [143,147,156,162]),
 (('malha','topologia','retopologia','mesh','non manifold'), [31,49,162,397]),
 (('repetir','repeticao','scatter','instanc','folhagem'), [67,231,235,391]),
 (('uv','texture','textura','bake','atlas'), [165,171,186,395,400]),
 (('material','pbr','shader','roughness','magma','emissiv','lava'), [189,196,202,206,211]),
 (('rig','armature','bone','osso','pivo','pivot','deformacao'), [96,185,398,402]),
 (('animation','animacao','idle','loop','action','nla'), [401,402]),
 (('roblox','studio','fbx'), [392,401,402,403]),
 (('glb','gltf','web'), [393,395]),
 (('validar','qa','inspecao','norma','erro','falha'), [395,396,397,398,405])
]
STOPWORDS={'para','como','com','uma','uns','das','dos','nos','nas','por','pelo','pela','the','and','with','for','from','uma','que','em','no','na','de','do','da','e','ou','a','o','as','os','um','ao','se','os','as','etapa','parte','modelar','criar','construir'}

def normalize(value):
    return unicodedata.normalize('NFKD',str(value).lower()).encode('ascii','ignore').decode('ascii')

def tokens(value):
    return {x for x in re.findall(r'[a-z0-9]+',normalize(value)) if len(x)>2 and x not in STOPWORDS}

def load_index(path=INDEX, verify_pdf=True):
    d=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(d,dict) or d.get('tool_count')!=407 or d.get('chapter_count')!=16:
        raise ValueError('Atlas index metadata invalid')
    if [x.get('id') for x in d.get('tools',[])]!=list(range(1,408)):
        raise ValueError('Atlas index is missing or repeating tool IDs')
    if len(d.get('workspaces',[]))!=11:
        raise ValueError('Atlas index is missing workspaces')
    if verify_pdf:
        # Reference is always fixed to the plugin root, never a user-provided arbitrary path.
        pdf=ROOT/d['source']['pdf_path']
        if pdf.is_file() and hashlib.sha256(pdf.read_bytes()).hexdigest()!=d['source']['sha256']:
            raise ValueError('Source PDF checksum differs from indexed atlas')
    return d

def version_state(atlas_version, installed_version=None):
    if not installed_version:
        return {'status':'UNVERIFIED_RUNTIME','note':'Discover installed Blender version and inspect actual bpy API before executing.'}
    wanted=re.match(r'^(\d+)\.(\d+)',str(atlas_version))
    actual=re.match(r'^(\d+)\.(\d+)',str(installed_version))
    if not wanted or not actual:
        return {'status':'VERSION_UNKNOWN','note':'Cannot compare versions; inspect installed Blender.'}
    if wanted.groups()!=actual.groups():
        return {'status':'VERSION_MISMATCH','note':'Atlas version differs from installed Blender; verify operator availability, API changes and target export.'}
    return {'status':'FAMILY_MATCH_API_UNVERIFIED','note':'Same major/minor only; this does not prove any specific bpy operator, nodes, modifier, or extension is available.'}

def route(index,query,stage='G2',target='general',limit=5,installed_version=None):
    if stage not in STAGE_CHAPTERS: raise ValueError('Unknown gate/stage: '+stage)
    if target not in ('general','roblox','web_glb','render'):raise ValueError('Unknown target: '+target)
    if not isinstance(query,str) or not query.strip():raise ValueError('Query must not be empty')
    if not isinstance(limit,int) or not 1<=limit<=20:raise ValueError('limit must be 1..20')
    q=tokens(query)
    raw=normalize(query)
    topical={}
    for keys,ids in TOPICS:
        if ids==[392,401,402,403] and stage!='G8' and not any(k in raw for k in ('export','fbx','import')):
            continue
        if any(k in raw for k in keys):
            for i in ids:topical[i]=topical.get(i,0)+14
    # Specific target receives a modest bias only when output/target matters.
    if target=='roblox' and ('export' in raw or 'fbx' in raw or stage=='G8'):
        for i in (392,401,402,403):topical[i]=topical.get(i,0)+15
    if target=='web_glb' and ('export' in raw or 'glb' in raw or stage=='G8'):
        for i in (393,395):topical[i]=topical.get(i,0)+15
    ranked=[]
    for item in index['tools']:
        fields=[('name',5),('function',2),('applications',2),('when',2),('reason',1),('correct_usage',1),('life_hack',0.5)]
        score=0.0;matched=[]
        for key,weight in fields:
            overlap=q & tokens(item[key]);score+=min(3,len(overlap))*weight
            if overlap:matched.append(key)
        if item['id'] in topical:score+=topical[item['id']];matched.append('curated_pdf_topic')
        if score>0:
            score+=3 if item['chapter_id'] in STAGE_CHAPTERS[stage] else -5
        if score>0:ranked.append((score,item,matched))
    ranked.sort(key=lambda a:(-a[0],a[1]['id']))
    if not ranked:
        ranked=[(0,index['tools'][i-1],['generic_stage_fallback']) for i in STAGE_DEFAULT.get(stage,[387,388,389])]
    results=[]
    for score,src,matched in ranked[:limit]:
        results.append({
            'tool_id':src['id'],'tool_name':src['name'],'atlas_page':src['page'],
            'atlas_chapter':src['chapter'],'score':round(score,1),
            'selection_basis':matched,
            'when':src['when'],'why':src['reason'],
            'recommended_use':src['correct_usage'],'life_hack':src['life_hack'],
            'bpy_operator_verified':False,
            'verification':'Confirm in installed Blender, bpy API/actual context and export destination before execution.'
        })
    return {'query':query,'stage':stage,'target':target,'atlas_pdf_sha256':index['source']['sha256'],
            'atlas_claimed_version':index['source']['source_claimed_blender_version'],
            'runtime':version_state(index['source']['source_claimed_blender_version'],installed_version),
            'tools':results,'status':'RECOMMENDATIONS_ONLY_NOT_EXECUTED',
            'source_role':'secondary user-supplied atlas; official Blender API/runtime and user-approved geometry take precedence'}

def plan_gcb(index,spec,installed_version=None,limit=3):
    if not isinstance(spec,dict) or not spec.get('project_id') or not isinstance(spec.get('steps'),list):
        raise ValueError('Invalid GCB spec for tool plan')
    target=spec.get('target','general')
    if target not in ('general','roblox','web_glb','render'):
        raise ValueError('Unsupported GCB target')
    steps=[]
    parts={x['id']:x for x in spec.get('parts',[]) if isinstance(x,dict) and 'id' in x}
    for st in spec['steps']:
        part_labels=' '.join(f"{parts[i].get('label','')} {parts[i].get('primitive','')}" for i in st.get('parts',[]) if i in parts)
        query=' '.join([st.get('title',''),st.get('notes',''),part_labels,spec.get('visual_style','')]).strip()
        if not query: query='modelagem de primitivas e encaixes'
        recommended=route(index,query,'G2',target,limit,installed_version)
        steps.append({'step_id':st['id'],'title':st.get('title',''),
                     'referenced_parts':st.get('parts',[]),'recommendations':recommended['tools']})
    return {'schema_version':'1.0','project_id':spec['project_id'],
            'origin':'GCB G1.5 ordered assembly steps','source_atlas':index['source'],
            'runtime':version_state(index['source']['source_claimed_blender_version'],installed_version),
            'steps':steps,'status':'ADVISORY_UNVERIFIED_API_NOT_EXECUTED',
            'mandatory_next_step':'Before bpy execution inspect actual Blender version/API, pick simplest operation meeting geometry, and verify renders + export.'}

def report_markdown(plan):
    lines=['# Seleção de ferramentas (Blender Atlas / aconselhamento)',
           '',f"Fonte: atlas fornecido pelo usuário, versão declarada {plan['source_atlas']['source_claimed_blender_version']}; ",
           f"API/runtime: {plan['runtime']['status']}.",
           '**Atenção:** ferramentas na interface não são comandos `bpy` prontos. Confira versão e assinatura no Blender instalado. Nenhuma operação foi executada.', '']
    for st in plan['steps']:
        lines.append(f"## {st['step_id']} — {st['title']}")
        for t in st['recommendations']:
            lines.append(f"- Atlas #{t['tool_id']:03d}, p. {t['atlas_page']}: **{t['tool_name']}** — {t['recommended_use']} ({t['why']})")
        lines.append('')
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser(description='Search Blender tool atlas without loading full PDF into model context')
    p.add_argument('--index',type=Path,default=INDEX)
    sub=p.add_subparsers(dest='command',required=True)
    search=sub.add_parser('search');search.add_argument('--query',required=True)
    search.add_argument('--stage',choices=STAGE_CHAPTERS,default='G2')
    search.add_argument('--target',choices=['general','roblox','web_glb','render'],default='general')
    search.add_argument('--limit',type=int,default=5)
    search.add_argument('--installed-version',default=None)
    search.add_argument('--out',type=Path)
    cmd=sub.add_parser('gcb-plan');cmd.add_argument('--spec',type=Path,required=True)
    cmd.add_argument('--installed-version',default=None);cmd.add_argument('--limit',type=int,default=3)
    cmd.add_argument('--out',type=Path,required=True)
    verify=sub.add_parser('verify-index');verify.add_argument('--pdf',type=Path,default=None)
    args=p.parse_args()
    try:
        index=load_index(args.index)
        if args.command=='verify-index':
            path=args.pdf or ROOT/index['source']['pdf_path']
            if not path.is_file():raise ValueError('Original PDF missing')
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            if actual!=index['source']['sha256']:raise ValueError('Source checksum mismatch')
            result={'status':'VALID_INDEX_PDF_MATCH','tools':407,'chapters':16,'workspaces':11,'sha256':actual}
        elif args.command=='search':
            result=route(index,args.query,args.stage,args.target,args.limit,args.installed_version)
        else:
            spec=json.loads(args.spec.read_text(encoding='utf-8'))
            result=plan_gcb(index,spec,args.installed_version,args.limit)
        payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if getattr(args,'out',None):
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(payload,encoding='utf-8')
            if args.command=='gcb-plan':
                args.out.with_suffix('.md').write_text(report_markdown(result),encoding='utf-8')
        print(payload)
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
