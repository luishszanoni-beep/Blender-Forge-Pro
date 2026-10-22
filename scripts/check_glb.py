#!/usr/bin/env python3
"""Self-contained structural GLB v2 checker. NOT visual/export-roundtrip proof."""
from __future__ import annotations
import argparse
import json
import struct
import sys
from pathlib import Path

JSON_TAG=b'JSON'; BIN_TAG=b'BIN\x00'; GLB_MAX=400*1024*1024


def analyze(path: Path) -> dict:
    errors,warnings=[],[];data={};counts={}
    path=Path(path)
    if not path.is_file():
        return {'status':'FAIL','errors':['file does not exist'],'warnings':[]}
    if path.stat().st_size > GLB_MAX:
        return {'status':'FAIL','errors':['file exceeds structural inspector 400 MiB limit'],'warnings':[]}
    raw=path.read_bytes()
    if len(raw)<20:
        return {'status':'FAIL','errors':['GLB too short'],'warnings':[]}
    magic,ver,declared_len=struct.unpack_from('<4sII',raw)
    if magic!=b'glTF' or ver!=2:
        errors.append('GLB magic/version must be glTF v2')
    if declared_len!=len(raw):
        errors.append('GLB header declared_length != file length')
    offset=12;chunks=[]
    while offset<len(raw):
        if offset+8>len(raw):
            errors.append('truncated chunk header');break
        clen, ctag=struct.unpack_from('<I4s',raw,offset);offset+=8
        if clen % 4:
            errors.append('chunk byte length not aligned to 4')
        if offset+clen>len(raw):
            errors.append('chunk exceeds file size');break
        chunks.append((ctag,raw[offset:offset+clen]));offset+=clen
    if not chunks or chunks[0][0]!=JSON_TAG:
        errors.append('first GLB chunk must be JSON');return {'status':'FAIL','errors':errors,'warnings':warnings}
    if len(chunks)>2 or (len(chunks)>1 and chunks[1][0]!=BIN_TAG):
        errors.append('expected JSON and optional BIN chunk only')
    try:
        data=json.loads(chunks[0][1].rstrip(b' \t\r\n\x00').decode('utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError) as e:
        errors.append(f'invalid GLB JSON chunk: {e}')
        return {'status':'FAIL','errors':errors,'warnings':warnings}
    if not isinstance(data,dict):
        errors.append('glTF root must be JSON object')
        return {'status':'FAIL','errors':errors,'warnings':warnings}
    if not isinstance(data.get('asset'),dict) or data.get('asset',{}).get('version')!='2.0':
        errors.append('glTF asset.version must be 2.0')
    for key in ('materials','images','meshes','nodes','skins','animations','scenes'):
        if not isinstance(data.get(key,[]),list):
            errors.append(f'{key} must be array');data[key]=[]
    binaries=chunks[1][1] if len(chunks)>1 and chunks[1][0]==BIN_TAG else b''
    buffers=data.get('buffers',[]);views=data.get('bufferViews',[]);accessors=data.get('accessors',[])
    if not isinstance(buffers,list) or not isinstance(views,list) or not isinstance(accessors,list):
        errors.append('buffer/byteview/accessor arrays invalid');buffers=[];views=[];accessors=[]
    for i,buf in enumerate(buffers):
        if not isinstance(buf,dict):errors.append(f'buffer[{i}] invalid');continue
        if 'uri' in buf:
            errors.append(f'buffer[{i}] external URI; GLB not self-contained')
        if not isinstance(buf.get('byteLength'),int) or buf['byteLength']<0:
            errors.append(f'buffer[{i}] invalid byteLength')
        elif i==0 and buf['byteLength']>len(binaries):
            errors.append('buffer[0] declares more bytes than BIN chunk')
        elif i==0 and len(binaries)-buf['byteLength']>3:
            warnings.append('BIN padded length difference >3 bytes')
    for i,bv in enumerate(views):
        if not isinstance(bv,dict):errors.append(f'bufferView[{i}] invalid');continue
        buff=bv.get('buffer');start=bv.get('byteOffset',0);size=bv.get('byteLength')
        if not isinstance(buff,int) or buff<0 or buff>=len(buffers):
            errors.append(f'bufferView[{i}] points to invalid buffer');continue
        if not isinstance(start,int) or start<0 or not isinstance(size,int) or size<0:
            errors.append(f'bufferView[{i}] invalid offset/length');continue
        if not isinstance(buffers[buff],dict) or start+size>buffers[buff].get('byteLength',-1):
            errors.append(f'bufferView[{i}] exceeds buffer range')
    for i,ac in enumerate(accessors):
        if not isinstance(ac,dict):errors.append(f'accessor[{i}] invalid');continue
        if 'bufferView' in ac and (not isinstance(ac['bufferView'],int) or not 0<=ac['bufferView']<len(views)):
            errors.append(f'accessor[{i}] points to invalid bufferView')
        if not isinstance(ac.get('count'),int) or ac['count']<0:
            errors.append(f'accessor[{i}] invalid count')
    meshes=data.get('meshes',[])
    if not isinstance(meshes,list) or not meshes:
        errors.append('GLB has no mesh objects');meshes=[]
    tris=0;primitive_count=0
    for mi,mesh in enumerate(meshes):
        if not isinstance(mesh,dict):errors.append(f'mesh[{mi}] invalid');continue
        prims=mesh.get('primitives',[])
        if not isinstance(prims,list) or not prims:
            errors.append(f'mesh[{mi}] has no primitives');continue
        for pj,p in enumerate(prims):
            primitive_count+=1
            if not isinstance(p,dict):errors.append(f'primitive {mi}:{pj} invalid');continue
            mode=p.get('mode',4)
            if not isinstance(mode,int) or mode not in range(7):
                errors.append(f'primitive {mi}:{pj} mode invalid');continue
            idx=p.get('indices')
            position=p.get('attributes',{}).get('POSITION') if isinstance(p.get('attributes'),dict) else None
            for label, ai in [('indices',idx),('POSITION',position)]:
                if ai is not None and (not isinstance(ai,int) or not 0<=ai<len(accessors)):
                    errors.append(f'primitive {mi}:{pj} invalid accessor {label}')
            if position is None:
                errors.append(f'primitive {mi}:{pj} missing POSITION')
            if idx is not None and isinstance(idx,int) and 0<=idx<len(accessors):
                n=accessors[idx].get('count',0)
            elif isinstance(position,int) and 0<=position<len(accessors):
                n=accessors[position].get('count',0)
            else:n=0
            if not isinstance(n,int):n=0
            if mode==4:
                if n % 3:errors.append(f'primitive {mi}:{pj} triangle index count not divisible by 3')
                tris+=n//3
            elif mode in (5,6):tris+=max(0,n-2)
            if 'material' in p and (not isinstance(p['material'],int) or not 0<=p['material']<len(data.get('materials',[]))):
                errors.append(f'primitive {mi}:{pj} invalid material index')
    for i,img in enumerate(data.get('images',[])):
        if not isinstance(img,dict):errors.append(f'image[{i}] invalid');continue
        if 'uri' in img: errors.append(f'image[{i}] external URI; GLB not self-contained')
        if 'bufferView' in img and (not isinstance(img['bufferView'],int) or not 0<=img['bufferView']<len(views)):
            errors.append(f'image[{i}] invalid bufferView')
    counts={'meshes':len(meshes),'primitives':primitive_count,'estimated_triangles':tris,
            'materials':len(data.get('materials',[])),'nodes':len(data.get('nodes',[])),
            'skins':len(data.get('skins',[])),'animations':len(data.get('animations',[])),
            'images':len(data.get('images',[]))}
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'warnings':warnings,'counts':counts,
            'note':'Structural check only. Blender reimport, material and reference fidelity require separate actual tests.'}


def main():
    a=argparse.ArgumentParser();a.add_argument('file');a.add_argument('--out');args=a.parse_args()
    report=analyze(Path(args.file));s=json.dumps(report,indent=2,ensure_ascii=False)+'\n';print(s,end='')
    if args.out:Path(args.out).write_text(s,encoding='utf-8')
    return 0 if report['status']=='PASS' else 2

if __name__=='__main__':sys.exit(main())
