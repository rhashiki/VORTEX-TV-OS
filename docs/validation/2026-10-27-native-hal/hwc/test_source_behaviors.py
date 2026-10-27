from pathlib import Path
import subprocess,json,hashlib
root=Path('/workspace/build01-hal-next/hwc');repo=root/'source'
out=root/'evidence/behavior';out.mkdir(parents=True,exist_ok=True)
def extract(content, signature):
 start=content.index(signature);brace=content.index('{',start);depth=0
 for i in range(brace,len(content)):
  if content[i]=='{':depth+=1
  if content[i]=='}':
   depth-=1
   if not depth:return content[start:i+1]
 raise ValueError(signature)
def run(label,patched):
 cpp=(repo/'rk_hwcomposer.cpp').read_text() if patched else subprocess.check_output(['git','show','HEAD:rk_hwcomposer.cpp'],cwd=repo).decode()
 tv=(repo/'TVInfo.cpp').read_text() if patched else subprocess.check_output(['git','show','HEAD:TVInfo.cpp'],cwd=repo).decode()
 policy=extract(cpp,'bool is_not_suit_mix_policy(')
 itoa=extract(tv,'static char *itoa(')
 headers='''#include <hardware/hwcomposer.h>
#include "gralloc_priv.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
'''
 body=r'''
int main() {
 int failures=0, checks=0;
 auto check=[&](const char* name,bool passed){ ++checks; if(!passed)++failures; std::printf("%s %s\n",passed?"PASS":"FAIL",name); };
 check("null-list-rejected",is_not_suit_mix_policy(NULL));
 hwc_display_contents_1_t *list=static_cast<hwc_display_contents_1_t*>(std::calloc(1,sizeof(hwc_display_contents_1_t)+sizeof(hwc_layer_1_t)));
 check("empty-list-rejected",is_not_suit_mix_policy(list));
 list->numHwLayers=1;
 check("null-handle-rejected",is_not_suit_mix_policy(list));
 private_handle_t handle(0,0,4096,NULL,0);
 list->hwLayers[0].handle=reinterpret_cast<buffer_handle_t>(&handle);
 struct PolicyCase { int format; bool reject; const char *name; };
 PolicyCase cases[]={
 {HAL_PIXEL_FORMAT_RGBA_8888,false,"RGBA-accepted"},
 {HAL_PIXEL_FORMAT_BGRA_8888,false,"BGRA-accepted"},
 {HAL_PIXEL_FORMAT_RGB_565,true,"RGB565-rejected"},
 {HAL_PIXEL_FORMAT_RGBX_8888,true,"RGBX-rejected"},
 {0,true,"format-zero-rejected"},
 {0x12345,true,"unknown-format-rejected"}};
 for(auto c:cases){ handle.format=c.format;check(c.name,is_not_suit_mix_policy(list)==c.reject); }
 std::free(list);
 struct StringCase { int value; const char *expected; };
 StringCase strings[]={{0,"0"},{1,"1"},{42,"42"},{1234,"1234"},{123456789,"123456789"}};
 for(auto c:strings){char buf[32];std::memset(buf,'#',sizeof(buf));buf[31]=0;char *returned=itoa(c.value,buf,10);check(c.expected,returned==buf&&std::strcmp(buf,c.expected)==0);}
 std::printf("TOTAL checks=%d failures=%d\n",checks,failures);
 return failures?1:0;
}
'''
 source=out/(label+'.cpp');source.write_text(headers+policy+'\n'+itoa+'\n'+body)
 compile=['g++','-std=gnu++11','-DANDROID','-I/workspace/build01-graphics-next/graphics/libhardware/include','-I/workspace/build01-platform-next/research/rockchip-system-core/include','-I/workspace/build01-platform-next/research/mali-legacy/gralloc-rk3328','-I'+str(root/'native-headers/opengl/include'),str(source),'-o',str(out/label)]
 r=subprocess.run(compile,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/(label+'.compile.log')).write_bytes(r.stdout)
 if r.returncode: print(r.stdout.decode());raise SystemExit('host compile failed')
 p=subprocess.run([str(out/label)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/(label+'.run.log')).write_bytes(p.stdout)
 print(label,p.returncode,p.stdout.decode())
 return {'label':label,'scope':'Host-only behavioral test of byte-extracted actual function bodies with genuine Android HAL/gralloc types; not Android runtime or hardware.', 'command':compile,'compile_exit_code':r.returncode,'run_exit_code':p.returncode,'function_hashes':{'policy':hashlib.sha256(policy.encode()).hexdigest(),'itoa':hashlib.sha256(itoa.encode()).hexdigest()},'source_file':source.name}
records=[run('before',False),run('after',True)]
(out/'behavior-results.json').write_text(json.dumps(records,indent=2)+'\n')
