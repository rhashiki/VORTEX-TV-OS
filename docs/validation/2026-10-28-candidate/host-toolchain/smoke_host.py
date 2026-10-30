from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parent
TOOL=ROOT/'tree/prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8'
SMOKE=ROOT/'smoke';SMOKE.mkdir(exist_ok=True)
CLANG=Path('/workspace/build01-full-next/platform/tree/prebuilts/clang/host/linux-x86/clang-2690385/bin/clang++')
CXX=Path('/workspace/build01-full-next/platform/tree/external/libcxx/include')
ABI=Path('/workspace/build01-full-next/platform/tree/external/libcxxabi/include')
ENV=os.environ.copy();ENV['LD_LIBRARY_PATH']='/workspace/build01-product-next/native-rules/acquisition/clang-tools/host-compat/lib/x86_64-linux-gnu'
(SMOKE/'stdlib_features.c').write_text('#include <features.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <stdint.h>\nint main(void) { void *p=malloc(32); if (!p) return 4; free(p); printf("glibc_headers=%d.%d malloc_ok=1\\n", __GLIBC__, __GLIBC_MINOR__); return 0; }\n')
(SMOKE/'libcxx_headers.cpp').write_text('#include <features.h>\n#include <cstdlib>\n#include <atomic>\n#include <cstdio>\nstatic_assert(__GLIBC__ == 2 && __GLIBC_MINOR__ == 15, "Wrong host sysroot");\nint test_host_headers() { std::atomic<int> x(7); return x.load() + (std::malloc(0)==nullptr); }\n')
results=[]
def run(label,cmd,expected=0):
 p=subprocess.run([str(x) for x in cmd],env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (ROOT/'evidence'/(label+'.log')).write_text(p.stdout)
 results.append({'case':label,'command':[str(x) for x in cmd],'exit_code':p.returncode,'expected_exit_code':expected,'status':'pass' if p.returncode==expected else 'failed'})
 return p.returncode==expected
run('gcc-version',[TOOL/'bin/x86_64-linux-gcc','--version'])
ok=run('gcc-stdlib-features-compile',[TOOL/'bin/x86_64-linux-gcc','--sysroot='+str(TOOL/'sysroot'),'-m64','-std=c11','-Wall','-Wextra','-Werror',SMOKE/'stdlib_features.c','-o',SMOKE/'stdlib_features'])
if ok:run('gcc-stdlib-features-runtime',[SMOKE/'stdlib_features'])
run('clang-real-libcxx-headers-compile',[CLANG,'--gcc-toolchain='+str(TOOL),'--sysroot='+str(TOOL/'sysroot'),'-target','x86_64-linux-gnu','-m64','-std=c++14','-nostdinc++','-I',CXX,'-I',ABI,'-Wall','-Wextra','-Werror','-c',SMOKE/'libcxx_headers.cpp','-o',SMOKE/'libcxx_headers.o'])
run('host-test-elf',['readelf','-h','-l','-d',SMOKE/'stdlib_features'])
result={'scope':'host compiler/sysroot/header smoke only; not a full Android build or target/hardware test','status':'pass' if all(x['status']=='pass' for x in results) else 'failed','cases':results,'outputs':[]}
for name in ['stdlib_features','libcxx_headers.o']:
 p=SMOKE/name
 if p.exists():result['outputs'].append({'path':str(p),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'evidence/host-smoke-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
