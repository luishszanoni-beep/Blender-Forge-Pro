"""GCB 1.5: auditable reference-to-blueprint data and deterministic technical plates.
Pure Python stdlib; visual Blender verification remains independent and mandatory.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import re
from pathlib import Path

VERSION = '1.0'
ALLOWED_PRIMITIVES = {'box', 'sphere', 'cylinder', 'cone', 'wedge', 'custom_mesh'}
ALLOWED_CONFIDENCE = {'observed', 'inferred', 'unknown'}
SAFE_ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,59}$')
VIEWS = ('front', 'side', 'top', 'three_quarter')


def load_spec(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _vec(value, name, errors, positive=False):
    if not isinstance(value, list) or len(value) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
        errors.append(f'{name}: expected three finite numbers')
        return None
    if positive and any(v <= 0 for v in value):
        errors.append(f'{name}: dimensions must be strictly positive')
    return value


def _id(value, label, errors):
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        errors.append(f'{label}: invalid stable ID')
        return None
    return value


def rotate(v, angles):
    """Apply Blender-compatible XYZ Euler angles, local vector to world."""
    x, y, z = v
    rx, ry, rz = [math.radians(a) for a in angles]
    x, y, z = x, y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, y, z = x * math.cos(ry) + z * math.sin(ry), y, -x * math.sin(ry) + z * math.cos(ry)
    x, y, z = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz), z
    return (x, y, z)


def world_anchor(part, local):
    rot = rotate(local, part['rotation_deg'])
    return tuple(a+b for a, b in zip(part['position'], rot))


def primitive_mesh(part):
    """Return vertices and faces for deterministic wireframe and Blender handoff.
    Geometry is a BLOCKOUT, never a claim of sculpt-level likeness.
    """
    w, d, h = part['dimensions']
    shape = part['primitive']
    if shape == 'box':
        pts = [(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),
               (-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]
        faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    elif shape == 'wedge':
        pts = [(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),
               (-w/2,d/2,h/2),(w/2,d/2,h/2)]
        faces = [(0,3,2,1),(3,4,5,2),(0,1,5,4),(0,4,3),(1,2,5)]
    elif shape in ('cylinder', 'cone'):
        n = 18
        verts1 = [(w/2*math.cos(2*math.pi*i/n), d/2*math.sin(2*math.pi*i/n), -h/2) for i in range(n)]
        if shape == 'cylinder':
            verts2 = [(x,y,h/2) for x,y,_ in verts1]
            pts = verts1+verts2
            faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        else:
            pts = verts1 + [(0,0,h/2)]
            faces = [tuple(reversed(range(n)))]+[(i,(i+1)%n,n) for i in range(n)]
    elif shape == 'sphere':
        n, rings = 18, 9
        pts = []
        for j in range(rings+1):
            z = math.cos(math.pi*j/rings) * h/2
            r = math.sin(math.pi*j/rings)
            for i in range(n):
                t = 2*math.pi*i/n
                pts.append((r*w/2*math.cos(t),r*d/2*math.sin(t),z))
        faces = []
        for j in range(rings):
            for i in range(n):
                a=j*n+i; b=j*n+(i+1)%n
                faces.append((a,b,b+n,a+n))
    else:
        recipe = part.get('geometry_recipe', {})
        pts = [tuple(p) for p in recipe.get('vertices', [])]
        faces = [tuple(f) for f in recipe.get('faces', [])]
    transformed = [world_anchor(part,v) for v in pts]
    return transformed, faces


def validate(spec):
    errors, warnings = [], []
    if not isinstance(spec, dict):
        return {'status':'BLOCKED','errors':['spec must be a JSON object'],'warnings':[]}
    if spec.get('gcb_version') != VERSION:
        errors.append(f'gcb_version must be {VERSION}')
    _id(spec.get('project_id'), 'project_id', errors)
    units = spec.get('units')
    if not isinstance(units, dict) or units.get('mode') not in ('relative','mm'):
        errors.append('units.mode must be relative or mm')
        mode='invalid'
    else:
        mode = units['mode']
    sources = spec.get('source_references', [])
    if not isinstance(sources, list):
        errors.append('source_references must be an array'); sources=[]
    source_ids = set()
    calibrated = set()
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            errors.append(f'source_references[{i}] must be an object');continue
        ident=_id(src.get('id'),f'source_references[{i}].id',errors)
        if ident in source_ids:errors.append(f'duplicate source ID {ident}')
        source_ids.add(ident)
        if src.get('projection') not in ('orthographic','perspective','unknown'):
            errors.append(f'source {ident}: invalid projection')
        if src.get('calibrated') is True:
            calibrated.add(ident)
    if mode == 'mm' and not calibrated and not spec.get('physical_dimensions_declared', False):
        errors.append('mm units require calibrated source or physical_dimensions_declared=true')
    if mode == 'relative':
        warnings.append('relative units: no absolute physical scale is established; do not claim real-world millimeters')
    parts=spec.get('parts')
    if not isinstance(parts, list) or not parts:
        return {'status':'BLOCKED','errors':errors+['parts must be a nonempty array'],'warnings':warnings}
    id_to_part={}
    fingerprints={}
    for i, p in enumerate(parts):
        if not isinstance(p, dict):
            errors.append(f'parts[{i}] is not an object');continue
        id=_id(p.get('id'),f'parts[{i}].id',errors)
        if id in id_to_part:errors.append(f'duplicate part ID: {id}')
        id_to_part[id]=p
        if not isinstance(p.get('label'),str) or not p['label'].strip():errors.append(f'{id}: missing label')
        prim=p.get('primitive')
        if prim not in ALLOWED_PRIMITIVES:errors.append(f'{id}: unsupported primitive {prim!r}')
        for fld in ('dimensions','position','rotation_deg'):
            _vec(p.get(fld),f'{id}.{fld}',errors,positive=(fld=='dimensions'))
        if p.get('confidence') not in ALLOWED_CONFIDENCE:errors.append(f'{id}: confidence must be observed/inferred/unknown')
        refs=p.get('source_ids',[])
        if not isinstance(refs,list) or any(r not in source_ids for r in refs):errors.append(f'{id}: unknown source IDs')
        if p.get('confidence')=='observed' and not refs:errors.append(f'{id}: observed geometry requires source evidence')
        if p.get('confidence')=='unknown':warnings.append(f'{id}: unknown geometry; design assumptions must be reviewed')
        if not isinstance(p.get('stage'),int) or p['stage'] < 1:errors.append(f'{id}: stage must be a positive integer')
        if p.get('separate_mesh') is not True:errors.append(f'{id}: separate_mesh must be true for traceable assembly')
        if 'pivot' in p:_vec(p['pivot'],f'{id}.pivot',errors)
        if prim=='custom_mesh':
            r=p.get('geometry_recipe')
            if not isinstance(r,dict) or not isinstance(r.get('vertices'),list) or len(r['vertices'])<3 or not isinstance(r.get('faces'),list) or not r['faces']:
                errors.append(f'{id}: custom_mesh requires explicit vertices and faces')
            else:
                for k,v in enumerate(r['vertices']):_vec(v,f'{id}.geometry_recipe.vertices[{k}]',errors)
                for f in r['faces']:
                    if not isinstance(f,list) or len(f)<3 or any(not isinstance(v,int) or v<0 or v>=len(r['vertices']) for v in f):
                        errors.append(f'{id}: invalid custom_mesh face index')
        try:
            fp=json.dumps([prim,p['dimensions'],p['position'],p['rotation_deg']],sort_keys=True)
            if fp in fingerprints:errors.append(f'{id}: identical geometry transform to {fingerprints[fp]} (duplicate component)')
            fingerprints[fp]=id
        except (KeyError,TypeError):pass
    for ident,p in id_to_part.items():
        if not isinstance(p,dict):continue
        parent=p.get('parent')
        if parent is not None and parent not in id_to_part:errors.append(f'{ident}: unknown parent {parent}')
        if parent==ident:errors.append(f'{ident}: cannot parent to itself')
        current=parent; chain={ident}
        while current in id_to_part and current not in chain:
            chain.add(current);current=id_to_part[current].get('parent')
        if current in chain:errors.append(f'{ident}: parenting cycle')
    attachments=spec.get('attachments',[])
    if not isinstance(attachments,list):errors.append('attachments must be list');attachments=[]
    anchored_pairs=set()
    for i,a in enumerate(attachments):
        if not isinstance(a,dict):errors.append(f'attachments[{i}] invalid');continue
        child,parent=a.get('child'),a.get('parent')
        if child not in id_to_part or parent not in id_to_part:
            errors.append(f'attachment[{i}] refers to unknown part');continue
        anchored_pairs.add((child,parent))
        u=_vec(a.get('anchor_child'),f'attachment[{i}].anchor_child',errors)
        v=_vec(a.get('anchor_parent'),f'attachment[{i}].anchor_parent',errors)
        tol=a.get('tolerance',0.025)
        if type(tol) not in (int,float) or not math.isfinite(tol) or tol < 0:
            errors.append(f'attachment[{i}]: bad tolerance');continue
        if u and v and all(k in id_to_part[child] and k in id_to_part[parent] for k in ('position','rotation_deg')):
            try:
                c=world_anchor(id_to_part[child],u);p=world_anchor(id_to_part[parent],v)
                distance=math.dist(c,p)
            except (TypeError,ValueError,KeyError,IndexError):
                errors.append(f'attachment[{i}]: cannot evaluate because referenced transforms are invalid')
            else:
                if distance>tol+1e-8:errors.append(f'attachment[{i}]: {child}->{parent} anchor gap {distance:.4f} > tolerance {tol:.4f} (units)')
    for ident,p in id_to_part.items():
        if not isinstance(p,dict):continue
        parent=p.get('parent')
        if parent is not None and (ident,parent) not in anchored_pairs:
            errors.append(f'{ident}: missing attachment anchor to parent {parent}; do not assume a touching joint')
    steps=spec.get('steps')
    if not isinstance(steps,list) or not steps:errors.append('steps must contain ordered construction phases');steps=[]
    seen_steps=set(); seen_parts=set()
    for i,s in enumerate(steps):
        if not isinstance(s,dict):errors.append(f'step {i} invalid');continue
        sid=_id(s.get('id'),f'steps[{i}].id',errors)
        if sid in seen_steps:errors.append(f'duplicate step {sid}')
        seen_steps.add(sid)
        if not isinstance(s.get('title'),str) or not s['title'].strip():errors.append(f'step {sid}: missing title')
        ids=s.get('parts')
        if not isinstance(ids,list) or not ids:errors.append(f'step {sid}: empty parts');continue
        for ident in ids:
            if ident not in id_to_part:errors.append(f'step {sid}: unknown part {ident}')
            if ident in seen_parts:errors.append(f'part {ident} appears in more than one construction step')
            seen_parts.add(ident)
            if ident in id_to_part and id_to_part[ident].get('stage')!=i+1:
                errors.append(f'part {ident}: stage does not match step order ({i+1})')
            if ident in id_to_part:
                parent=id_to_part[ident].get('parent')
                if parent is not None and parent not in seen_parts:
                    errors.append(f'{ident}: parent {parent} not present in or before step {sid}')
    missing=set(id_to_part)-seen_parts
    if missing:errors.append(f'parts absent from steps: {sorted(missing)}')
    if not any(p.get('confidence')=='observed' for p in id_to_part.values() if isinstance(p,dict)):
        warnings.append('No observed part: visual reference similarity cannot be claimed from this blueprint')
    return {'status':'BLOCKED' if errors else 'SPEC_VALIDATED_PENDING_VISUAL_QA','errors':errors,'warnings':warnings,
            'parts_count':len(parts),'step_count':len(steps),'units_mode':mode}


def project(v, view):
    x,y,z=v
    if view=='front':return (x,z,-y)
    if view=='side':return (y,z,-x)
    if view=='top':return (x,y,z)
    # approximate isometric orthographic: forward from (6,-8,6)
    return ((x+y)*0.707106781,(z*0.82+(y-x)*0.405), (x-y+z)*0.45)


def xml_escape(v):return html.escape(str(v),quote=True)


def _draw_panel(parts, visible, highlight, view, x0,y0,width,height, exploded=False):
    margin = 65
    lines = [f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="12" fill="#101b28" stroke="#34465b"/>']
    caption = {'front':'FRONTAL X/Z','side':'LATERAL Y/Z','top':'SUPERIOR X/Y','three_quarter':'PERSPECTIVA 3/4'}[view]
    lines.append(f'<text x="{x0+20}" y="{y0+32}" fill="#dde5ee" font-size="18" font-family="Arial">{caption}</text>')
    all_points = []
    visible_points=[]
    each=[]
    for p in parts:
        verts,faces=primitive_mesh(p)
        pts=[project(v,view) for v in verts]
        if p['id'] in visible:
            visible_points.extend(pts)
            shift=(0,0)
            if exploded:
                idx=next((i for i,q in enumerate(parts) if q['id']==p['id']),0)
                shift=((idx%3-1)*0.55, (idx//3)*0.35)
            each.append((p,pts,faces,shift))
        all_points += pts
    if not all_points:return ''.join(lines)
    extent_x=[q[0] for q in all_points];extent_y=[q[1] for q in all_points]
    cx=(min(extent_x)+max(extent_x))/2;cy=(min(extent_y)+max(extent_y))/2
    rx=max(extent_x)-min(extent_x);ry=max(extent_y)-min(extent_y)
    scale=min((width-2*margin)/max(rx,0.05),(height-2*margin)/max(ry,0.05))
    if exploded:scale*=0.72
    def xy(v,s):return (x0+width/2+(v[0]+s[0]-cx)*scale,y0+height/2-(v[1]+s[1]-cy)*scale)
    # projected guides cross at origin; stable scale across all plates
    ox,oy=xy(project((0,0,0),view),(0,0))
    lines.extend([f'<line x1="{x0+15}" y1="{oy:.1f}" x2="{x0+width-15}" y2="{oy:.1f}" stroke="#2d3f54" stroke-dasharray="5 6"/>',
                  f'<line x1="{ox:.1f}" y1="{y0+45}" x2="{ox:.1f}" y2="{y0+height-15}" stroke="#2d3f54" stroke-dasharray="5 6"/>'])
    if view != 'three_quarter' and not exploded and visible_points:
        vis_x=[q[0] for q in visible_points];vis_y=[q[1] for q in visible_points]
        rx_vis=max(vis_x)-min(vis_x);ry_vis=max(vis_y)-min(vis_y)
        x_left=x0+width/2+(min(vis_x)-cx)*scale
        x_right=x0+width/2+(max(vis_x)-cx)*scale
        y_top=y0+height/2-(max(vis_y)-cy)*scale
        y_bottom=y0+height/2-(min(vis_y)-cy)*scale
        label_y=y0+height-24
        mark_x=x0+width-37
        lines.append(f'<line x1="{x_left:.1f}" y1="{label_y-9}" x2="{x_right:.1f}" y2="{label_y-9}" stroke="#c2edaa" stroke-width="1.5"/>')
        for xp in (x_left,x_right):
            lines.append(f'<line x1="{xp:.1f}" y1="{label_y-16}" x2="{xp:.1f}" y2="{label_y-2}" stroke="#c2edaa" stroke-width="1.5"/>')
        lines.append(f'<rect x="{x0+width/2-44:.1f}" y="{label_y-27:.1f}" width="88" height="19" fill="#101b28"/>')
        lines.append(f'<text x="{x0+width/2:.1f}" y="{label_y-12:.1f}" text-anchor="middle" fill="#c2edaa" font-size="15" font-family="Arial">{rx_vis:.3f}</text>')
        lines.append(f'<line x1="{mark_x}" y1="{y_top:.1f}" x2="{mark_x}" y2="{y_bottom:.1f}" stroke="#c2edaa" stroke-width="1.5"/>')
        for yp in (y_top,y_bottom):
            lines.append(f'<line x1="{mark_x-7}" y1="{yp:.1f}" x2="{mark_x+7}" y2="{yp:.1f}" stroke="#c2edaa" stroke-width="1.5"/>')
        lines.append(f'<text x="{mark_x-6}" y="{(y_top+y_bottom)/2:.1f}" text-anchor="end" fill="#c2edaa" font-size="14" font-family="Arial">{ry_vis:.3f}</text>')
    each.sort(key=lambda item:sum(v[2] for v in item[1])/max(len(item[1]),1))
    for p,pts,faces,shift in each:
        new=p['id'] in highlight
        stroke='#67d9d3' if new else '#8599b0'
        fill='#144653' if new else '#2a3647'
        for f in faces:
            coordinates=' '.join(f'{xy(pts[i],shift)[0]:.1f},{xy(pts[i],shift)[1]:.1f}' for i in f)
            lines.append(f'<polygon points="{coordinates}" fill="{fill}" fill-opacity="0.55" stroke="{stroke}" stroke-width="1.5"/>')
        px,py=xy(project(tuple(p['position']),view),shift)
        lines.append(f'<rect x="{px+5:.1f}" y="{py-16:.1f}" width="{max(40,11*len(p["id"])+12)}" height="22" rx="5" fill="#0b1622" stroke="{stroke}"/>')
        lines.append(f'<text x="{px+11:.1f}" y="{py:.1f}" fill="#ffffff" font-family="Arial" font-size="16">{xml_escape(p["id"])}</text>')
    return ''.join(lines)


def sheet_svg(spec, step=None, exploded=False):
    parts=spec['parts']
    if step is None:visible={p['id'] for p in parts};highlight=set(visible);title='00 — VISAO GERAL'
    else:
        steps=spec['steps']
        visible={part_id for s in steps[:step+1] for part_id in s['parts']}
        highlight=set(steps[step]['parts']);title=f'{step+1:02d} — {steps[step]["title"].upper()}'
    if exploded:title='01 — VISTA EXPLODIDA (POSICOES ESQUEMATICAS)'
    background='<rect width="1600" height="1180" fill="#0b1420"/>'
    h=f'<text x="65" y="75" fill="#eaf2fa" font-family="Arial" font-size="34" font-weight="bold">{xml_escape(title)}</text>'
    desc=f'GCB v1.5 | {spec["project_id"]} | unidades: {spec["units"]["mode"]} | geometria tecnica aproximada; NAO atesta fidelidade artistica'
    h+=f'<text x="65" y="110" fill="#9baec3" font-family="Arial" font-size="18">{xml_escape(desc)}</text>'
    panels=[]
    for (view,x,y) in [('front',65,155),('side',815,155),('top',65,615),('three_quarter',815,615)]:
        panels.append(_draw_panel(parts,visible,highlight,view,x,y,720,425,exploded))
    keys=' | '.join(f'{p["id"]}: {p["primitive"]} [{",".join(str(v) for v in p["dimensions"])}]' for p in parts if p['id'] in highlight)
    footer=f'<text x="65" y="1093" fill="#70dcd4" font-family="Arial" font-size="16">PECAS DESTA ETAPA: {xml_escape(keys[:155])}</text>'
    if len(keys)>155:footer+='<text x="65" y="1120" fill="#9baec3" font-family="Arial" font-size="15">Ver tabela completa de pecas no handoff.md e gcb_spec.json.</text>'
    if exploded:footer+='<text x="65" y="1150" fill="#ffc98b" font-family="Arial" font-size="16">DESLOCAMENTOS VISUAIS NA VISTA EXPLODIDA NAO SAO COORDENADAS DE CONSTRUCAO.</text>'
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180">'+background+h+''.join(panels)+footer+'</svg>'


def fingerprint(spec):
    return hashlib.sha256(json.dumps(spec,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def create_handoff(spec,report,images):
    mode=spec['units']['mode']
    rows=['# GCB | Handoff para o Codex', '',f'Projeto: `{spec["project_id"]}`',f'Especificacao SHA256: `{fingerprint(spec)}`',
          'Status: `SPEC_VALIDATED_PENDING_VISUAL_QA` — nao significa modelo aprovado.',
          '', '## Instrucoes obrigatorias',
          '1. Use `gcb_spec.json` como a UNICA fonte numerica da geometria; imagens sao vistas derivadas. Nunca extraia medidas da imagem raster.',
          '2. Construa cada componente por seu ID, primitive, dimensions, position e rotation_deg. Preserve meshes separadas, pivots e parent.',
          '3. Siga `steps` na ordem. Renderize frente, lado, superior, traseira e 3/4 no Blender, com cameras fixas.',
          '4. Para custom_mesh, use apenas os vertices/faces declarados. Para formas organicas nao especificadas, PARE na hipoteses; nao declare fidelidade perfeita.',
          '5. Compare contra a arte original (nao apenas contra as pranchas). Registre incertezas, divergencias e correcoes locais.',
          '6. Rode o Fidelity Auditor independente antes de G2 ser aprovado; depois prossiga com G3-G8 conforme os gates existentes.',
          f'7. Unidades: `{mode}`. Em relative, NAO converter valores em milimetros sem calibracao explicita.',
          '8. Ignore deslocamentos artificiais do desenho explodido: sao apenas para leitura.',
          '', '## Inventario de pecas', '', '| ID | Primitiva | Dimensoes (X,Y,Z) | Centro (X,Y,Z) | Evidencia |', '|---|---|---|---|---|']
    for p in spec['parts']:
        rows.append(f'| {p["id"]} | {p["primitive"]} | {p["dimensions"]} | {p["position"]} | {p["confidence"]} |')
    rows+=['','## Montagem ordenada']
    for s in spec['steps']:
        rows.append(f'- **{s["id"]} – {s["title"]}**: {", ".join(s["parts"])}. {s.get("notes", "")}')
    rows+=['','## Pranchas tecnicas (SVG; PNG quando disponivel)']
    rows += [f'- `{p}`' for p in images]
    rows+=['','## Limites de aprovacao','- Este manual valida estrutura e coerencia interna, NAO prova semelhanca visual, rigging final ou exportacao Roblox.',
           '- Referencias desconhecidas/inferidas nunca viram observacao comprovada.',
           '- Qualquer erro de encaixe, peça obrigatoria ausente ou alteracao de Geometry Fidelity Lock bloqueia entrega.',
           '', '## Preflight',f'- Erros: {len(report["errors"])}',f'- Avisos: {len(report["warnings"])}']
    rows += [f'  - {w}' for w in report['warnings']]
    return '\n'.join(rows)+'\n'


def write_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
