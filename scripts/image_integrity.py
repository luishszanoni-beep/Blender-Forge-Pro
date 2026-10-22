"""Lightweight image integrity check for model reference and QA evidence.

PNG validates chunk boundaries, CRC, IHDR and IDAT/IEND. JPEG/WebP require
Pillow decoder. This is NOT semantic/visual inspection of the image content.
"""
from __future__ import annotations
import struct
import zlib
from pathlib import Path

MAX_FILE=200*1024*1024


def inspect(path: Path) -> dict:
    try:
        path=Path(path)
        if not path.is_file():
            return {'status':'FAIL','reason':'missing file'}
        if path.stat().st_size>MAX_FILE:
            return {'status':'FAIL','reason':'image exceeds 200MiB preflight limit'}
        ext=path.suffix.lower()
        if ext=='.png':
            data=path.read_bytes()
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                return {'status':'FAIL','reason':'PNG signature mismatch'}
            off=8;seen_ihdr=False;seen_idat=False;seen_iend=False;dims=None
            while off<len(data):
                if off+12>len(data):return {'status':'FAIL','reason':'truncated PNG chunk'}
                n=struct.unpack_from('>I',data,off)[0]
                tag=data[off+4:off+8]
                if off+12+n>len(data):return {'status':'FAIL','reason':'PNG chunk out of range'}
                content=data[off+8:off+8+n]
                crc=struct.unpack_from('>I',data,off+8+n)[0]
                if (zlib.crc32(tag+content)&0xffffffff)!=crc:
                    return {'status':'FAIL','reason':'PNG CRC mismatch'}
                if not seen_ihdr:
                    if tag!=b'IHDR' or n!=13:return {'status':'FAIL','reason':'IHDR not first or invalid'}
                    w,h=struct.unpack_from('>II',content)
                    if not 0<w<=32768 or not 0<h<=32768:return {'status':'FAIL','reason':'invalid image dimensions'}
                    dims=[w,h];seen_ihdr=True
                if tag==b'IDAT':seen_idat=True
                if tag==b'IEND':
                    seen_iend=True
                    if n!=0 or off+12+n!=len(data):return {'status':'FAIL','reason':'invalid IEND/trailing bytes'}
                    break
                off+=12+n
            if not (seen_ihdr and seen_idat and seen_iend):
                return {'status':'FAIL','reason':'PNG requires IHDR IDAT IEND'}
            return {'status':'PASS','dimensions':dims,'scope':'PNG chunk structural integrity; not pixel/visual validation'}
        if ext in ('.jpg','.jpeg','.webp'):
            try:
                from PIL import Image
            except ImportError:
                return {'status':'UNVERIFIED','reason':'Pillow missing; JPEG/WebP cannot be decoded here'}
            with Image.open(path) as im:
                if im.format != ('JPEG' if ext in ('.jpg','.jpeg') else 'WEBP'):
                    return {'status':'FAIL','reason':'image contents differ from extension'}
                sz=im.size;im.verify()
            return {'status':'PASS','dimensions':list(sz),'scope':'decoder verified; not semantic quality'}
        return {'status':'UNVERIFIED','reason':'unsupported image format'}
    except (OSError,ValueError,struct.error) as e:
        return {'status':'FAIL','reason':str(e)}
