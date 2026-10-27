from pathlib import Path
import json,hashlib,subprocess,shlex
root=Path('/workspace/build01-graphics-next/graphics'); ev=root/'evidence'; ev.mkdir(exist_ok=True)
kernel=Path('/workspace/build01-sd-next/kernel-sd/source'); out=kernel.parent/'out'
lib=root/'libhardware'; baseline=root/'baseline/include/hardware'; baseline.mkdir(parents=True,exist_ok=True)
pristine=subprocess.check_output(['git','show','HEAD:include/hardware/rk_fh.h'],cwd=lib)
(baseline/'rk_fh.h').write_bytes(pristine)
tc=Path('/workspace/build01-sd/kernel-work/toolchain/bin'); gcc=str(tc/'arm-linux-gnueabihf-gcc'); nm=str(tc/'arm-linux-gnueabihf-nm')
fields={
'rk_fb_area_par':['data_format','ion_fd','phy_addr','acq_fence_fd','x_offset','y_offset','xpos','ypos','xsize','ysize','xact','yact','xvir','yvir','fbdc_en','fbdc_cor_en','fbdc_data_format','data_space','reserved0'],
'rk_fb_win_par':['win_id','z_order','alpha_mode','g_alpha_val','mirror_en','area_par','reserved0'],
'rk_fb_win_cfg_data':['wait_fs','ret_fence_fd','rel_fence_fd','win_par'],
'rk_fb_wb_cfg':['data_format','ion_fd','phy_addr','xsize','ysize','reserved0','reversed1'],
'rk_lcdc_post_cfg':['xpos','ypos','xsize','ysize']}
# Expressions are evaluated after including the real complete header; declarations are never copied.
expressions={}
for typ, members in fields.items():
 if typ=='rk_fb_wb_cfg': continue
 expressions[f'{typ}__size']=f'sizeof(struct {typ})'
 expressions[f'{typ}__align']=f'__alignof__(struct {typ})'
 for member in members:
  expressions[f'{typ}__{member}__offset']=f'__builtin_offsetof(struct {typ}, {member})'
  expressions[f'{typ}__{member}__size']=f'sizeof(((struct {typ} *)0)->{member})'
wbexpressions={'rk_fb_win_cfg_data__wb_cfg__offset':'__builtin_offsetof(struct rk_fb_win_cfg_data, wb_cfg)', 'rk_fb_win_cfg_data__wb_cfg__size':'sizeof(((struct rk_fb_win_cfg_data *)0)->wb_cfg)'}
for typ in ['rk_fb_wb_cfg']:
 wbexpressions[f'{typ}__size']=f'sizeof(struct {typ})'
 wbexpressions[f'{typ}__align']=f'__alignof__(struct {typ})'
 for member in fields[typ]:
  wbexpressions[f'{typ}__{member}__offset']=f'__builtin_offsetof(struct {typ}, {member})'
  wbexpressions[f'{typ}__{member}__size']=f'sizeof(((struct {typ} *)0)->{member})'
source='#ifdef KERNEL_HEADER\n#include <linux/rk_fb.h>\n#else\n#include <hardware/rk_fh.h>\n#endif\n'
source+=''.join(f'char measure__{n}[({e}) + 1];\n' for n,e in expressions.items())
source+='#ifndef NO_WB\n'+''.join(f'char measure__{n}[({e}) + 1];\n' for n,e in wbexpressions.items())+'#endif\n'
source+='int abi_probe_no_runtime(void) { return 0; }\n'
(root/'contract_measure.c').write_text(source)
raw=(out/'drivers/video/rockchip/.rk_fb.o.cmd').read_text().splitlines()[0].split(' := ',1)[1]
args=shlex.split(raw)[3:]; assert args[0]=='-Wp,-MD,drivers/video/rockchip/.rk_fb.o.d'
kflags=[];i=0
while i<len(args):
 a=args[i]
 if a.startswith('-Wp,-MD,'): i+=1;continue
 if a=='-o': i+=2;continue
 if a in ['-c',str(kernel/'drivers/video/rockchip/rk_fb.c')]:i+=1;continue
 kflags.append(a);i+=1
uflags=['-march=armv7-a','-mabi=aapcs-linux','-mfloat-abi=hard','-fno-common','-std=gnu11','-Wall','-Wextra','-Werror','-I'+str(lib/'include')]
commands={}
def run(label,cmd,cwd=out,expect=0):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (ev/(label+'.log')).write_text(p.stdout)
 commands[label]={'argv':cmd,'cwd':str(cwd),'exit_code':p.returncode}
 assert p.returncode==expect,(label,p.stdout)
 return p.stdout

