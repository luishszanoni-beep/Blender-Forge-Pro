#!/usr/bin/env python3
"""Build a traceable, read-only index of the user-provided Blender atlas.
Build-time dependency: PyMuPDF (fitz). The search/router has no PDF dependency.
Never use this source as a substitute for the installed Blender Python API.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ENTRY_RE = re.compile(r'(?m)^(\d{3})[ \t]+([^\n]+)$')
CHAPTER_RE = re.compile(r'(?m)^CAPÍTULO[ \t]+(\d{2})[ \t]*/[ \t]*FERRAMENTAS E FUNCIONALIDADES')
LABEL_RE = re.compile(r'(?<!\w)(O QUE FAZ|APLICAÇÕES|QUANDO|MOTIVO|USO CORRETO|LIFE-HACK)(?=\s)',re.I)
FIELD_MAP = {'O QUE FAZ':'function','APLICAÇÕES':'applications','QUANDO':'when','MOTIVO':'reason','USO CORRETO':'correct_usage','LIFE-HACK':'life_hack'}
CHAPTER_TITLES={
1:'Interface, projeto e navegação',
2:'Seleção, transformação e edição de mesh',
3:'Modificadores: geração e acabamento',
4:'Modificadores: deformação, dados e simulação',
5:'Curvas, superfícies, texto e objetos especiais',
6:'Escultura digital e retopologia',
7:'UV Mapping e pintura de texturas',
8:'Materiais, shaders e texturas procedurais',
9:'Geometry Nodes: construção procedural',
10:'Cabelo, groom e Geometry Nodes para fios',
11:'Rigging, armatures e controle de deformação',
12:'Animação, keyframes, constraints e NLA',
13:'Física clássica e efeitos simulados',
14:'Renderização, luz, câmera e composição de cena',
15:'Grease Pencil, compositor, tracking e vídeo',
16:'Pipeline, automação, validação e exportacao'
}
WORKSPACES = [
 {'name':'Layout','focus':'cena e organização','pages':[78,79]},
 {'name':'Modeling','focus':'geometria e topologia','pages':[78,79]},
 {'name':'Sculpting','focus':'volume orgânico','pages':[78,80]},
 {'name':'UV Editing','focus':'coordenadas de textura','pages':[78,80]},
 {'name':'Texture Paint','focus':'pintura de imagens','pages':[78,81]},
 {'name':'Shading','focus':'materiais e PBR','pages':[78,81]},
 {'name':'Animation','focus':'keyframes e actions','pages':[78,82]},
 {'name':'Rendering','focus':'resultado renderizado','pages':[78,82]},
 {'name':'Compositing','focus':'tratamento de imagem','pages':[78,83]},
 {'name':'Geometry Nodes','focus':'regras procedurais','pages':[78,83]},
 {'name':'Scripting','focus':'Python e validações','pages':[78,84]}
]

def collapsed(text):
    return ' '.join(text.split())

def fields_from_chunk(chunk):
    # Ignore the following chapter header or practical appendix after last tool.
    for boundary in ('\nCAPÍTULO ', '\nAPLICAÇÃO PRÁTICA', '\nFONTE PRIMÁRIA:', '\nMANUAL DE CONSULTA'):
        chunk=chunk.split(boundary,1)[0]
    matches=list(LABEL_RE.finditer(chunk))
    out={k:'' for k in FIELD_MAP.values()}
    for i,m in enumerate(matches):
        name=FIELD_MAP[m.group(1).upper()]
        end=matches[i+1].start() if i+1<len(matches) else len(chunk)
        out[name]=collapsed(chunk[m.end():end])
    return out

def build(pdf:Path):
    import fitz
    doc=fitz.open(pdf)
    if len(doc)!=85:raise ValueError(f'Unexpected PDF page count: {len(doc)} != 85')
    records=[];chapter=0
    for page_num,page in enumerate(doc,1):
        if not 5<=page_num<=68:continue
        body=page.get_text(sort=False)
        boundaries=sorted([(m.start(),'chapter',m) for m in CHAPTER_RE.finditer(body)]+[(m.start(),'tool',m) for m in ENTRY_RE.finditer(body)],key=lambda x:x[0])
        for idx,(start,typ,m) in enumerate(boundaries):
            if typ=='chapter':chapter=int(m.group(1));continue
            tool_id=int(m.group(1))
            if not 1<=tool_id<=407:continue
            if chapter not in CHAPTER_TITLES:raise ValueError(f'Chapter missing at tool {tool_id}')
            end=boundaries[idx+1][0] if idx+1<len(boundaries) else len(body)
            vals=fields_from_chunk(body[m.end():end]);
            records.append({'id':tool_id,'name':collapsed(m.group(2)), 'chapter_id':chapter,
                           'chapter':CHAPTER_TITLES[chapter], 'page':page_num,**vals})
    ids=[x['id'] for x in records]
    if ids!=list(range(1,408)):
        missing=sorted(set(range(1,408))-set(ids))
        raise ValueError(f'Not all 407 sequential tools extracted; missing={missing}, count={len(ids)}')
    if any(not x['name'] or not x['function'] or not x['correct_usage'] for x in records):
        broken=[x['id'] for x in records if not x['name'] or not x['function'] or not x['correct_usage']]
        raise ValueError(f'Missing critical source fields: {broken}')
    digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
    return {'schema_version':'1.0', 'source':{
        'title':'Atlas do Blender: 407 ferramentas, recursos e fluxos de trabalho',
        'pdf_path':'assets/blender-atlas/Atlas_Blender_5_2_2_LTS_407_Ferramentas_e_11_Abas.pdf',
        'sha256':digest,'page_count':85,'source_claimed_blender_version':'5.2.2',
        'edition':'outubro 2026','authority':'user-supplied secondary field guide',
        'scope_note':'Curated list, NOT an exhaustive operator/API registry; validate with current installed Blender and official API.',
        'official_manual':'https://docs.blender.org/manual/en/5.2/',
        'official_api':'https://docs.blender.org/api/5.2/'},
        'chapter_count':len(CHAPTER_TITLES),'tool_count':len(records),
        'chapters':[{'id':i,'title':title} for i,title in CHAPTER_TITLES.items()],
        'workspaces':WORKSPACES,'tools':records}

def main():
    parser=argparse.ArgumentParser(description='Build the Atlas search index from the original PDF')
    parser.add_argument('pdf',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=build(args.pdf)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tools':result['tool_count'],'chapters':result['chapter_count'],'workspaces':len(result['workspaces']),'sha256':result['source']['sha256'],'output':str(args.out)},ensure_ascii=False))

if __name__=='__main__':main()
