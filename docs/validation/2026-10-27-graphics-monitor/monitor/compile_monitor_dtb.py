#!/usr/bin/env python3
"""Repeat the recorded kernel DT compilation with isolated outputs only."""
from pathlib import Path
import hashlib,json,subprocess,sys
BASE=Path('/workspace/build01-graphics-next/monitor')
KERNEL=Path('/workspace/build01-sd-next/kernel-sd/source')
KOUT=Path('/workspace/build01-sd-next/kernel-sd/out')
DTS=KERNEL/'arch/arm/boot/dts'
commands=[]
for name,source in [('sd-original',DTS/'rk3229-sdk-sd-reference.dts'),('sd-monitor-gated',BASE/'rk3229-sdk-sd-monitor-gated.dts')]:
 dep=BASE/(name+'.cpp.d');pre=BASE/(name+'.preprocessed.dts');dtb=BASE/(name+'.dtb')
 cpp=['python3','/workspace/vortex-build/tools/legacy_kernel_gcc_wrapper.py','/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf-gcc','-E','-Wp,-MD,'+str(dep),'-nostdinc','-I'+str(DTS),'-I'+str(DTS/'include'),'-I'+str(KERNEL/'include'),'-I'+str(KOUT/'include'),'-undef','-D__DTS__','-x','assembler-with-cpp','-o',str(pre),str(source)]
 dtc=[str(KOUT/'scripts/dtc/dtc'),'-O','dtb','-o',str(dtb),'-b','0','-i',str(DTS),'-d',str(BASE/(name+'.dtc.d')),str(pre)]
 for label,cmd in [('cpp',cpp),('dtc',dtc)]:
  p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (BASE/(name+'.'+label+'.log')).write_text(p.stdout)
  commands.append({'label':name+'-'+label,'command':cmd,'exit_code':p.returncode,'log':name+'.'+label+'.log'})
  if p.returncode:raise RuntimeError(cmd)
 (BASE/(name+'.decompiled.dts')).write_bytes(subprocess.check_output([str(KOUT/'scripts/dtc/dtc'),'-I','dtb','-O','dts',str(dtb)]))
old=KOUT/'arch/arm/boot/dts/rk3229-sdk-sd-reference.dtb'
assert (BASE/'sd-original.dtb').read_bytes()==old.read_bytes(),'Base source no longer reproduces prior compiled DTB'
(BASE/'dtb-build-commands.json').write_text(json.dumps({'scope':'Standalone DT preprocessing/compilation using the prior recorded kernel command, no kernel rebuild. All new outputs are outside old source/out trees.','prior_command_file':str(KOUT/'arch/arm/boot/dts/.rk3229-sdk-sd-reference.dtb.cmd'),'base_DTB_byte_identical_to_prior':True,'commands':commands},indent=2)+'\n')
print('PASS: four commands exit 0; original source reproduces prior DTB byte-for-byte')
