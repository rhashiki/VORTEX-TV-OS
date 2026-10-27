#!/usr/bin/env python3
"""Replay only checked source patches, and compare bytes with the product tree."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path('/workspace/build01-product-next/source-replay')
GRAPH = Path('/workspace/build01-product-next/product-graph/tree')
REPO = Path('/workspace/vortex-build')
SD = REPO / 'rom/sdcard/patches'
GFX = REPO / 'rom/platform-reference/graphics/patches'
SPECS = [
    ('build', Path('/workspace/build01-platform-next/research/rockchip-build'), 'd2721c65c9282b31df7b79f85289ee6c4e636716', [Path('/workspace/build01-product-next/product-graph/build-vortex-sd-package-scope.patch')]),
    ('device/rockchip/rk322x', Path('/workspace/build01-sd-next/device-sd'), 'f33a129bfab6d9cc87184ee3bf032224801fa446', [SD/'0001-rk322x-sd-only-fstab.patch', SD/'0004-rk3229-sdk-sd-controller.patch']),
    ('device/rockchip/common', Path('/workspace/build01-sd-next/common-sd'), '3b1aa90ef43f9d34094739a211ad44bf9a2c0b74', [SD/'0002-common-sd-only-init.patch', SD/'0003-common-disable-internal-provisioning.patch', SD/'0005-common-remove-sd-factory-services.patch']),
    ('vendor/rockchip/rk322x', Path('/workspace/build01-sd-next/vendor-sd'), '50c7170ecb4bd907059db37f09f4767b301f2d15', [SD/'0006-vendor-omit-bluetooth.patch', GFX/'0004-vendor-use-source-graphics-hals.patch']),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def run(args, cwd):
    proc = subprocess.run(args, cwd=cwd, capture_output=True)
    return {'argv': args, 'returncode': proc.returncode, 'stdout': proc.stdout.decode('utf-8', 'replace'), 'stderr': proc.stderr.decode('utf-8', 'replace')}

results = {'scope': 'source_patch_replay_only', 'projects': [], 'stock_product_comparison': {}}
for rel, source, rev, patches in SPECS:
    dest = ROOT/'trees'/rel
    dest.mkdir(parents=True, exist_ok=False)
    archive = subprocess.check_output(['git', 'archive', rev], cwd=source)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
        tf.extractall(dest, filter='data')
    item = {'path':rel, 'upstream_base':rev, 'source_repository':str(source), 'archive_sha256':sha(archive), 'patches':[], 'mismatches':[], 'changed_files':[]}
    subprocess.run(['git','init','-q'],cwd=dest,check=True)
    subprocess.run(['git','add','.'],cwd=dest,check=True)
    for patch in patches:
        record = {'path':str(patch), 'sha256':sha(patch.read_bytes()), 'check':run(['git','apply','--check',str(patch)],dest)}
        if record['check']['returncode']:
            raise RuntimeError(record)
        record['apply'] = run(['git','apply',str(patch)],dest)
        if record['apply']['returncode']:
            raise RuntimeError(record)
        item['patches'].append(record)
    changed = subprocess.check_output(['git','diff','--name-only'],cwd=dest,text=True).splitlines()
    files = sorted(p for p in dest.rglob('*') if '.git' not in p.relative_to(dest).parts and (p.is_file() or p.is_symlink()))
    item['files_compared'] = len(files)
    records = []
    for p in files:
        sub = p.relative_to(dest).as_posix()
        actual = GRAPH/rel/sub
        if p.is_symlink():
            expected = os.readlink(p)
            matches = actual.is_symlink() and os.readlink(actual)==expected
            info = {'path':sub,'symlink':expected}
        else:
            digest = sha(p.read_bytes())
            matches = actual.is_file() and not actual.is_symlink() and sha(actual.read_bytes())==digest
            info = {'path':sub,'sha256':digest,'size':p.stat().st_size}
        records.append(info)
        if not matches:
            item['mismatches'].append(sub)
        if sub in changed:
            item['changed_files'].append(info)
    item['file_manifest_sha256'] = sha(json.dumps(records,sort_keys=True,separators=(',',':')).encode())
    (ROOT/(rel.replace('/','_')+'-files.json')).write_text(json.dumps(records,indent=2)+'\n')
    item['pass'] = not item['mismatches']
    results['projects'].append(item)

evidence = GRAPH.parent/'evidence'
for name in ('packages','copy-files','properties'):
    before = evidence/f'baseline-05-{name}.list'
    after = evidence/'rk322x_box'/f'{name}.list'
    a,b = before.read_bytes(),after.read_bytes()
    results['stock_product_comparison'][name] = {'before':str(before),'after':str(after),'before_sha256':sha(a),'after_sha256':sha(b),'byte_identical':a==b}
results['pass'] = all(p['pass'] for p in results['projects']) and all(v['byte_identical'] for v in results['stock_product_comparison'].values())
(ROOT/'source-replay.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'pass':results['pass'],'projects':[{k:p[k] for k in ('path','files_compared','pass','mismatches')} for p in results['projects']],'stock_product_comparison':results['stock_product_comparison']},indent=2))
raise SystemExit(0 if results['pass'] else 1)
