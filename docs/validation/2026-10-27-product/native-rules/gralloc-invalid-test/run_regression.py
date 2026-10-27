#!/usr/bin/env python3
"""Execute actual extracted allocator function against host-only recording boundaries."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
DEFAULT_BASELINE=BASE/'source-copies-attempt01/libgralloc/alloc_device.cpp'
DEFAULT_PATCHED=BASE/'tree/hardware/rockchip/libgralloc/alloc_device.cpp'
GRAPHICS=BASE/'tree/system/core/include/system/graphics.h'
GRALLOC=BASE/'tree/hardware/libhardware/include/hardware/gralloc.h'
NAMES=['HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED','HAL_PIXEL_FORMAT_YCrCb_420_SP','HAL_PIXEL_FORMAT_YV12','HAL_PIXEL_FORMAT_YCrCb_NV12','HAL_PIXEL_FORMAT_YCrCb_NV12_10','HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO','HAL_PIXEL_FORMAT_YCbCr_420_888','HAL_PIXEL_FORMAT_RGBA_8888','HAL_PIXEL_FORMAT_RGBX_8888','HAL_PIXEL_FORMAT_BGRA_8888','HAL_PIXEL_FORMAT_RGB_888','HAL_PIXEL_FORMAT_RGB_565','GRALLOC_USAGE_HW_VIDEO_ENCODER','GRALLOC_USAGE_HW_FB','GRALLOC_USAGE_EXTERNAL_DISP','GRALLOC_USAGE_PRIVATE_0','GRALLOC_USAGE_PRIVATE_1']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def function(data):
 start=data.index('static int alloc_device_alloc(')
 end=data.index('\nstatic int alloc_device_free(',start)
 return data[start:end]
def constants():
 raw=GRAPHICS.read_text()+GRALLOC.read_text()
 result={}
 for name in NAMES:
  m=re.search(r'\b'+name+r'\s*=\s*(0x[0-9a-fA-F]+|[0-9]+)\s*[,;]',raw)
  if not m:raise ValueError('constant missing: '+name)
  result[name]=int(m[1],0)
 return result
PRELUDE=r'''
#include <cerrno>
#include <cstddef>
#include <cstdio>
#include <cstring>
#define PLATFORM_SDK_VERSION 25
#define GRALLOC_ALIGN(value,base) (((value)+((base)-1)) & ~((base)-1))
#define ALOGE(...) ((void)0)
#define ALOGD(...) ((void)0)
struct private_handle_t { int yuv_info, width, height, format; size_t stride; int share_fd; };
using buffer_handle_t = private_handle_t*;
struct alloc_device_t {};
enum { MALI_YUV_BT601_NARROW=1, MALI_YUV_BT601_WIDE=2, MALI_YUV_BT709_NARROW=3, MALI_YUV_BT709_WIDE=4 };
static int buffer_calls=0,fb_calls=0,stub_result=0;
static size_t captured_size=0;
static private_handle_t produced;
static int rockchip_log(int) {return 0;}
static int gralloc_alloc_buffer(alloc_device_t*,size_t size,int,buffer_handle_t* output) {
 ++buffer_calls;
 if(stub_result)return stub_result; // Baseline invalid path's undefined size is never inspected.
 captured_size=size;*output=&produced;return 0;
}
static int gralloc_alloc_framebuffer(alloc_device_t*,size_t size,int,buffer_handle_t* output) {
 ++fb_calls;
 if(stub_result)return stub_result;
 captured_size=size;*output=&produced;return 0;
}
'''
TESTS=r'''
static int failed=0,passed=0;
static void emit(const char* name,bool ok,int ret) {
 printf("%s %s ret=%d buffer_calls=%d fb_calls=%d\n",ok?"PASS":"FAIL",name,ret,buffer_calls,fb_calls);
 if(ok)++passed;else ++failed;
}
static void reset() {buffer_calls=fb_calls=0;stub_result=0;captured_size=0;produced={};}
static void rejected(const char*name,int format,int usage,bool null_handle=false,bool null_stride=false) {
 reset();stub_result=-EIO;
 private_handle_t sentinel={};buffer_handle_t handle=&sentinel;int stride=117;
 int ret=alloc_device_alloc(nullptr,18,3,format,usage,null_handle?nullptr:&handle,null_stride?nullptr:&stride);
 emit(name,ret==-EINVAL && buffer_calls==0 && fb_calls==0 && handle==&sentinel && stride==117,ret);
}
static void accepted(const char* name,int w,int h,int format,int usage,size_t size,int stride,int final_format,bool fb=false) {
 reset();buffer_handle_t handle=nullptr;int actual_stride=-1;
 int ret=alloc_device_alloc(nullptr,w,h,format,usage,&handle,&actual_stride);
 bool ok=ret==0 && buffer_calls==(fb?0:1) && fb_calls==(fb?1:0) && captured_size==size && actual_stride==stride && handle==&produced && produced.width==w && produced.height==h && produced.format==final_format && produced.stride==static_cast<size_t>(stride) && produced.yuv_info==MALI_YUV_BT601_NARROW;
 emit(name,ok,ret);
}
int main() {
 rejected("unsupported-NV12-video-buffer",HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO,0);
 rejected("unsupported-NV12-video-framebuffer",HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO,GRALLOC_USAGE_HW_FB);
 rejected("unsupported-NV12-video-external",HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO,GRALLOC_USAGE_HW_FB|GRALLOC_USAGE_EXTERNAL_DISP);
 rejected("unknown-format",0x7fffffff,0);
 rejected("null-output-handle",HAL_PIXEL_FORMAT_RGBA_8888,0,true,false);
 rejected("null-output-stride",HAL_PIXEL_FORMAT_RGBA_8888,0,false,true);
 accepted("RGBA-buffer",640,480,HAL_PIXEL_FORMAT_RGBA_8888,0,1228800,640,HAL_PIXEL_FORMAT_RGBA_8888);
 accepted("RGB888-row-alignment",17,2,HAL_PIXEL_FORMAT_RGB_888,0,128,21,HAL_PIXEL_FORMAT_RGB_888);
 accepted("NV12-neighbor",18,2,HAL_PIXEL_FORMAT_YCrCb_NV12,0,80,20,HAL_PIXEL_FORMAT_YCrCb_NV12);
 accepted("NV12-10-neighbor",18,3,HAL_PIXEL_FORMAT_YCrCb_NV12_10,0,108,18,HAL_PIXEL_FORMAT_YCrCb_NV12_10);
 accepted("YV12-row-height-alignment",18,3,HAL_PIXEL_FORMAT_YV12,0,192,32,HAL_PIXEL_FORMAT_YV12);
 accepted("RGBA-framebuffer-route",640,480,HAL_PIXEL_FORMAT_RGBA_8888,GRALLOC_USAGE_HW_FB,1228800,640,HAL_PIXEL_FORMAT_BGRA_8888,true);
 accepted("implementation-defined-RGBX",18,2,HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED,0,256,32,HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED);
 accepted("implementation-defined-encoder-NV12",18,2,HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED,GRALLOC_USAGE_HW_VIDEO_ENCODER,80,20,HAL_PIXEL_FORMAT_YCrCb_NV12);
 printf("RESULT passed=%d failed=%d\n",passed,failed);
 return failed?1:0;
}
'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,default=DEFAULT_BASELINE);ap.add_argument('--patched',type=Path,default=DEFAULT_PATCHED);args=ap.parse_args()
 baseline_function=function(args.baseline.read_text())
 patched_function=function(args.patched.read_text())
 old='ALOGE("unsupport format [0x%x] now", HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO);\n\t\t\t\tbreak;'
 new=old.rsplit('break;',1)[0]+'return -EINVAL;'
 if baseline_function.count(old)!=1 or baseline_function.replace(old,new)!=patched_function:
  raise ValueError('Source delta must be exactly the reviewed unsupported-format rejection')
 values=constants();defs='\n'.join(f'constexpr int {name} = {value};' for name,value in values.items())+'\n'
 report={'scope':'Host-only function-boundary regression executing the exact extracted alloc_device_alloc function with recording allocation/log/type fixtures. No real Android HAL loading, GPU, allocation, rendering, or physical-board validation. Stub/type shape differs from full Android ABI and size_t is host-native.','constants':values,'header_sources':[{'path':str(p),'sha256':digest(p)} for p in [GRAPHICS,GRALLOC]],'checks':[]}
 for label,path in [('baseline',args.baseline),('patched',args.patched)]:
  original=path.read_text();extracted=function(original)
  (ROOT/f'{label}-alloc-function.cpp.txt').write_text(extracted)
  harness=ROOT/f'{label}-harness.cpp';harness.write_text(PRELUDE+'\n'+defs+'\n'+extracted+'\n'+TESTS)
  executable=ROOT/f'{label}-test';cmd=['g++','-std=c++11','-O0','-Wall','-Wextra',str(harness),'-o',str(executable)]
  p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(ROOT/f'{label}-compile.log').write_bytes(p.stdout)
  if p.returncode:raise RuntimeError(f'{label} compile failed: {p.stdout.decode()}')
  p=subprocess.run([str(executable)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(ROOT/f'{label}-runtime.log').write_bytes(p.stdout)
  output=p.stdout.decode();print(label,p.returncode,output)
  passed=len(re.findall(r'^PASS ',output,re.M));failed=len(re.findall(r'^FAIL ',output,re.M))
  expected=(label=='baseline' and p.returncode==1 and passed==11 and failed==3) or (label=='patched' and p.returncode==0 and passed==14 and failed==0)
  report['checks'].append({'label':label,'source':str(path),'source_sha256':digest(path),'extracted_function_sha256':hashlib.sha256(extracted.encode()).hexdigest(),'compile_command':cmd,'exit_code':p.returncode,'passed':passed,'failed':failed,'expected_result_met':expected,'runtime_log':f'{label}-runtime.log','compile_log':f'{label}-compile.log'})
 report['status']='pass' if all(x['expected_result_met'] for x in report['checks']) else 'fail'
 (ROOT/'regression-result.json').write_text(json.dumps(report,indent=2)+'\n')
 return 0 if report['status']=='pass' else 1
if __name__=='__main__':sys.exit(main())
