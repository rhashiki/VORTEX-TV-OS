from pathlib import Path
import hashlib,json,subprocess
root=Path(__file__).resolve().parent
cases=root/'cases';cases.mkdir(exist_ok=True)
ev=root/'evidence';ev.mkdir(exist_ok=True)
sources=json.loads((root/'sources.json').read_text())
# This is GNUmake variable expansion only: no compiler or AOSP platform build.
# Disable shell calls (including upstream version.sh), and use no-op include
# destinations for Android module registration. Paths and flags are inspected.
def expand(label,patched,platform,gpu,residual):
 name=f'{label}-'+('patched' if patched else 'before')+f'-{platform}-{gpu}-'+('residual' if residual else 'clean')
 directory=cases/name;directory.mkdir(exist_ok=True)
 if residual: (directory/'hardware/arm').mkdir(parents=True,exist_ok=True)
 if patched: source=root/label/'Android.mk'
 else:
  source=directory/'Android.mk'
  source.write_bytes(subprocess.check_output(['git','show','HEAD:Android.mk'],cwd=root/label))
 harness=directory/'selection.mk'
 harness.write_text(f'''# DIAGNOSTIC ONLY: module registration and shell calls are disabled.
SHELL := /bin/false
CLEAR_VARS := /dev/null
BUILD_SHARED_LIBRARY := /dev/null
BUILD_MULTI_PREBUILT := /dev/null
my-dir = {source.parent}
PLATFORM_SDK_VERSION := 25
TARGET_BOARD_PLATFORM := {platform}
TARGET_BOARD_PLATFORM_GPU := {gpu}
TARGET_BOARD_PLATFORM_PRODUCT := box
TARGET_BOARD_HARDWARE := rk30board
include {source}
$(info RESULT_CFLAGS=$(LOCAL_CFLAGS))
$(info RESULT_INCLUDES=$(LOCAL_C_INCLUDES))
$(info RESULT_MODULE=$(LOCAL_MODULE))
$(info RESULT_SHARED=$(LOCAL_SHARED_LIBRARIES))
.PHONY: diagnostic
diagnostic:
''')
 p=subprocess.run(['make','--no-print-directory','-f',str(harness),'diagnostic'],cwd=directory,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (ev/(name+'.log')).write_text(p.stdout)
 fields={}
 for line in p.stdout.splitlines():
  if line.startswith('RESULT_'):
   key,val=line.split('=',1);fields[key.removeprefix('RESULT_')]=val.replace(str(source.parent),'<MODULE_SOURCE>')
 return {'case':name,'source_file':str(source),'field_paths_normalized_to_module_source':True,'exit_code':p.returncode,'fields':fields,'log':name+'.log'}
results=[]
for patched,platform,gpu,residual in [(False,'rk322x','mali400',False),(False,'rk322x','mali400',True),(True,'rk322x','mali400',False),(True,'rk322x','mali400',True),(True,'rk322x','mali-t760',False),(False,'rk3288','mali-t760',False),(False,'rk3288','mali-t760',True),(True,'rk3288','mali-t760',False),(True,'rk3288','mali-t760',True)]:
 results.append(expand('gralloc',patched,platform,gpu,residual))
for patched,platform in [(False,'rk322x'),(True,'rk322x'),(False,'rk3288'),(True,'rk3288')]:
 results.append(expand('hwcomposer',patched,platform,'mali400' if platform=='rk322x' else 'mali-t760',True))
by_name={r['case']:r for r in results}
def find(label,patched,platform,gpu,residual):return by_name[f'{label}-'+('patched' if patched else 'before')+f'-{platform}-{gpu}-'+('residual' if residual else 'clean')]
checks={}
a=find('gralloc',False,'rk322x','mali400',True)
checks['upstream_residual_directory_selects_MALI600']='-DMALI_600' in a['fields']['CFLAGS']
for residual in [False,True]:
 r=find('gralloc',True,'rk322x','mali400',residual)
 checks[f'patched_rk322x_legacy_selection_residual_{residual}']=r['exit_code']==0 and '-DGRALLOC_32_BITS' in r['fields']['CFLAGS'] and '-DMALI_600' not in r['fields']['CFLAGS'] and r['fields']['MODULE']=='gralloc.rk30board'
checks['patched_rk322x_wrong_GPU_rejected']=find('gralloc',True,'rk322x','mali-t760',False)['exit_code']!=0
for residual in [False,True]:
 before=find('gralloc',False,'rk3288','mali-t760',residual)
 after=find('gralloc',True,'rk3288','mali-t760',residual)
 checks[f'non_rk322x_gralloc_fields_preserved_residual_{residual}']=before['fields']==after['fields'] and before['exit_code']==after['exit_code']==0
before=find('hwcomposer',False,'rk322x','mali400',True)
after=find('hwcomposer',True,'rk322x','mali400',True)
checks['upstream_HWC_UMP_include_before_selected_gralloc']=before['fields']['INCLUDES'].index('hardware/rockchip/libgralloc_ump')<before['fields']['INCLUDES'].index('hardware/rockchip/libgralloc ')
includes=after['fields']['INCLUDES'].split()
checks['rk322x_HWC_uses_selected_gralloc_only']='hardware/rockchip/libgralloc' in includes and 'hardware/rockchip/libgralloc_ump' not in includes and 'hardware/intel/libgralloc' not in includes
checks['non_rk322x_HWC_fields_preserved']=find('hwcomposer',False,'rk3288','mali-t760',True)['fields']==find('hwcomposer',True,'rk3288','mali-t760',True)['fields']
# Exact replay into new tiny directories; no old worktree mutation.
replay={}
for label in ['gralloc','hwcomposer','vendor']:
 d=root/'replay'/label;d.mkdir(parents=True,exist_ok=True)
 name='device-vendor.mk' if label=='vendor' else 'Android.mk'
 original=subprocess.check_output(['git','show','HEAD:'+name],cwd=root/label)
 (d/name).write_bytes(original)
 patches=[]
 if label=='vendor':patches.append(Path('/workspace/vortex-build/rom/sdcard/patches/0006-vendor-omit-bluetooth.patch'))
 patches.append(root/(label+'-rk322x-source-hals.patch' if label=='vendor' else label+'-rk322x-source-selection.patch'))
 for patch in patches:
  subprocess.run(['git','apply','--check',str(patch)],cwd=d,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  subprocess.run(['git','apply',str(patch)],cwd=d,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert (d/name).read_bytes()==(root/label/name).read_bytes()
 replay[label]={'revision':sources[label]['revision'],'patches':[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in patches],'byte_identical_replay':True,'result_sha256':hashlib.sha256((d/name).read_bytes()).hexdigest()}
base=(root/'vendor-after-0006.mk').read_bytes().splitlines(keepends=True)
modified=(root/'vendor/device-vendor.mk').read_bytes().splitlines(keepends=True)
removed=[line for line in base if line not in modified]
checks['vendor_exactly_three_removals']=len(removed)==3 and len(base)-len(modified)==3 and all(any(n in line for n in [b'/gralloc.default.so:',b'/gralloc.rk30board.so:',b'/hwcomposer.rk30board.so:']) for line in removed)
assert all(checks.values()),checks
result={'schema_version':1,'scope':'Diagnostic GNUmake selection and exact source-patch replay only; no HAL compilation, linking or hardware claims. Shell calls and module registration disabled in harness.','checks':checks,'case_results':results,'patch_replay':replay,'vendor_removed_lines':[l.decode().rstrip() for l in removed],'limits':['Mali/OMX private buffer ABI and other ioctl interfaces remain unverified.','Only the pinned candidates are patched. This does not prove the final system file inventory.','A complete Android build must provide the rebuilt HAL modules; no prebuilts are substituted.']}
(ev/'source-selection-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'cases':len(results),'checks':checks,'patch_replay':replay},indent=2))
