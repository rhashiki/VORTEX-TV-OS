from pathlib import Path
import shutil,subprocess,json,hashlib
root=Path('/workspace/build01-product-next/product-graph');tree=root/'tree';tree.mkdir(exist_ok=True)
source_paths={
'build':Path('/workspace/build01-platform-next/research/rockchip-build'),
'device/rockchip/rk322x':Path('/workspace/build01-sd-next/device-sd'),
'device/rockchip/common':Path('/workspace/build01-sd-next/common-sd'),
'vendor/rockchip/rk322x':Path('/workspace/build01-sd-next/vendor-sd')}
records={}
for dest,src in source_paths.items():
 out=tree/dest
 shutil.copytree(src,out,ignore=shutil.ignore_patterns('.git'),dirs_exist_ok=True,symlinks=True)
 records[dest]={'source':str(src),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=src,text=True).strip(),'local_diff_sha256':hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=src)).hexdigest()}
# Apply already approved graphics vendor-copy exclusion on top of0006.
p=Path('/workspace/vortex-build/rom/platform-reference/graphics/patches/0004-vendor-use-source-graphics-hals.patch')
subprocess.run(['git','apply','--check',str(p)],cwd=tree/'vendor/rockchip/rk322x',check=True)
subprocess.run(['git','apply',str(p)],cwd=tree/'vendor/rockchip/rk322x',check=True)
(root/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
(tree/'out').mkdir(exist_ok=True)
