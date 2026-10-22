#!/usr/bin/env python3
"""GCB G0-F: ask for project source files before the geometry blueprint.

This module checks only local files explicitly declared by the coordinator.
It does NOT claim to inspect ChatGPT attachments, cloud resources or Blender scenes.
This gate does not perform visual QA or parse untrusted 3D documents.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

IMG = {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp', '.svg', '.gif'}
DOC = {'.pdf', '.txt', '.md', '.csv', '.json'}
MODEL = {'.blend', '.fbx', '.glb', '.gltf', '.obj', '.stl', '.dae'}
VIDEO = {'.mp4', '.mov', '.webm', '.avi', '.gif'}
MAP = IMG | {'.exr', '.hdr', '.tga'}
ROLES = {
    'art_reference': IMG | {'.pdf'},
    'orthographic_reference': IMG | {'.pdf'},
    'detail_reference': IMG | {'.pdf'},
    'style_reference': IMG | {'.pdf'},
    'technical_document': DOC | {'.dxf', '.dwg'},
    'source_mesh': MODEL,
    'rig_reference': MODEL | IMG | {'.pdf'},
    'material_map': MAP,
    'animation_reference': VIDEO | MODEL | IMG,
}
VIEWS = {'front', 'back', 'left', 'right', 'side', 'top', 'bottom', 'three_quarter', 'unknown'}
INTENTS = {'reference_model', 'edit_existing', 'original_model'}
TARGETS = {'roblox', 'web_glb', 'render', 'general'}
SAFE_ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,59}$')


def _missing(code, title, accepted, reason, text_ok=False):
    return {'code': code, 'title': title, 'accepted': accepted,
            'reason': reason, 'text_accepted': text_ok}


def _safe_file(root: Path, raw: str):
    """Reject traversal, absolute paths, symlinks and non-files; read metadata only."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError('empty file path')
    relative = Path(raw)
    if relative.is_absolute() or '..' in relative.parts or relative.drive:
        raise ValueError('absolute or traversal path rejected')
    clean_root = root.resolve()
    path = clean_root / relative
    if not path.resolve().is_relative_to(clean_root):
        raise ValueError('file resolves outside project root')
    candidate = clean_root
    for segment in relative.parts:
        candidate = candidate / segment
        if candidate.is_symlink():
            raise ValueError('symlink rejected')
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('file is missing or empty')
    return path


def inspect_assets(manifest: dict, root: Path):
    valid, errors, warnings = [], [], []
    seen_ids, seen_paths = set(), set()
    assets = manifest.get('assets', [])
    if not isinstance(assets, list) or len(assets) > 1000:
        return [], ['assets must be a list of at most 1000 records'], []
    for i, item in enumerate(assets):
        if not isinstance(item, dict):
            errors.append(f'asset {i}: expected object')
            continue
        ident, role, path = item.get('id'), item.get('role'), item.get('path')
        if not isinstance(ident, str) or not SAFE_ID.fullmatch(ident):
            errors.append(f'asset {i}: invalid ID')
            continue
        if ident in seen_ids:
            errors.append(f'asset {ident}: duplicate ID')
            continue
        seen_ids.add(ident)
        if role not in ROLES:
            errors.append(f'asset {ident}: unknown role')
            continue
        if not isinstance(path, str):
            errors.append(f'asset {ident}: path must be a string')
            continue
        if path in seen_paths:
            warnings.append(f'asset {ident}: duplicate path; counted once')
            continue
        seen_paths.add(path)
        try:
            verified = _safe_file(root, path)
        except (ValueError, OSError) as exc:
            errors.append(f'asset {ident}: {exc}')
            continue
        if verified.suffix.lower() not in ROLES[role]:
            errors.append(f'asset {ident}: unsupported extension for {role}')
            continue
        view = item.get('view', 'unknown')
        if view not in VIEWS:
            errors.append(f'asset {ident}: invalid view')
            continue
        valid.append({'id': ident, 'role': role, 'path': path,
                      'view': view, 'bytes': verified.stat().st_size})
    return valid, errors, warnings


