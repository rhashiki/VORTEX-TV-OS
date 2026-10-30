from pathlib import Path
import hashlib,json,os,subprocess,tarfile
ROOT=Path(__file__).resolve().parent
MIRROR=ROOT/'tree'
DEST=MIRROR/'prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8'
BIONIC=Path('/workspace/build01-platform-next/research/rockchip-bionic')
PIN='8b2e5b977118ebb8447cdf429c4a6be534c4fd1b'
def sha(data):return hashlib.sha256(data).hexdigest()
records=[];links=[];payload=0
with tarfile.open(ROOT/'host-gcc48-r6.tar.gz') as archive:
 for m in archive.getmembers():
  p=DEST/m.name
  if m.isfile():
   raw=archive.extractfile(m).read();got=p.read_bytes();assert got==raw,m.name
   assert p.stat().st_mode&0o777 == m.mode&0o777,m.name
   payload+=len(got);records.append({'path':m.name,'bytes':len(got),'sha256':sha(got)})
  elif m.issym():
   assert os.readlink(p)==m.linkname,m.name
   try:
    target=p.resolve(strict=True);status='resolved_within_mirror'
   except RuntimeError:
    assert m.linkname==p.name,m.name
    target=None;status='preserved_upstream_self_reference'
   except FileNotFoundError:
    target=p.resolve(strict=False);status='preserved_upstream_dangling_reference'
   if target is not None:assert target==MIRROR or MIRROR in target.parents,m.name
   links.append({'path':m.name,'link_target':m.linkname,'resolution':status,'resolved_target':str(target) if target else None})
  elif m.isdir():assert p.is_dir(),m.name
  else:raise AssertionError(m.name)
header=MIRROR/'bionic/libc/include/stdatomic.h'
original=subprocess.check_output(['git','--no-replace-objects','-C',str(BIONIC),'show',PIN+':libc/include/stdatomic.h'])
assert header.read_bytes()==original
provenance={'source_repository':'https://github.com/rockchip-android/bionic','source_revision':PIN,'source_path':'libc/include/stdatomic.h','bytes':len(original),'sha256':sha(original),'copied_exactly_from_git_blob':True,'upstream_link_target':'../../../../../../../../bionic/libc/include/stdatomic.h','upstream_symlink_unmodified':True}
(ROOT/'evidence/bionic-header-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(ROOT/'evidence/extracted-files.json').write_text(json.dumps(records,indent=2)+'\n')
(ROOT/'evidence/extracted-symlinks.json').write_text(json.dumps(links,indent=2)+'\n')
summary={'status':'pass','regular_files':len(records),'symlinks':len(links),'regular_payload_bytes':payload,'all_regular_bytes_modes_match_archive':True,'all_symlink_targets_match_archive':True,'unresolved_links_are_preserved_upstream':[x for x in links if x['resolution']!='resolved_within_mirror'],'selected_bionic_cross_project_header_sha256':sha(original),'scope':'pinned host toolchain extraction only, not Android build or hardware compatibility'}
(ROOT/'evidence/extraction-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='unresolved_links_are_preserved_upstream'},indent=2))
