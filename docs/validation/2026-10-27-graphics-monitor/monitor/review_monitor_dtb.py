#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/workspace/build01-platform-next/uboot-sd/out/scripts/dtc/pylibfdt')
import libfdt
BASE=Path('/workspace/build01-graphics-next/monitor')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def nodes(p):
 f=libfdt.Fdt(p.read_bytes());out={}
 off=-1;depth=-1;stack=[]
 while True:
  off,depth=f.next_node(off,depth,quiet=(libfdt.NOTFOUND,))
  if off<0 or depth<0:break
  stack=stack[:depth]
  stack.append(f.get_name(off))
  path="/"+"/".join(stack[1:])
  props={}
  po=f.first_property_offset(off,quiet=(libfdt.NOTFOUND,))
  while po>=0:
   v=f.get_property_by_offset(po)
   props[v.name]=bytes(v).hex()
   po=f.next_property_offset(po,quiet=(libfdt.NOTFOUND,))
  out[path]=props
 return out
original=nodes(BASE/'sd-original.dtb');gated=nodes(BASE/'sd-monitor-gated.dtb')
assert set(original)==set(gated)
diff=[]
for path in sorted(original):
 assert set(original[path])==set(gated[path])
 for prop in original[path]:
  if original[path][prop]!=gated[path][prop]:
   diff.append({'path':path,'property':prop,'before_hex':original[path][prop],'after_hex':gated[path][prop]})
assert len(diff)==2,diff
for d in diff:
 assert d['property']=='status' and bytes.fromhex(d['before_hex'])==b'okay\0' and bytes.fromhex(d['after_hex'])==b'disabled\0',diff
assert {x['path'] for x in diff}=={'/fiq-debugger','/dvfs/vd_logic/pd_ddr/clk_ddr'},diff
checks={
 'only_two_properties_changed':True,
 'fiq_debugger_disabled':gated['/fiq-debugger']['status']==b'disabled\0'.hex(),
 'legacy_DDR_DVFS_disabled':gated['/dvfs/vd_logic/pd_ddr/clk_ddr']['status']==b'disabled\0'.hex(),
 'PSCI_node_unchanged':original['/psci']==gated['/psci'],
 'suspend_node_unchanged':original['/rockchip_suspend']==gated['/rockchip_suspend'],
 'SD_controller_unchanged':original['/rksdmmc@30000000']==gated['/rksdmmc@30000000'],
 'internal_controllers_unchanged':all(original[p]==gated[p] for p in ['/rksdmmc@30020000','/nandc@30030000'])}
assert all(checks.values())
report={'schema_version':1,'scope':'Actual DTB structural comparison and source-gating review only, no physical execution or proof that every vendor SMC path is absent.','profile':{'file':'rk3229-sdk-sd-monitor-gated.dts','sha256':sha(BASE/'rk3229-sdk-sd-monitor-gated.dts')},'base_DTB':{'size_bytes':(BASE/'sd-original.dtb').stat().st_size,'sha256':sha(BASE/'sd-original.dtb'),'byte_identical_to_prior_compiled_DTB':True},'new_DTB':{'file':'sd-monitor-gated.dtb','size_bytes':(BASE/'sd-monitor-gated.dtb').stat().st_size,'sha256':sha(BASE/'sd-monitor-gated.dtb')},'node_count':len(gated),'differences':diff,'checks':checks,'registration_effect_in_examined_sources':{'fiq':'rk_fiq_debugger.c checks of_device_is_available(np) before register/init, returns -ENODEV for disabled node.','DDR':'of_dvfs_init uses for_each_available_child_of_node for clock nodes; disabled clk_ddr omitted. ddrfreq_init then gets no clk_ddr DVFS node and returns -EINVAL before callbacks, registrations, worker creation.'},'limits':['No full kernel recompile; same prior kernel binary/config, source-proven DT filtering only.','Vendor SIP version negotiation and suspend control boot calls remain compiled/reachable and return unknown under this monitor.','PSCI CPU_SUSPEND unsupported and kernel suspend error handling remain unresolved.','DDR callbacks remain in binary; paths outside the disabled legacy worker need separate review.','No monitor RAM reservations added; delivered Linux DTB must still reserve OP-TEE core/SHM.','No alternate UART console is enabled by this two-change profile.','No physical boot or R329Q hardware approval.']}
config=Path('/workspace/build01-sd-next/kernel-sd/out/.config').read_text()
report['console_observability']={
 'kernel_CONFIG_CMDLINE':'empty',
 'kernel_CONFIG_SERIAL_ROCKCHIP':'y',
 'kernel_CONFIG_SERIAL_ROCKCHIP_CONSOLE':'n',
 'chosen_bootargs':bytes.fromhex(gated['/chosen']['bootargs']).rstrip(b'\0').decode(),
 'UART_status':{p:bytes.fromhex(gated[p]['status']).rstrip(b'\0').decode() for p in ['/serial@11010000','/serial@11020000','/serial@11030000']},
 'UART2_pinctrl_0_hex':gated['/serial@11030000']['pinctrl-0'],
 'assessment':'Disabling FIQ removes the selected serial console path. UART1 exists as an enabled serial device but ordinary Rockchip console support is not compiled; UART2 is disabled. No ordinary UART console is established by this profile. UART2 DTS already references UART21 PB1/PB2, but enabling a usable console also requires config and bootarg review; physical wiring remains unknown.'}
assert 'CONFIG_SERIAL_ROCKCHIP=y' in config and '# CONFIG_SERIAL_ROCKCHIP_CONSOLE is not set' in config and 'CONFIG_CMDLINE=""' in config
(BASE/'monitor-dtb-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
