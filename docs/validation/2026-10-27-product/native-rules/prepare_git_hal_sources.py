from pathlib import Path
import subprocess,hashlib,json
root=Path('/workspace/build01-product-next/native-rules');tree=root/'tree';repo=Path('/workspace/vortex-build')
base=Path('/workspace/build01-platform-next/research/mali-legacy')
old=root/'source-copies-attempt01';old.mkdir(exist_ok=True)
rows=[]
for name,upstream,pins,patches in [
 ('libgralloc',base/'gralloc-rk3328','c92fb8cd8becd57b025149f2861a2072b092ddea',['0002-gralloc-select-mali400-for-rk322x.patch']),
 ('hwcomposer',base/'hwcomposer-rk3328','d3ec43f2f751123ca5e7bda2d07eded4c6352a35',['0003-hwc-use-selected-gralloc-header.patch','0005-hwc-fix-format-policy-and-hdmi-strings.patch','0006-hwc-fix-diagnostic-formats.patch'])]:
 target=tree/'hardware/rockchip'/name
 if not (target/'.git').exists():
  target.rename(old/name)
  subprocess.run(['git','worktree','add','--detach',str(target),pins],cwd=upstream,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  for filename in patches:
   patch=repo/'rom/platform-reference/graphics/patches'/filename
   subprocess.run(['git','apply','--check',str(patch)],cwd=target,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   subprocess.run(['git','apply',str(patch)],cwd=target,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  for f in target.glob('*.cpp'):
   assert f.read_bytes()==(old/name/f.name).read_bytes(),f
 rows.append({'source':str(target),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=target,text=True).strip(),'patches':patches,'cpp_bytes_match_previous_staged_copy':True,'upstream_tracked_status':subprocess.check_output(['git','status','--porcelain'],cwd=upstream,text=True).splitlines()})
(root/'hal-source-worktree-provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
