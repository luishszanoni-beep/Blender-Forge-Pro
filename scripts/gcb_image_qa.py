#!/usr/bin/env python3
"""G1-R: offline metadata and handoff validation for generated modeling references.

This tool DOES NOT inspect image anatomy, image content or 3D fidelity.
A recorded review is a user/agent declaration, not a verifiable visual test.

Usage:
  python scripts/gcb_image_qa.py validate QA.json --root PROJECT --out QA_REPORT.json
  python scripts/gcb_image_qa.py handoff QA.json --root PROJECT --out CODEX_HANDOFF.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SCHEMA_VERSION = '1.0'
ID_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,59}$')
VIEWS = {'front', 'back', 'left', 'right', 'side', 'top', 'bottom', 'three_quarter', 'closeup'}
ORIGINS = {'user_original', 'generated_design', 'generated_inferred'}
CONFIDENCES = {'observed', 'inferred', 'unknown'}
PRIMITIVES = {'box', 'sphere', 'cylinder', 'cone', 'wedge', 'custom_mesh', 'curve', 'compound'}
CATEGORIES = {'identity', 'anatomy', 'connections', 'articulation', 'views', 'geometry', 'surface', 'handoff'}
SUBJECTS = {'creature', 'character', 'plant', 'vehicle', 'mechanical', 'object'}
CRITICAL_CATEGORIES = {'identity', 'connections', 'views', 'geometry', 'handoff'}
MAGIC = {'.png': bytes.fromhex('89504e470d0a1a0a'), '.jpg': bytes.fromhex('ffd8'), '.jpeg': bytes.fromhex('ffd8'), '.webp': b'RIFF'}


def _id(value):
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _array(value):
    return value if isinstance(value, list) else []


def _image_valid(path):
    suffix = path.suffix.lower()
    if suffix not in MAGIC:
        return False
    with path.open('rb') as stream:
        first = stream.read(24)
    if len(first) < 12 or not first.startswith(MAGIC[suffix]):
        return False
    if suffix == '.png':
        return len(first) >= 24 and first[12:16] == b'IHDR' and int.from_bytes(first[16:20], 'big') > 0 and int.from_bytes(first[20:24], 'big') > 0
    if suffix == '.webp':
        return len(first) >= 12 and first[8:12] == b'WEBP'
    return len(first) >= 16


def _relative_real_path(root, rel):
    if not _nonempty(rel):
        raise ValueError('empty relative path')
    p = Path(rel)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('unsafe path')
    resolved_root = root.resolve()
    resolved_file = (resolved_root / p).resolve()
    if not resolved_file.is_relative_to(resolved_root):
        raise ValueError('path escapes authorized project root')
    return resolved_file


def evaluate(data: dict, root: Path, gcb_spec: dict | None = None):
    errors, warnings, files = [], [], []
    if not isinstance(data, dict):
        return {'contract_version': SCHEMA_VERSION, 'status': 'BLOCKED_INVALID_CONTRACT', 'ready_for_gcb': False,
                'errors': ['QA must be a JSON object'], 'warnings': [], 'image_files': []}
    if data.get('schema_version') != SCHEMA_VERSION:
        errors.append('schema_version must be 1.0')
    if not _id(data.get('project_id')):
        errors.append('project_id must be a stable nonempty ID')
    subject = data.get('subject_type')
    if subject not in SUBJECTS:
        errors.append('unsupported subject_type')
    if data.get('purpose') != 'image_references_for_3d':
        errors.append('purpose must be image_references_for_3d')

    images = _array(data.get('images'))
    if not images:
        errors.append('at least one real image is required; do not pass a plan as generated art')
    image_ids = set()
    for i, im in enumerate(images):
        prefix = f'images[{i}]'
        if not isinstance(im, dict):
            errors.append(f'{prefix}: expected object'); continue
        iid = im.get('id')
        if not _id(iid) or iid in image_ids:
            errors.append(f'{prefix}: missing, duplicate or invalid image ID')
        else:
            image_ids.add(iid)
        if im.get('view') not in VIEWS:
            errors.append(f'{prefix}: invalid view')
        if im.get('projection') not in {'perspective', 'orthographic', 'unknown'}:
            errors.append(f'{prefix}: missing projection')
        if im.get('origin') not in ORIGINS:
            errors.append(f'{prefix}: missing/invalid origin')
        if im.get('confidence') not in CONFIDENCES:
            errors.append(f'{prefix}: invalid confidence')
        if im.get('origin') == 'generated_inferred' and im.get('confidence') == 'observed':
            errors.append(f'{prefix}: generated inferred view cannot be measured/observed source')
        if im.get('origin') != 'user_original' and im.get('calibrated') is True:
            errors.append(f'{prefix}: free-form generated art cannot be claimed as calibrated physical drawing')
        if im.get('origin') == 'generated_inferred' and im.get('projection') == 'orthographic':
            warnings.append(f'{prefix}: inferred orthographic-looking view does not prove physically calibrated camera')
        try:
            p = _relative_real_path(root, im.get('path'))
            if not p.is_file() or not _image_valid(p):
                raise ValueError('image file missing, malformed or unsupported')
            blob = p.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            if im.get('sha256') and im['sha256'] != digest:
                errors.append(f'{prefix}: image hash differs from declared protected source')
            files.append({'id': iid, 'path': im.get('path'), 'size_bytes': len(blob), 'sha256': digest})
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f'{prefix}: {exc}')

    for i, im in enumerate(images):
        if not isinstance(im, dict): continue
        iid=im.get('id')
        based_on=_array(im.get('based_on_ids'))
        if im.get('origin') == 'generated_inferred' and not based_on:
            errors.append(f'images[{i}]: inferred generated view must declare its source image ID(s)')
        for source_id in based_on:
            if source_id not in image_ids or source_id == iid:
                errors.append(f'images[{i}]: invalid provenance source image {source_id}')

    parts = _array(data.get('parts'))
    if not parts:
        errors.append('parts inventory missing')
    part_ids = set()
    gcb_ids = {p.get('id') for p in _array(gcb_spec.get('parts')) if isinstance(p, dict)} if isinstance(gcb_spec, dict) else None
    for i, part in enumerate(parts):
        pre = f'parts[{i}]'
        if not isinstance(part, dict): errors.append(f'{pre}: expected object'); continue
        pid = part.get('id')
        if not _id(pid) or pid in part_ids:
            errors.append(f'{pre}: missing/duplicate/invalid part ID')
        else:
            part_ids.add(pid)
        if not _nonempty(part.get('label')) or not _nonempty(part.get('build_instruction')) or not _nonempty(part.get('structural_note')):
            errors.append(f'{pre}: label/build_instruction/structural_note required for Codex')
        if part.get('primitive') not in PRIMITIVES:
            errors.append(f'{pre}: primitive or custom_mesh recipe type required')
        if part.get('confidence') not in CONFIDENCES:
            errors.append(f'{pre}: confidence must be observed, inferred or unknown')
        if part.get('moving') is True and part.get('separate_mesh') is not True:
            errors.append(f'{pre}: moving part must be a separate mesh')
        pivot = part.get('pivot')
        if pivot is not None and (not isinstance(pivot, list) or len(pivot) != 3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in pivot)):
            errors.append(f'{pre}: pivot must be three finite values or null')
        if part.get('moving') is True and pivot is None:
            warnings.append(f'{pre}: moving part has no pivot hypothesis yet')
        if not _array(part.get('image_ids')):
            errors.append(f'{pre}: image evidence ID(s) required')
        gcb_id = part.get('gcb_part_id')
        if gcb_id is not None and gcb_ids is not None and gcb_id not in gcb_ids:
            errors.append(f'{pre}: gcb_part_id does not exist in numeric GCB')
    for i, part in enumerate(parts):
        if not isinstance(part, dict): continue
        for iid in _array(part.get('image_ids')):
            if iid not in image_ids: errors.append(f'parts[{i}]: unknown image reference {iid}')
        for connected in _array(part.get('connection_ids')):
            if connected not in part_ids or connected == part.get('id'):
                errors.append(f'parts[{i}]: unknown/self connection {connected}')

    steps = _array(data.get('modeling_steps'))
    if not steps:
        errors.append('modeling_steps missing: must explain execution to Codex')
    covered, step_ids = set(), set()
    for i, step in enumerate(steps):
        pre = f'modeling_steps[{i}]'
        if not isinstance(step, dict): errors.append(f'{pre}: expected object'); continue
        sid=step.get('id')
        if not _id(sid) or sid in step_ids: errors.append(f'{pre}: missing/duplicate/invalid step ID')
        else: step_ids.add(sid)
        if not _nonempty(step.get('instruction')) or not _nonempty(step.get('acceptance')):
            errors.append(f'{pre}: step requires instruction and acceptance conditions')
        if not _array(step.get('part_ids')):
            errors.append(f'{pre}: no part_ids')
        for part_id in _array(step.get('part_ids')):
            if part_id not in part_ids: errors.append(f'{pre}: references undefined part {part_id}')
            else: covered.add(part_id)
    for part_id in sorted(part_ids - covered): errors.append(f'unplanned part {part_id} has no modeling step')

    checks = _array(data.get('checks'))
    categories = {}
    for i, check in enumerate(checks):
        pre=f'checks[{i}]'
        if not isinstance(check, dict): errors.append(f'{pre}: expected object'); continue
        cat=check.get('category')
        if cat not in CATEGORIES or cat in categories:
            errors.append(f'{pre}: invalid or repeated quality category')
        else:
            categories[cat]=check
        if check.get('status') not in {'PASS', 'FAIL', 'UNKNOWN', 'NA'}:
            errors.append(f'{pre}: invalid assessment status')
        if not _nonempty(check.get('note')):
            errors.append(f'{pre}: a specific reviewer note is required')
        if check.get('status') != 'NA' and not _array(check.get('image_ids')):
            errors.append(f'{pre}: visual evidence image IDs required')
        for image_id in _array(check.get('image_ids')):
            if image_id not in image_ids: errors.append(f'{pre}: unknown image {image_id}')
        for part_id in _array(check.get('part_ids')):
            if part_id not in part_ids: errors.append(f'{pre}: unknown part {part_id}')
    required_categories = {'identity', 'connections', 'views', 'geometry', 'surface', 'handoff'}
    if subject in {'creature','character','plant'}: required_categories.add('anatomy')
    if subject in {'creature','character','vehicle','mechanical'} or any(isinstance(x,dict) and x.get('moving') is True for x in parts):
        required_categories.add('articulation')
    for missing in sorted(required_categories - categories.keys()):errors.append(f'missing QA category {missing}')

    review = data.get('review') if isinstance(data.get('review'),dict) else {}
    rev_status = review.get('status', 'pending')
    if rev_status not in {'approved','pending','rejected'}: errors.append('invalid reviewer status')
    inspected = set(_array(review.get('inspected_image_ids')))
    if not inspected.issubset(image_ids): errors.append('review mentions nonexistent image IDs')
    if rev_status == 'approved':
        if review.get('reviewer_role') != 'fidelity-auditor':errors.append('approval requires fidelity-auditor declaration')
        if not _nonempty(review.get('notes')): errors.append('approval missing review summary')
        if inspected != image_ids: errors.append('approval needs claimed inspection of every included image')
        if _array(review.get('blockers')): errors.append('approval has unresolved blockers')
        for category,check in categories.items():
            if check.get('status') not in {'PASS','NA'}:
                errors.append(f'approval contradicts check {category} status {check.get("status")}')
    if rev_status == 'rejected' and not _array(review.get('blockers')):
        warnings.append('rejected review should describe specific blockers')
    if not any(isinstance(x,dict) and isinstance(x.get('origin'),str) and x['origin'].startswith('generated') for x in images):
        warnings.append('no generated images: G1-R may not be necessary')

    ready=(not errors and rev_status=='approved')
    status = ('BLOCKED_INVALID_CONTRACT' if errors else 'PENDING_VISUAL_QA' if rev_status=='pending' else 'REJECTED_VISUAL_QA' if rev_status=='rejected' else 'REVIEW_DECLARED_APPROVED')
    return {'contract_version':SCHEMA_VERSION,'project_id':data.get('project_id'),'status':status,
            'ready_for_gcb':ready,'visual_anatomy_tested_by_script':False,
            'visual_review_declaration_only':True,'errors':errors,'warnings':warnings,
            'image_files':files,'images_count':len(images),'parts_count':len(parts),'steps_count':len(steps)}


def handoff(data: dict, report: dict):
    lines = [f'# Codex — referencias visuais para {data.get("project_id", "projeto")}', '',
             '> As imagens sao orientacoes visuais; a especificacao numerica GCB controla as transformacoes reais.',
             '> Vistas geradas e medidas nao calibradas sao inferidas. Este arquivo NAO comprova fidelidade visual ou fisica.', '',
             f'Estado do contrato: **{report["status"]}**', '', '## Imagens / procedencia']
    for im in _array(data.get('images')):
        if not isinstance(im,dict):continue
        lines.append(f'- `{im.get("id")}` — `{im.get("path")}`; vista `{im.get("view")}`; origem `{im.get("origin")}`; confianca `{im.get("confidence")}`')
    lines += ['', '## Partes e operacoes de construcao']
    for part in _array(data.get('parts')):
        if not isinstance(part,dict):continue
        lines += [f'### {part.get("id")} — {part.get("label")}',
                  f'- Geometria base: `{part.get("primitive")}`; malha separada: `{bool(part.get("separate_mesh"))}`; mover: `{bool(part.get("moving"))}`',
                  f'- Referencia: {", ".join(_array(part.get("image_ids")))}; confianca `{part.get("confidence")}`',
                  f'- Estrutura/conexoes: {part.get("structural_note", "")}; liga com {", ".join(_array(part.get("connection_ids")))}',
                  f'- Execucao: {part.get("build_instruction", "")}',
                  f'- Pivo candidato (nunca validado apenas por imagem): `{part.get("pivot")}`', '']
    lines += ['## Etapas verificaveis']
    for n,step in enumerate(_array(data.get('modeling_steps')), 1):
        if not isinstance(step,dict):continue
        lines += [f'{n}. **{step.get("id")}** ({", ".join(_array(step.get("part_ids")))}) — {step.get("instruction")}',
                  f'   - Aceitacao: {step.get("acceptance")}']
    lines += ['', '## Revisor / risco residual']
    rev=data.get('review') or {}
    lines += [f'- Declaracao de revisao: `{rev.get("status", "pending")}`; papel `{rev.get("reviewer_role", "nao indicado")}`',
              f'- Observacoes: {rev.get("notes", "NAO REVISADO")}',
              '- Comparar renders reais no Blender com as imagens; validar pivôs, mesh, clip e exportacao em G1.5-G8.', '']
    return '\n'.join(lines)


def main(argv=None):
    p=argparse.ArgumentParser(description='GCB G1-R reference image QA metadata gate (NOT visual inspection)')
    p.add_argument('command',choices=('validate','handoff'))
    p.add_argument('manifest',type=Path)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--gcb-spec',type=Path,default=None)
    p.add_argument('--out',type=Path,default=None)
    args=p.parse_args(argv)
    try:
        data=json.loads(args.manifest.read_text(encoding='utf-8'))
        spec=json.loads(args.gcb_spec.read_text(encoding='utf-8')) if args.gcb_spec else None
        result=evaluate(data,args.root,spec)
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        result={'status':'BLOCKED_INVALID_CONTRACT','ready_for_gcb':False,'errors':[str(exc)]}
        data={}
    if args.command=='handoff':
        if not result.get('ready_for_gcb'):
            print(json.dumps(result,indent=2,ensure_ascii=False));return 4
        payload=handoff(data,result)
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(payload,encoding='utf-8')
        else: print(payload)
    else:
        payload=json.dumps(result,indent=2,ensure_ascii=False)
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(payload+'\n',encoding='utf-8')
        print(payload)
    return 0 if result.get('ready_for_gcb') else 4


if __name__=='__main__':sys.exit(main())
