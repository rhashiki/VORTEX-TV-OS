from pathlib import Path
import shutil,json,subprocess,hashlib
root=Path('/workspace/build01-product-next/native-rules');tree=root/'tree';tree.mkdir(exist_ok=True)
source=Path('/workspace/build01-platform-next/research/rockchip-build')
if not (tree/'build').exists():shutil.copytree(source,tree/'build',ignore=shutil.ignore_patterns('.git','__pycache__'))
shutil.copyfile(tree/'build/core/root.mk',tree/'Makefile')
def link(src,dst):
 p=tree/dst;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.symlink_to(src,target_is_directory=True)
link('/workspace/build01-platform-next/aosp-app/tree/prebuilts/sdk','prebuilts/sdk')
link('/workspace/build01-platform-next/research/rockchip-bionic','bionic')
link('/workspace/build01-platform-next/research/rockchip-system-core','system/core')
link('/workspace/build01-graphics-next/graphics/libhardware','hardware/libhardware')
link('/workspace/build01-platform-next/research/rockchip-librkvpu','hardware/rockchip/librkvpu')
for src,dst in [('/workspace/build01-hal-next/gralloc-link/gralloc-source','hardware/rockchip/libgralloc'),('/workspace/build01-hal-next/hwc-format/source','hardware/rockchip/hwcomposer')]:
 if not (tree/dst).exists():shutil.copytree(src,tree/dst,ignore=shutil.ignore_patterns('.git'))
link('/workspace/build01-graphics-next/graphics/hal-build/libcxx-include','external/libcxx/include')
link('/workspace/build01-hal-next/hwc/native-headers/include','frameworks/native/include')
link('/workspace/build01-hal-next/hwc/native-headers/opengl/include','frameworks/native/opengl/include')
# Complete the same true GLES header subset that the prior ARM build used.
link('/workspace/build01-graphics-next/graphics/hal-build/native-opengl-include/GLES','frameworks/native/opengl/include/GLES')
meta={'scope':'Disposable real-make native rule investigation; not complete platform source tree.','rockchip_build_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'root_makefile_sha256':hashlib.sha256((tree/'Makefile').read_bytes()).hexdigest(),'no_existing_sources_modified':True}
(root/'tree-inputs.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta))
