#!/usr/bin/env python3
"""GCB stage G1.5: validate blueprint and generate Codex-facing construction plates.
Usage: python scripts/gcb.py validate INPUT.json
       python scripts/gcb.py prepare INPUT.json --out /project/planning/gcb --require-png
"""
import argparse
import json
import sys
from pathlib import Path
from gcb_core import create_handoff, fingerprint, load_spec, sheet_svg, validate, write_json
from blender_tool_router import load_index, plan_gcb, report_markdown


def main():
    parser=argparse.ArgumentParser(description='Blender Forge Pro GCB construction planning')
    cmd=parser.add_subparsers(dest='command',required=True)
    for name in ('validate','prepare'):
        sub=cmd.add_parser(name)
        sub.add_argument('spec',type=Path)
        sub.add_argument('--out',type=Path,default=None)
        if name=='prepare':
            sub.add_argument('--require-png',action='store_true')
            sub.add_argument('--installed-blender-version',default=None,help='Optional observed Blender version; not an API verification')
            sub.add_argument('--intake-report',type=Path,default=None,help='Optional verified G0-F intake report')
            sub.add_argument('--reference-qa-report',type=Path,default=None,help='G1-R audited source-image report, required by policy for generated source images')
            sub.add_argument('--excellence-references',type=Path,default=None,help='Optional 3DERL selection JSON, non-authoritative examples for Codex handoff')
    args=parser.parse_args()
    try:spec=load_spec(args.spec)
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e)},ensure_ascii=False));return 2
    report=validate(spec)
    if args.command=='validate':
        print(json.dumps(report,indent=2,ensure_ascii=False))
        if args.out:write_json(args.out,report)
        return 0 if not report['errors'] else 2
    if report['errors']:
        print(json.dumps(report,indent=2,ensure_ascii=False));return 2
    if args.out is None:
        parser.error('prepare requires --out')
    if args.intake_report is not None:
        try:
            intake=json.loads(args.intake_report.read_text(encoding='utf-8'))
        except (OSError,ValueError,json.JSONDecodeError) as e:
            print(json.dumps({'status':'BLOCKED_FILE_INTAKE','error':str(e)},ensure_ascii=False))
            return 4
        if not isinstance(intake,dict) or intake.get('ready_for_g1') is not True or intake.get('errors') or intake.get('missing_required'):
            print(json.dumps({'status':'BLOCKED_FILE_INTAKE','error':'G0-F required input incomplete'},ensure_ascii=False))
            return 4
        # Intake checks source presence only. It is not visual/scene/fidelity approval.
    if args.reference_qa_report is not None:
        try:
            image_qa=json.loads(args.reference_qa_report.read_text(encoding='utf-8'))
        except (OSError,ValueError,json.JSONDecodeError) as exc:
            print(json.dumps({'status':'BLOCKED_REFERENCE_IMAGE_QA','error':str(exc)},ensure_ascii=False))
            return 5
        if not isinstance(image_qa,dict) or image_qa.get('ready_for_gcb') is not True or image_qa.get('status') != 'REVIEW_DECLARED_APPROVED' or image_qa.get('errors') or image_qa.get('project_id') != spec.get('project_id') or not image_qa.get('image_files'):
            print(json.dumps({'status':'BLOCKED_REFERENCE_IMAGE_QA','error':'G1-R source-image audit incomplete or not for this project'},ensure_ascii=False))
            return 5
        # This is a structured independent-review declaration, NOT machine visual/anatomy QA.
    excellence_examples=None
    if args.excellence_references is not None:
        try:
            from excellence_reference_router import load_catalog, validate_catalog
            excellence_examples=json.loads(args.excellence_references.read_text(encoding='utf-8'))
            curated=load_catalog()
            if validate_catalog(curated):raise ValueError('bundled exemplar catalog is invalid')
            selected=excellence_examples.get('selected',[])
            if excellence_examples.get('status')!='ADVISORY_EXEMPLARS_NOT_SOURCE_EVIDENCE' or not isinstance(selected,list) or len(selected)>3:
                raise ValueError('invalid exemplar plan; maximum 3 references, advisory only')
            official={x['id']:x for x in curated['entries']}
            ids=[]
            for ref in selected:
                if not isinstance(ref,dict) or not isinstance(ref.get('id'),str) or ref['id'] not in official:
                    raise ValueError('unrecognized exemplar reference')
                trusted=official[ref['id']]
                for field in ('title','provider','source_url','preview_url','license','learning_points'):
                    if ref.get(field)!=trusted[field]:raise ValueError('catalog record was modified: '+field)
                if ref.get('role')!='quality_exemplar_not_user_source':raise ValueError('quality exemplar role mismatch')
                ids.append(ref['id'])
            if len(set(ids))!=len(ids):raise ValueError('duplicate reference IDs')
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
            print(json.dumps({'status':'BLOCKED_INVALID_EXCELLENCE_PLAN','error':str(exc)},ensure_ascii=False))
            return 6
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    try:
        import cairosvg
    except ImportError:
        cairosvg=None
    if args.require_png and cairosvg is None:
        print('BLOQUEADO: --require-png precisa do pacote opcional cairosvg; SVG continuaria disponivel.',file=sys.stderr)
        return 3
    base=out/'sheets'
    base.mkdir(parents=True,exist_ok=True)
    plates=[('00_overview',sheet_svg(spec))]
    if len(spec['parts'])>=3:
        plates.append(('01_exploded',sheet_svg(spec,exploded=True)))
    for i,s in enumerate(spec['steps']):
        plates.append((f'{i+1:02d}_step_{s["id"]}',sheet_svg(spec,step=i)))
    images=[];png_count=0
    for stem,svg in plates:
        path=base/(stem+'.svg')
        path.write_text(svg,encoding='utf-8')
        images.append('sheets/'+stem+'.svg')
        if cairosvg is not None:
            png=base/(stem+'.png')
            try:
                cairosvg.svg2png(bytestring=svg.encode('utf-8'),write_to=str(png),output_width=1600,output_height=1180)
            except Exception as e:
                print(f'PNG_RENDER_FAILED for {stem}: {e}',file=sys.stderr)
                if args.require_png:return 3
            else:
                images.append('sheets/'+stem+'.png');png_count+=1
    write_json(out/'gcb_spec.json',spec)
    report.update({'reference_image_qa': 'REVIEW_DECLARED_APPROVED' if args.reference_qa_report else 'NOT_PROVIDED',
                   'spec_sha256':fingerprint(spec), 'technical_plates':len(plates), 'png_count':png_count,
                   'svg_count':len(plates), 'blender_executed':False,
                   'visual_similarity':'PENDING_VISUAL_QA',
                   'geometry_validation':'SPEC_VALIDATED_ONLY',
                   'g1_5_approval':'PENDING_INDEPENDENT_AUDIT'})
    if png_count<len(plates):
        report['warnings'].append('PNG unavailable for some sheets; SVG remains canonical. No visual model claim.')
    # Advisory Atlas tool selection accompanies the deterministic GCB handoff.
    # Selection never executes bpy, changes geometry, or approves fidelity.
    tool_appendix=''
    try:
        atlas=load_index()
        tool_plan=plan_gcb(atlas,spec,installed_version=args.installed_blender_version,limit=3)
        write_json(out/'blender_tool_plan.json',tool_plan)
        (out/'blender_tool_plan.md').write_text(report_markdown(tool_plan),encoding='utf-8')
        report['atlas_tool_selection']='ADVISORY_UNVERIFIED_API_NOT_EXECUTED'
        report['atlas_source_sha256']=atlas['source']['sha256']
        tool_appendix='\n\n## Consulta ao Atlas Blender (GCB v1.8)\n\n'
        tool_appendix+='Veja `blender_tool_plan.json` (dados) e `blender_tool_plan.md` (resumo com IDs/páginas).\n'
        tool_appendix+='São recomendações técnicas, NÃO comandos bpy validados. Confirmar API no Blender instalado antes de executar.\n'
    except (ValueError,OSError,KeyError,TypeError) as exc:
        report['atlas_tool_selection']='NOT_AVAILABLE_UNVERIFIED'
        report['warnings'].append('Atlas tool routing unavailable: '+str(exc))
        tool_appendix='\n\n## Consulta ao Atlas Blender\n\nIndisponível neste ambiente; não inventar comandos.\n'
    # Advisory gallery is verified against our own bundled CC0 catalog; arbitrary
    # edited outside text must not become instructions in the Codex handoff.
    excellence_appendix=''
    if excellence_examples is not None:
        (out/'quality_excellence_references.json').write_text(json.dumps(excellence_examples,indent=2,ensure_ascii=False),encoding='utf-8')
        excellence_appendix='\n\n## Referências comparativas de excelência 3D (3DERL v1.9)\n\n'
        excellence_appendix+='Exemplos CC0 apenas para ensinar construção, NÃO para copiar o design nem inferir medidas, malha, articulação ou rig. Arte do usuário prevalece.\n\n'
        for x in excellence_examples['selected']:
            excellence_appendix+=f"- **{x['title']}** — {x['provider']}: [fonte]({x['source_url']}) | [imagem remota]({x['preview_url']}). "
            excellence_appendix+='Princípio: '+x['learning_points'][0]+'\n'
        report['excellence_library']='NON_AUTHORITATIVE_VISUAL_PREVIEWS'
        report['excellence_example_count']=len(excellence_examples['selected'])
    write_json(out/'gcb_preflight.json',report)
    (out/'gcb_handoff.md').write_text(create_handoff(spec,report,images)+tool_appendix+excellence_appendix,encoding='utf-8')
    print(json.dumps({'status':report['status'],'output':str(out),'sheets':len(plates),
                      'png_count':png_count,'g1_5_approval':report['g1_5_approval']},ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