def evaluate_intake(manifest: dict, root: Path) -> dict:
    if not isinstance(manifest, dict):
        return {'status': 'BLOCKED_INVALID_MANIFEST', 'ready_for_g1': False,
                'errors': ['manifest must be an object']}
    errors = []
    project_id = manifest.get('project_id')
    if not isinstance(project_id, str) or not SAFE_ID.fullmatch(project_id):
        errors.append('project_id must be a stable simple ID')
    intent = manifest.get('intent')
    if intent not in INTENTS:
        errors.append('intent must be reference_model, edit_existing, or original_model')
    target = manifest.get('target')
    if target not in TARGETS:
        errors.append('target must be roblox, web_glb, render or general')
    needs = manifest.get('needs', {})
    provided = manifest.get('provided_information', {})
    declined = manifest.get('unavailable', [])
    if not isinstance(needs, dict) or not isinstance(provided, dict):
        errors.append('needs and provided_information must be objects')
        needs, provided = {}, {}
    if not isinstance(declined, list) or not all(isinstance(x, str) for x in declined):
        errors.append('unavailable must be an array of item codes')
        declined = []
    for key, value in needs.items():
        if key not in {'rigging', 'animation', 'strict_fidelity', 'exact_materials',
                       'retarget_rig', 'absolute_scale_required', 'existing_scene_access'} or type(value) is not bool:
            errors.append(f'needs.{key}: unknown key or expected boolean')
    assets, asset_errors, warnings = inspect_assets(manifest, root)
    errors.extend(asset_errors)
    roles = {a['role'] for a in assets}
    visual_roles = {'art_reference', 'orthographic_reference'}
    has_visual = bool(visual_roles & roles)
    has_model = 'source_mesh' in roles
    has_tech = 'technical_document' in roles
    brief = provided.get('brief')
    has_brief = isinstance(brief, str) and bool(brief.strip())
    has_scale = bool(provided.get('verified_dimensions')) or bool(provided.get('verified_dimension_source'))
    has_rig_spec = isinstance(provided.get('rig_spec'), str) and bool(provided.get('rig_spec').strip())
    requested = []
    recommended = []
    info = []
    if intent == 'reference_model' and not (has_visual or has_model):
        requested.append(_missing('primary_visual', 'Arte original ou modelo 3D de referencia',
                                  'PNG/JPG/WEBP/PDF (ou BLEND/FBX/GLB/OBJ)',
                                  'A reconstrucao fiel exige ao menos uma referencia acessivel.'))
    if intent == 'edit_existing' and not (has_model or needs.get('existing_scene_access', False)):
        requested.append(_missing('editable_source', 'Arquivo do modelo existente',
                                  'BLEND/FBX/GLB/OBJ ou acesso autorizado a cena existente',
                                  'Nao alterar ou reconstruir uma cena desconhecida por suposicao.'))
    if intent == 'original_model' and not (has_brief or has_visual or has_model):
        requested.append(_missing('creative_brief', 'Descricao original do modelo',
                                  'Texto com forma, estilo e finalidade ou imagens conceituais',
                                  'Nao ha informacao suficiente para definir o objeto.', True))
    if needs.get('absolute_scale_required') and not has_scale:
        requested.append(_missing('physical_scale', 'Dimensoes e fonte de escala verificavel',
                                  'Desenho tecnico/PDF/CAD com escala ou medidas fornecidas em texto',
                                  'Nao e possivel afirmar milimetros a partir de uma imagem nao calibrada.', True))
    if needs.get('retarget_rig') and not (('rig_reference' in roles) or has_rig_spec):
        requested.append(_missing('target_skeleton', 'Esqueleto ou especificacao do rig de destino',
                                  'FBX/BLEND/GLB com ossos ou lista de hierarquia/orientacoes em texto',
                                  'Retargeting exato depende de um rig conhecido.', True))

    if intent == 'reference_model' and has_visual and needs.get('strict_fidelity', False):
        views = {a['view'] for a in assets if a['role'] in visual_roles and a['view'] != 'unknown'}
        if len(views) < 2 and 'multi_angle_views' not in declined:
            recommended.append(_missing('multi_angle_views', 'Vistas adicionais do mesmo modelo',
                                        'Frente, costas, laterais e superior em PNG/JPG/WEBP/PDF',
                                        'Reduz ambiguidade de volume; se nao houver, as superficies ocultas serao inferidas.'))
        if 'detail_reference' not in roles and 'closeups' not in declined:
            recommended.append(_missing('closeups', 'Close-ups de componentes complexos',
                                        'Imagens da cabeca, asas, encaixes, patas, cauda ou relevos',
                                        'Ajuda a preservar detalhes que se perdem no enquadramento geral.'))
    if needs.get('exact_materials') and not ({'material_map', 'style_reference'} & roles):
        if 'material_sources' not in declined:
            recommended.append(_missing('material_sources', 'Arquivos de material ou paleta',
                                        'Albedo, roughness, metallic, normal, emission, paleta ou guia visual',
                                        'Ajuda a reproduzir acabamento; nao prova detalhe geometrico.'))
    if needs.get('animation'):
        if 'animation_reference' not in roles and 'motion_reference' not in declined:
            recommended.append(_missing('motion_reference', 'Videos ou arquivos com movimentos',
                                        'MP4/MOV/WEBM/GIF ou FBX de animacao',
                                        'Melhora poses e timing; nao impede criar animacoes originais.'))
        clips = provided.get('animation_clips')
        if not isinstance(clips, list) or not any(isinstance(x,str) and x.strip() for x in clips):
            info.append(_missing('animation_clips', 'Quais animacoes deseja?',
                                 'Ex.: Idle, Walk, Attack, Fly (resposta em texto)',
                                 'Define o escopo das animacoes antes do rigging.', True))
    if needs.get('rigging') and not needs.get('retarget_rig') and not has_rig_spec:
        info.append(_missing('rig_preferences', 'Preferencias de rig (se houver)',
                             'Rig personalizado, R15 ou articulacoes especificas (texto)',
                             'Sem restricao especifica, o rig sera planejado para o objeto.', True))
    if target == 'roblox':
        if not isinstance(provided.get('roblox_constraints'), str) or not provided.get('roblox_constraints').strip():
            info.append(_missing('engine_constraints', 'Restricoes de importacao no Roblox (se houver)',
                                 'Limites de triangulos, rig, escala, formato ou nomeacao (texto)',
                                 'Opcional quando nao existem exigencias proprias.', True))
    if has_tech and needs.get('absolute_scale_required') and not has_scale:
        warnings.append('Technical file exists, but scale has not been verified; still request calibrated dimensions.')
    for item in recommended:
        if item['code'] in declined:
            warnings.append(f"Declared unavailable: {item['code']}")
    if errors:
        status = 'BLOCKED_INVALID_MANIFEST'
    elif requested:
        status = 'AWAITING_REQUIRED_INPUT'
    elif recommended:
        status = 'READY_WITH_ASSUMPTIONS'
    else:
        status = 'READY_FOR_REFERENCE_ANALYSIS'
    return {'schema_version': '1.0', 'project_id': project_id,
            'status': status, 'ready_for_g1': not (errors or requested),
            'verified_assets': assets, 'missing_required': requested,
            'recommended_files': recommended, 'text_questions': info,
            'unavailable_recorded': sorted(set(declined)),
            'warnings': warnings, 'errors': errors,
            'visual_qa': 'NOT_EXECUTED', 'gcb_g1_5_approved': False}