def measure(label,flags,cwd=out):
 obj=ev/(label+'.o')
 run(label,[gcc,*flags,'-c',str(root/'contract_measure.c'),'-o',str(obj)],cwd)
 symbols=run(label+'-symbols',[nm,'-S','--defined-only',str(obj)],cwd)
 values={}
 for line in symbols.splitlines():
  parts=line.split()
  if len(parts)==4 and parts[3].startswith('measure__'): values[parts[3].removeprefix('measure__')]=int(parts[1],16)-1
 return values
kernel_values=measure('kernel-header',kflags+['-DKERNEL_HEADER'])
beforeflags=['-I'+str(root/'baseline/include'),*uflags]
before=measure('userspace-before',beforeflags+['-DNO_WB'])
assert before['rk_fb_win_cfg_data__size']==904 and kernel_values['rk_fb_win_cfg_data__size']==908
assert all(before[n]==v for n,v in kernel_values.items() if n in before and n!='rk_fb_win_cfg_data__size')
expected='/* Expected values measured independently from the complete pinned kernel header. */\n'
for n,e in {**expressions,**wbexpressions}.items():expected+=f'typedef char require__{n}[({e}) == {kernel_values[n]} ? 1 : -1];\n'
(root/'expected-kernel-contract.h').write_text(expected)
(root/'contract_assert.c').write_text('#include <hardware/rk_fh.h>\n#include "expected-kernel-contract.h"\nint contract_assert_no_runtime(void) { return 0; }\n')
pre=subprocess.run([gcc,*beforeflags,'-c',str(root/'contract_assert.c'),'-o',str(ev/'userspace-before-contract.o')],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(ev/'userspace-before-contract.log').write_text(pre.stdout)
commands['userspace-before-contract']={'exit_code':pre.returncode,'argv':[gcc,*beforeflags,'-c',str(root/'contract_assert.c'),'-o',str(ev/'userspace-before-contract.o')]}
assert pre.returncode!=0
# Exact kernel writeback declaration, rather than padding or an ioctl shim.
h=lib/'include/hardware/rk_fh.h'; original=pristine; assert hashlib.sha256(original).hexdigest()=='e3d3629b706628ab3d46423551e25f7c2dfacc6f8b10e8100ed1253bb7e3de6e'
text=original.decode()
wb='''/* RK_FBIOSET_CONFIG_DONE ABI of kernel 6c04d006 (include/linux/rk_fb.h).
 * Keep zero-initialized unless writeback is explicitly implemented: the
 * kernel disables writeback only when both ion_fd and phy_addr are zero.
 */
struct rk_fb_wb_cfg {
\tu8  data_format;
\tshort ion_fd;
\tu32 phy_addr;
\tu16 xsize;
\tu16 ysize;
\tu8 reserved0;
\tu32 reversed1;
};

'''
assert text.count('struct rk_fb_area_par {')==1
text=text.replace('struct rk_fb_area_par {',wb+'struct rk_fb_area_par {').replace('struct  rk_lcdc_post_cfg post_cfg;','struct  rk_fb_wb_cfg wb_cfg;')
h.write_bytes(text.encode())
subprocess.run(['git','diff','--check'],cwd=lib,check=True)
patch=subprocess.check_output(['git','diff','--','include/hardware/rk_fh.h'],cwd=lib)
(root/'libhardware-rk-fb-kernel-contract.patch').write_bytes(patch)
after=measure('userspace-after',uflags)
assert after==kernel_values
run('userspace-after-contract',[gcc,*uflags,'-c',str(root/'contract_assert.c'),'-o',str(ev/'userspace-after-contract.o')])
result={'scope':'Full real kernel/userspace headers compiled for ARM; compile-time contract layout checks only, not a HAL link or ioctl runtime test.',
'kernel_revision':'6c04d006ae881944d32c19e68b992d0bd5ab4fde','libhardware_revision':'d0c81ba009240cb9ab38d75d7e88190055349c2a',
'kernel_header_sha256':hashlib.sha256((kernel/'include/linux/rk_fb.h').read_bytes()).hexdigest(),
'userspace_header_before_sha256':hashlib.sha256(original).hexdigest(),'userspace_header_after_sha256':hashlib.sha256(h.read_bytes()).hexdigest(),
'patch_sha256':hashlib.sha256(patch).hexdigest(),'measurements_before':before,'measurements_kernel':kernel_values,'measurements_after':after,
'common_prefix_measurements_match_before':True,'all_measurements_match_after':True,'checked_quantities':len(after),
'negative_compile_exit_code':pre.returncode,'positive_compile_exit_code':0,'commands':commands}
(ev/'header-contract-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if not k.startswith('measurements') and k!='commands'},indent=2))
