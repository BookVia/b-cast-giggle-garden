"""Strict PNG cache integrity checks using only the standard library."""
import struct,zlib
from pathlib import Path
def valid_png(path,width=1920,height=1080):
 try:
  data=Path(path).read_bytes()
  if data[:8]!=b'\x89PNG\r\n\x1a\n':return False
  at=8;compressed=[];seen_end=False;shape=None
  while at<len(data):
   if at+12>len(data):return False
   size=struct.unpack('>I',data[at:at+4])[0];kind=data[at+4:at+8];end=at+8+size
   if end+4>len(data):return False
   payload=data[at+8:end];crc=struct.unpack('>I',data[end:end+4])[0]
   if zlib.crc32(kind+payload)&0xffffffff!=crc:return False
   if shape is None and kind!=b'IHDR':return False
   if kind==b'IHDR':
    if shape is not None or size!=13:return False
    shape=struct.unpack('>IIBBBBB',payload)
   if kind==b'IDAT':compressed.append(payload)
   if kind==b'IEND':
    if size!=0 or end+4!=len(data):return False
    seen_end=True;break
   at=end+4
  if not seen_end or not compressed or not shape:return False
  w,h,bits,color,compression,filter_method,interlace=shape
  channels={0:1,2:3,4:2,6:4}.get(color)
  if w!=width or h!=height or bits not in (8,16) or not channels or compression or filter_method or interlace:return False
  expected=h*(1+w*channels*(bits//8))
  decoder=zlib.decompressobj();raw=decoder.decompress(b''.join(compressed),expected+1)
  return decoder.eof and not decoder.unused_data and len(raw)==expected
 except (OSError,ValueError,struct.error,zlib.error):return False
