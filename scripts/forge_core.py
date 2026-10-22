"""Blender Forge Pro portable project, evidence and artifact checks.

This module uses only the Python standard library; its success does not
indicate that any actual Blender modeling or visual inspection occurred.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,59}$")
DESTINATIONS = {"render", "web_glb", "roblox", "general"}
MODES = {"high_fidelity", "game_ready", "adaptive"}
VIEWS = {"front", "back", "left", "right", "top", "bottom", "front_left", "front_right", "back_left", "back_right", "detail"}
FORMATS = {"blend", "glb", "fbx", "obj", "usd"}
IMG_FORMATS = {".png", ".jpeg", ".jpg", ".webp", ".pdf"}
GATES = [f"G{i}" for i in range(9)]
STATES = {"PENDING", "BLOCKED", "READY_FOR_VISUAL_QA", "APPROVED", "REJECTED", "SKIPPED_NOT_APPLICABLE"}


def read_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def inside(root: Path, rel: Any, *, must_exist: bool = False) -> Path:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise ValueError("unsafe or empty relative path")
    p = Path(rel)
    if p.is_absolute() or any(x in ("..", ".") for x in p.parts):
        raise ValueError("absolute, dot or parent path not allowed")
    base = root.resolve()
    current = base
    for segment in p.parts:
        current = current / segment
        if current.is_symlink():
            raise ValueError('symlink path component not permitted')
    full = (base / p).resolve()
    if not full.is_relative_to(base):
        raise ValueError("path escapes project root")
    if must_exist and not full.is_file():
        raise ValueError("missing file or symbolic link not allowed")
    # symlink ancestors are resolved above; reject if chain links outside root.
    return full


def check_id(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def _dict(obj: Any) -> dict:
    return obj if isinstance(obj, dict) else {}


def _refs(project: dict) -> dict[str, dict]:
    return {r['id']: r for r in project.get('references', []) if isinstance(r, dict) and isinstance(r.get('id'), str)}


def validate_project(project: dict, root: Path, *, allow_missing_refs: bool = False) -> dict:
    errors, warnings = [], []
    req = ('schema_version', 'project_id', 'title', 'destination', 'mode', 'units', 'references', 'parts', 'deliverables')
    for field in req:
        if field not in project:
            errors.append(f"missing field: {field}")
    if project.get('schema_version') != '1.0':
        errors.append('schema_version must be 1.0')
    if not check_id(project.get('project_id')):
        errors.append('project_id invalid; use lowercase a-z, 0-9, - or _')
    if not isinstance(project.get('title'), str) or not project.get('title', '').strip():
        errors.append('title must be nonempty text')
    if project.get('destination') not in DESTINATIONS:
        errors.append('destination invalid')
    if project.get('mode') not in MODES:
        errors.append('mode invalid')
    if project.get('units') != 'm':
        errors.append('units must be m for consistent Blender scene scale')
    if project.get('goal', 'reference_match') not in ('reference_match', 'original_design'):
        errors.append('goal must be reference_match or original_design')
    if not isinstance(project.get('rig_required', False), bool):
        errors.append('rig_required must be boolean')
    refs = project.get('references', [])
    if not isinstance(refs, list):
        errors.append('references must be list')
        refs = []
    if not refs and project.get('goal', 'reference_match') == 'reference_match':
        errors.append('reference_match requires at least one source reference')
    ref_ids = set()
    for i, ref in enumerate(refs):
        if not isinstance(ref, dict):
            errors.append(f'references[{i}] must be object')
            continue
        rid = ref.get('id')
        if not check_id(rid) or rid in ref_ids:
            errors.append(f'references[{i}] id missing, invalid or duplicate')
        else:
            ref_ids.add(rid)
        if ref.get('view') not in VIEWS and ref.get('view') != 'unknown':
            errors.append(f'references[{i}] unsupported view')
        if ref.get('projection') not in ('orthographic', 'perspective', 'unknown'):
            errors.append(f'references[{i}] invalid projection')
        if ref.get('projection') == 'unknown':
            warnings.append(f'references[{i}] camera uncalibrated: pixel shape IoU cannot prove measured fidelity')
        try:
            fp = inside(root, ref.get('path'), must_exist=not allow_missing_refs)
            if fp.suffix.lower() not in IMG_FORMATS:
                errors.append(f'references[{i}] not a supported reference type')
            if not fp.exists():
                warnings.append(f'references[{i}] file not provided yet: {ref.get("path")}')
            elif fp.is_file() and fp.stat().st_size == 0:
                errors.append(f'references[{i}] file empty')
            elif fp.is_file():
                try:
                    with fp.open('rb') as f:
                        header = f.read(16)
                    ext=fp.suffix.lower()
                    sigok = ((ext=='.png' and header.startswith(b'\x89PNG\r\n\x1a\n'))
                             or (ext in ('.jpg','.jpeg') and header.startswith(b'\xff\xd8\xff'))
                             or (ext=='.webp' and header[:4]==b'RIFF' and header[8:12]==b'WEBP')
                             or (ext=='.pdf' and header.startswith(b'%PDF-')))
                    if not sigok: errors.append(f'references[{i}] extension does not match binary signature')
                except OSError as e:
                    errors.append(f'references[{i}] cannot read signature: {e}')
        except ValueError as e:
            errors.append(f'references[{i}] {e}')
    dims = project.get('dimensions_mm', {})
    if not isinstance(dims, dict):
        errors.append('dimensions_mm must be object')
    else:
        for axis, val in dims.items():
            if axis not in ('height', 'width', 'depth') or not isinstance(val, (int, float)) or isinstance(val, bool) or not 0 < val <= 1e7:
                errors.append(f'invalid dimensions_mm.{axis}')
    parts = project.get('parts', [])
    if not isinstance(parts, list) or not parts:
        errors.append('parts must be nonempty list')
        parts = []
    seen_part_ids, seen_feature_ids, geom_features = set(), set(), []
    for i, part in enumerate(parts):
        if not isinstance(part, dict):
            errors.append(f'parts[{i}] must be object')
            continue
        pid = part.get('id')
        if not check_id(pid) or pid in seen_part_ids:
            errors.append(f'parts[{i}] invalid/duplicate id')
        else:
            seen_part_ids.add(pid)
        if not isinstance(part.get('label'), str) or not part.get('label', '').strip():
            errors.append(f'parts[{i}] needs label')
        if not isinstance(part.get('required'), bool):
            errors.append(f'parts[{i}] requires bool required')
        if part.get('confidence') not in ('observed', 'inferred', 'unknown'):
            errors.append(f'parts[{i}] requires observed/inferred/unknown confidence')
        if not isinstance(part.get('locked', False), bool):
            errors.append(f'parts[{i}] locked must be bool')
        preflist=part.get('reference_ids', [])
        if not isinstance(preflist, list) or any(x not in ref_ids for x in preflist):
            errors.append(f'parts[{i}] references undefined source IDs')
        features = part.get('features', [])
        if not isinstance(features, list):
            errors.append(f'parts[{i}] features must be list')
            features = []
        for j,feat in enumerate(features):
            if not isinstance(feat, dict):
                errors.append(f'parts[{i}].features[{j}] invalid object')
                continue
            fid = feat.get('id')
            if not check_id(fid) or fid in seen_feature_ids:
                errors.append(f'parts[{i}].features[{j}] invalid/duplicate feature id')
            else:
                seen_feature_ids.add(fid)
            if feat.get('representation') not in ('geometry','material','either'):
                errors.append(f'feature {fid} representation invalid')
            if not isinstance(feat.get('required'), bool):
                errors.append(f'feature {fid} requires boolean required')
            srcs=feat.get('source_ref_ids', [])
            if not isinstance(srcs,list) or any(s not in ref_ids for s in srcs):
                errors.append(f'feature {fid} references undefined IDs')
            if feat.get('representation')=='geometry' and feat.get('required') is True:
                geom_features.append((pid,fid))
            if 'min_relief_mm' in feat:
                rv = feat.get('min_relief_mm')
                if feat.get('representation')!='geometry' or not isinstance(rv,(int,float)) or isinstance(rv,bool) or not 0 < rv <= 10000:
                    errors.append(f'feature {fid}: min_relief_mm needs geometry and positive numeric value')
    deliv = project.get('deliverables', [])
    if not isinstance(deliv,list) or not deliv or any(x not in FORMATS for x in deliv) or len(deliv)!=len(set(deliv)):
        errors.append('deliverables must be nonempty unique list of supported formats')
    else:
        if project.get('destination')=='web_glb' and 'glb' not in deliv:
            errors.append('web_glb projects must request glb output')
        if 'blend' not in deliv:
            warnings.append('editable .blend source not requested; this reduces auditability')
    budget = project.get('budgets', {})
    if not isinstance(budget, dict):
        errors.append('budgets must be object')
    else:
        for bkey in ('triangles_max','materials_max','glb_size_mb_max'):
            if bkey in budget:
                val=budget[bkey]
                if not isinstance(val,(int,float)) or isinstance(val,bool) or val<=0:
                    errors.append(f'budgets.{bkey} must be positive number')
    checks=project.get('checks', {})
    if not isinstance(checks, dict):
        errors.append('checks must be object')
    else:
        vs=checks.get('required_views',[])
        if not isinstance(vs,list) or len(vs)!=len(set(vs)) or any(v not in VIEWS for v in vs):
            errors.append('checks.required_views invalid or repeated')
    if project.get('mode') == 'game_ready' and not budget:
        warnings.append('game_ready has no explicit performance budget; supply target limits')
    return {"status":"FAIL" if errors else "PASS", "errors":errors, "warnings":warnings,
            "counts":{"references":len(refs),"parts":len(parts),"features":len(seen_feature_ids),"required_geometric_features":len(geom_features)}}


def route_project(project: dict) -> dict:
    steps = ["reference-analyst","geometry-architect"]
    needs_geometry = any(f.get('representation')=='geometry' and f.get('required') for p in project.get('parts',[]) if isinstance(p,dict) for f in p.get('features',[]) if isinstance(f,dict))
    if needs_geometry or project.get('mode')=='high_fidelity':
        steps.append('sculpt-surface')
    steps.append('material-specialist')
    if project.get('mode') in ('game_ready','adaptive') or project.get('destination') in ('web_glb','roblox'):
        steps.append('topology-engineer')
    if project.get('rig_required', False):
        steps.append('rigging-specialist')
    steps.extend(['fidelity-auditor','export-engineer','fidelity-auditor'])
    return {"project_id":project.get('project_id'),"ordered_skills":steps,
            "notes":["G6 SKIPPED_NOT_APPLICABLE for static projects" if not project.get('rig_required') else "G6 mandatory: pose QA", "Fidelity Auditor is independent at G2/G3 and final G7/G8"]}


def _verify_files(root: Path, files: Any, errors: list, label: str) -> int:
    if not isinstance(files,list):
        errors.append(f'{label} must be list')
        return 0
    total=0
    for j,path in enumerate(files):
        try:
            p=inside(root,path,must_exist=True)
            if p.stat().st_size <= 0:
                errors.append(f'{label}[{j}] file empty: {path}')
            elif p.suffix.lower() in ('.png','.jpg','.jpeg','.webp'):
                from image_integrity import inspect
                v=inspect(p)
                if v['status']!='PASS':
                    errors.append(f'{label}[{j}] image invalid/unverified: {v.get("reason")}')
                else:total+=1
            else:
                total+=1
        except ValueError as e:
            errors.append(f'{label}[{j}] {e}: {path}')
    return total


def check_evidence(project: dict, evidence: dict, root: Path) -> dict:
    errors,warnings=[],[]
    if evidence.get('schema_version')!='1.0' or evidence.get('project_id')!=project.get('project_id'):
        errors.append('evidence schema_version/project_id mismatch')
    gates=evidence.get('gates', {})
    if not isinstance(gates,dict):
        errors.append('gates must be object');gates={}
    required_states={}
    for g in GATES:
        val=gates.get(g, {})
        if not isinstance(val,dict) or val.get('state') not in STATES:
            errors.append(f'{g} missing/invalid state')
            continue
        st=val['state'];required_states[g]=st
        if g=='G6' and not project.get('rig_required',False):
            if st not in ('SKIPPED_NOT_APPLICABLE','APPROVED'):
                errors.append('G6 for static project must be SKIPPED_NOT_APPLICABLE or APPROVED')
            continue
        if st!='APPROVED':
            errors.append(f'{g} cannot be accepted: {st}')
        evidence_files=val.get('evidence_files', [])
        if g in ('G2','G3','G4','G5','G7','G8') and st=='APPROVED' and not evidence_files:
            errors.append(f'{g} approved without evidence_files')
        if evidence_files:
            _verify_files(root, evidence_files, errors, f'{g}.evidence_files')
    blockers=evidence.get('critical_blockers')
    if not isinstance(blockers,list):
        errors.append('critical_blockers must be array')
    elif blockers:
        errors.append(f'{len(blockers)} critical blockers remain')
    views=evidence.get('views', [])
    if not isinstance(views,list):
        views=[];errors.append('views must be array')
    inspected=[]
    for j,v in enumerate(views):
        if not isinstance(v,dict):
            errors.append(f'views[{j}] invalid object');continue
        if v.get('inspected') is True and isinstance(v.get('reviewer'),str) and v.get('reviewer','').strip():
            inspected.append(v.get('view'))
            _verify_files(root,[v.get('file')],errors,f'views[{j}].file')
    required_views=_dict(project.get('checks')).get('required_views',[])
    waived=evidence.get('user_waived_views', [])
    if not isinstance(waived,list):
        errors.append('user_waived_views must be list');waived=[]
    for v in required_views:
        if v not in inspected:
            if v in waived and evidence.get('waiver_authorized_by_user') is True:
                warnings.append(f'user-authorized waiver: {v}')
            else:
                errors.append(f'required view not inspected: {v}')
    if not inspected and not waived:
        errors.append('no visual views actually inspected')
    proofs=evidence.get('geometry_proofs',[])
    if not isinstance(proofs,list):
        errors.append('geometry_proofs must be list');proofs=[]
    prooftable={p.get('feature_id'):p for p in proofs if isinstance(p,dict)}
    for part in project.get('parts',[]):
        if not isinstance(part,dict):continue
        for feature in part.get('features',[]):
            if not isinstance(feature,dict) or feature.get('representation')!='geometry' or feature.get('required') is not True:continue
            fid=feature.get('id');proof=prooftable.get(fid)
            if not proof or proof.get('part_id')!=part['id']:
                errors.append(f'missing evaluated mesh proof: {fid}')
                continue
            if proof.get('evaluated_mesh_verified') is not True or proof.get('reviewed') is not True:
                errors.append(f'geometry proof incomplete/unreviewed: {fid}')
            if project.get('destination') in ('web_glb','roblox') and proof.get('export_verified') is not True:
                errors.append(f'geometry export proof missing: {fid}')
            _verify_files(root,proof.get('evidence_files', []),errors,f'geometry_proofs.{fid}')
            if not proof.get('evidence_files'):
                errors.append(f'geometry proof missing image/evidence: {fid}')
    outputtable={x.get('format'):x for x in evidence.get('deliverables',[]) if isinstance(x,dict)}
    for fmt in project.get('deliverables',[]):
        out=outputtable.get(fmt)
        if not out:
            errors.append(f'missing deliverable record: {fmt}');continue
        if not isinstance(out.get('path'),str) or not out['path'].lower().endswith('.'+fmt):
            errors.append(f'{fmt} extension mismatch');continue
        present=_verify_files(root,[out['path']],errors,f'deliverable {fmt}')
        if present:
            payload=inside(root,out['path'],must_exist=True)
            with payload.open('rb') as stream:
                head=stream.read(24)
            if fmt=='blend' and not head.startswith(b'BLENDER'):
                errors.append('blend file lacks BLENDER header')
            if fmt=='glb':
                if not head.startswith(b'glTF'):
                    errors.append('GLB file lacks glTF header')
                else:
                    from check_glb import analyze
                    structure=analyze(payload)
                    if structure['status']!='PASS':
                        errors.append('GLB structural inspection failed: '+'; '.join(structure['errors'][:3]))
        if out.get('roundtrip_checked') is not True and fmt in ('glb','fbx'):
            errors.append(f'{fmt} reimport/roundtrip not verified')
    final=evidence.get('final_review',{})
    if not isinstance(final,dict) or final.get('decision')!='APPROVED' or not isinstance(final.get('reviewer'),str) or not final.get('reviewer','').strip():
        errors.append('final review must be APPROVED with real reviewer identity')
    return {"status":"FAIL" if errors else "PASS", "errors":errors,"warnings":warnings,
            "note":"Evidence-record consistency only; requires genuine visual review and independent Blender roundtrip results.",
            "summary":{"required_views":len(required_views),"inspected_views":len(set(inspected)),"geometry_proofs":len(proofs),"recorded_outputs":len(outputtable)}}


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def build_manifest(root: Path, candidates: list[str]) -> dict:
    out=[]
    if not isinstance(candidates,list) or not candidates:
        raise ValueError('specify one or more filenames')
    if len(candidates)!=len(set(candidates)):
        raise ValueError('duplicate manifest path')
    for c in sorted(candidates):
        fp=inside(root,c,must_exist=True)
        if fp.stat().st_size > 400 * 1024 * 1024:
            raise ValueError(f'artifact too large for built-in manifest (400MiB): {c}')
        out.append({'path':c,'size_bytes':fp.stat().st_size,'sha256':sha256_file(fp)})
    return {'schema_version':'1.0','files':out}


def verify_manifest(root: Path, manifest: dict) -> dict:
    errors=[];seen=set()
    if manifest.get('schema_version')!='1.0':
        errors.append('schema_version invalid')
    for i,item in enumerate(manifest.get('files',[])):
        if not isinstance(item,dict):
            errors.append(f'files[{i}] not object');continue
        rel=item.get('path')
        if rel in seen:
            errors.append(f'duplicate path: {rel}');continue
        seen.add(rel)
        try:
            fp=inside(root,rel,must_exist=True)
            if fp.stat().st_size!=item.get('size_bytes') or sha256_file(fp)!=item.get('sha256'):
                errors.append(f'hash or size mismatch: {rel}')
        except ValueError as e:
            errors.append(f'{e}: {rel}')
    if not seen:
        errors.append('empty manifest')
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'checked_files':len(seen)}
