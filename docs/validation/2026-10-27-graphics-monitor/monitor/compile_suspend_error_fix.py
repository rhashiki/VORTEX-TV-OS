#!/usr/bin/env python3
from pathlib import Path
import difflib,hashlib,json,shlex,subprocess
BASE=Path('/workspace/build01-graphics-next/monitor')
KERNEL=Path('/workspace/build01-sd-next/kernel-sd/source')
KOUT=Path('/workspace/build01-sd-next/kernel-sd/out')
source=KERNEL/'arch/arm/mach-rockchip/rockchip_pm.c'
original=source.read_bytes()
old=b'''\tif (psci_suspend_available()) {
\t\tRKPM_DDR_FUN(prepare);
\t\tcpu_suspend(0, rk_lpmode_enter);
\t\tRKPM_DDR_FUN(finish);
\t\treturn 0;
\t}
'''
new=b'''\tif (psci_suspend_available()) {
\t\tint ret;

\t\tRKPM_DDR_FUN(prepare);
\t\tret = cpu_suspend(0, rk_lpmode_enter);
\t\tRKPM_DDR_FUN(finish);
\t\treturn ret;
\t}
'''
assert original.count(old)==1
patched=original.replace(old,new)
local=BASE/'rockchip_pm.c';local.write_bytes(patched)
patch=BASE/'kernel-propagate-psci-suspend-error.patch'
patch.write_text(''.join(difflib.unified_diff(original.decode().splitlines(keepends=True),patched.decode().splitlines(keepends=True),fromfile='a/arch/arm/mach-rockchip/rockchip_pm.c',tofile='b/arch/arm/mach-rockchip/rockchip_pm.c')))
check=subprocess.run(['git','apply','--check',str(patch)],cwd=KERNEL,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(BASE/'suspend-patch-check.log').write_text(check.stdout)
assert check.returncode==0
recorded=(KOUT/'arch/arm/mach-rockchip/.rockchip_pm.o.cmd').read_text().splitlines()[0].split(' := ',1)[1]
base_cmd=shlex.split(recorded)
commands=[]
for label,src in [('before',source),('after',local)]:
 cmd=list(base_cmd)
 cmd[cmd.index('-o')+1]=str(BASE/('rockchip_pm-'+label+'.o'))
 cmd[-1]=str(src)
 cmd=[('-Wp,-MD,'+str(BASE/('rockchip_pm-'+label+'.d'))) if x.startswith('-Wp,-MD,') else x for x in cmd]
 proc=subprocess.run(cmd,cwd=KOUT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (BASE/('rockchip_pm-'+label+'.compile.log')).write_text(proc.stdout)
 commands.append({'label':label,'cwd':str(KOUT),'command':cmd,'exit_code':proc.returncode,'log':'rockchip_pm-'+label+'.compile.log'})
 if proc.returncode:raise RuntimeError(label+' actual-source object compile failed')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert source.read_bytes()==original
report={'schema_version':1,'scope':'Minimal errno propagation fix compiled as actual ARM kernel translation unit with existing kernel configuration; not linked into a full new kernel or executed.','kernel_revision':'6c04d006ae881944d32c19e68b992d0bd5ab4fde','source':'arch/arm/mach-rockchip/rockchip_pm.c','original_sha256':hashlib.sha256(original).hexdigest(),'patched_sha256':sha(local),'patch_sha256':sha(patch),'git_apply_check':'pass','commands':commands,'before_object_sha256':sha(BASE/'rockchip_pm-before.o'),'after_object_sha256':sha(BASE/'rockchip_pm-after.o'),'old_source_and_output_preserved':True,'limits':['Does not implement CPU_SUSPEND in OP-TEE; unsupported suspend will be reported as an error instead of unconditional success.','Only compile-checked actual translation unit; no full kernel link, hardware execution or suspend/resume test.','Existing constrained SD kernel artifact remains unchanged and does not contain this patch.']}
(BASE/'suspend-error-fix-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='commands'},indent=2))