def format_request(report: dict) -> str:
    lines = ['# Coleta de arquivos para o Blender Forge Pro / GCB', '']
    files = report.get('verified_assets', [])
    if files:
        lines.extend(['**Arquivos ja recebidos e verificados:**', ''])
        for a in files:
            lines.append(f"- `{a['path']}` ({a['role']}, {a['view']})")
        lines.append('')
    sections = [
        ('**Arquivos/informacoes essenciais pendentes:**', report.get('missing_required', [])),
        ('**Arquivos recomendados, se voce tiver:**', report.get('recommended_files', [])),
        ('**Informacoes que podem ser respondidas por texto:**', report.get('text_questions', [])),
    ]
    for title, items in sections:
        if not items:
            continue
        lines.extend([title, ''])
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. **{item['title']}** - {item['accepted']}. {item['reason']}")
        lines.append('')
    if report.get('missing_required'):
        lines.append('Envie os materiais essenciais em uma so resposta. Arquivos recomendados podem ser enviados juntos.')
    elif report.get('recommended_files'):
        lines.append('Ja posso iniciar a analise com o que existe. Se tiver as referencias adicionais, envie-as agora; senao, seguirei com inferencias declaradas.')
    elif report.get('text_questions'):
        lines.append('Os arquivos essenciais estao presentes. Responda as preferencias acima apenas se elas afetarem o resultado desejado.')
    else:
        lines.append('Nao ha arquivos adicionais a solicitar nesta etapa. Prosseguir para G1, sem alegar validacao visual.')
    lines.append('Se alguma vista ou arquivo nao existir, diga "nao tenho"; nao inventarei vistas ou medidas.')
    if report.get('errors'):
        lines.extend(['', '**Corrigir inventario de arquivos:**', ''])
        lines.extend(f"- {item}" for item in report['errors'])
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description='GCB source file intake and human request generator')
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True,
                        help='Output directory relative to project root')
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError('project root must be directory')
        # Output must remain project-local; never overwrite input assets.
        output = root / args.out
        if args.out.is_absolute() or '..' in args.out.parts or not output.resolve().is_relative_to(root):
            raise ValueError('output must stay under project root')
        if output.is_symlink():
            raise ValueError('output symlink rejected')
        data = json.loads(args.manifest.read_text(encoding='utf-8'))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'BLOCKED_INVALID_MANIFEST', 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    report = evaluate_intake(data, root)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'intake_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (output / 'file_request.md').write_text(format_request(report), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'ready_for_g1': report['ready_for_g1'],
                      'required_count': len(report['missing_required']),
                      'recommended_count': len(report['recommended_files']),
                      'report': str(output / 'intake_report.json')}, ensure_ascii=False))
    return 2 if report['errors'] else 3 if report['missing_required'] else 0


if __name__ == '__main__':
    sys.exit(main())
