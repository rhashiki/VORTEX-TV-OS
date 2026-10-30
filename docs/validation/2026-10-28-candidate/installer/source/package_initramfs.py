#!/usr/bin/env python3
"""Create a deterministic component archive in memory; never opens a device."""
from pathlib import Path
import gzip,hashlib,json,stat

ROOT=Path(__file__).resolve().parent


def newc(entries):
    output=bytearray()
    for index,(name,mode,data,rmajor,rminor) in enumerate(entries+[('TRAILER!!!',0,b'',0,0)],1):
        encoded=name.encode()+b'\0'
        fields=(index,mode,0,0,2 if stat.S_ISDIR(mode) else 1,0,len(data),0,0,rmajor,rminor,len(encoded),0)
        output.extend(b'070701'+''.join('%08x'%v for v in fields).encode())
        output.extend(encoded)
        output.extend(b'\0'*(-len(output)%4))
        output.extend(data)
        output.extend(b'\0'*(-len(output)%4))
    return bytes(output)


def parse_newc(data):
    offset=0;records=[]
    while True:
        assert data[offset:offset+6]==b'070701'
        fields=[int(data[offset+6+i*8:offset+14+i*8],16) for i in range(13)]
        offset+=110;name=data[offset:offset+fields[11]-1].decode();offset+=fields[11]
        offset+=( -offset%4 )
        payload=data[offset:offset+fields[6]];offset+=fields[6];offset+=(-offset%4)
        if name=='TRAILER!!!':break
        records.append({'name':name,'mode':oct(fields[1]),'size_bytes':len(payload),
                        'rdev_major':fields[9],'rdev_minor':fields[10],
                        'sha256':hashlib.sha256(payload).hexdigest()})
    assert offset==len(data)
    return records


def main():
    binary=(ROOT/'artifacts/vortex-diagnostic-init').read_bytes()
    entries=[(n,stat.S_IFDIR|0o755,b'',0,0) for n in ('dev','proc','sys')]
    entries += [('dev/console',stat.S_IFCHR|0o600,b'',5,1),('init',stat.S_IFREG|0o755,binary,0,0)]
    raw=newc(entries);packed=gzip.compress(raw,compresslevel=9,mtime=0)
    assert raw==newc(entries) and packed==gzip.compress(raw,compresslevel=9,mtime=0)
    records=parse_newc(gzip.decompress(packed));assert len(records)==5
    for name,data in [('vortex-diagnostic-initramfs.cpio',raw),('vortex-diagnostic-initramfs.cpio.gz',packed)]:
        (ROOT/'artifacts'/name).write_bytes(data)
    report={'scope':'deterministic initramfs component only; no bootloader/kernel/Android image or hardware boot',
            'entries':records,'gzip_mtime':0,'root_uid_gid':0,
            'determinism_check':'same binary produces byte-identical newc and gzip within this tool invocation',
            'mount_or_device_operations':'none; dev/console is encoded as archive metadata only'}
    (ROOT/'evidence/initramfs-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'archive_entries':len(records),'newc_bytes':len(raw),'gzip_bytes':len(packed)}))


if __name__=='__main__':main()
