#!/usr/bin/env python3
"""Host boundary regression of actual source function with recorded hardware boundaries."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parent
STAGE=ROOT.parent
TREE=STAGE/'tree'
BASE=STAGE/'baseline/audio_hw.c'
PATCHED=TREE/'hardware/rockchip/audio/tinyalsa_hal/audio_hw.c'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(p):
 s=p.read_text();start=s.index('static int adev_open_output_stream(');end=s.index('\n/**',start);return s[start:end]
PRELUDE=r'''
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <pthread.h>
#include <hardware/audio.h>
#include <tinyalsa/asoundlib.h>
#define PROPERTY_VALUE_MAX 92
#define ALOGD(...) ((void)0)
#define ALOGE(...) ((void)0)
#define HDMI_MULTI_DEFAULT_SAMPLING_RATE 44100
#define HW_PARAMS_FLAG_LPCM 0
#define HW_PARAMS_FLAG_NLPCM 1
#define DEFAULT_MODE 0
#define HDMI_BITSTREAM_MODE 6
#define SPDIF_PASSTHROUGH_MODE 8
#define MEDIA_AUDIO_DEVICE "persist.audio.currentplayback"
#define MEDIA_CFG_AUDIO_BYPASS "media.cfg.audio.bypass"
#define PCM_DEVICE 0
#define PCM_DEVICE_DEEP 3
#define OUT_DEVICE_SPEAKER 0
#define IN_SOURCE_MIC 0
#define LPCM 0
#define NLPCM 1
#define HBR 2
enum output_type { OUTPUT_DEEP_BUF, OUTPUT_LOW_LATENCY, OUTPUT_HDMI_MULTI, OUTPUT_DIRECT, OUTPUT_TOTAL };
struct stream_out;
struct audio_device { struct audio_hw_device hw_device; struct stream_out *outputs[OUTPUT_TOTAL]; pthread_mutex_t lock_outputs; int pre_output_device_id,pre_input_source_id; };
struct stream_out { struct audio_stream_out stream; struct audio_device *dev; audio_channel_mask_t supported_channel_masks[2],channel_mask; audio_devices_t device; struct pcm_config config; int pcm_device,output_direct_mode; bool output_direct,standby; uint64_t nframes; };
struct { int output_mode; } direct_mode;
static struct pcm_config pcm_config={.channels=2,.rate=44100,.period_size=1024,.period_count=4,.format=PCM_FORMAT_S16_LE};
static struct pcm_config pcm_config_direct={.channels=2,.rate=48000,.period_size=2048,.period_count=4,.format=PCM_FORMAT_S24_LE};
static struct pcm_config pcm_config_hdmi_multi={.channels=6,.rate=44100,.period_size=1024,.period_count=4,.format=PCM_FORMAT_S16_LE};
static struct pcm_config pcm_config_deep={.channels=2,.rate=44100,.period_size=4096,.period_count=4,.format=PCM_FORMAT_S16_LE};
static const char *device_property="6",*bypass_property="true";
static int support_rate=1,allocation_fail=0,allocated=0,freed=0,lock_calls=0,channel_status_calls=0;
static void *test_calloc(size_t n,size_t size) {if(allocation_fail)return NULL;++allocated;return calloc(n,size);}
static void test_free(void *p) {if(p)++freed;free(p);}
static int test_mutex_lock(pthread_mutex_t *p) {(void)p;++lock_calls;return 0;}
static int test_mutex_unlock(pthread_mutex_t *p) {(void)p;return 0;}
static int property_get(const char *key,char *value,const char *def) {const char *s=def;if(!strcmp(key,MEDIA_AUDIO_DEVICE))s=device_property;else if(!strcmp(key,MEDIA_CFG_AUDIO_BYPASS))s=bypass_property;strcpy(value,s);return strlen(s);}
static int isCurIEC958SamplerateSupport(unsigned rate) {(void)rate;return support_rate;}
static void setChanSta(unsigned rate,unsigned channels) {(void)rate;(void)channels;++channel_status_calls;}
static uint32_t getter_rate(const struct audio_stream *s) {return ((const struct stream_out*)s)->config.rate;}
static audio_format_t getter_format(const struct audio_stream *s) {(void)s;return AUDIO_FORMAT_PCM_16_BIT;}
static audio_channel_mask_t getter_channels(const struct audio_stream *s) {return ((const struct stream_out*)s)->channel_mask;}
'''
TEST=r'''
static int passed=0,failed=0;
static void reset(void) {device_property="6";bypass_property="true";support_rate=1;allocation_fail=allocated=freed=lock_calls=channel_status_calls=0;direct_mode.output_mode=0;}
static void emit(const char *name,int ok,int result) {printf("%s %s rc=%d alloc=%d free=%d locks=%d chansta=%d\n",ok?"PASS":"FAIL",name,result,allocated,freed,lock_calls,channel_status_calls);if(ok)++passed;else ++failed;}
static void run_case(const char *name,audio_devices_t devices,audio_output_flags_t flags,unsigned rate,audio_channel_mask_t mask,int mode,int bypass,int supported,int busy,int failalloc,int expected,int slot,int expected_rate,int expected_direct_mode) {
 reset();device_property=mode==8?"8":mode==6?"6":"0";bypass_property=bypass?"true":"false";support_rate=supported;allocation_fail=failalloc;
 struct audio_device device={0};struct stream_out previous={0};if(busy)device.outputs[OUTPUT_HDMI_MULTI]=&previous;
 struct audio_config config={.sample_rate=rate,.channel_mask=mask,.format=AUDIO_FORMAT_PCM_16_BIT};struct audio_config original=config;
 struct audio_stream_out *published=NULL;
 int rc=adev_open_output_stream(&device.hw_device,0,devices,flags,&config,&published,"");
 int ok=rc==expected;
 if(expected==0) {
  struct stream_out *out=(struct stream_out*)published;ok=ok&&out&&device.outputs[slot]==out&&config.sample_rate==(unsigned)expected_rate&&out->output_direct_mode==expected_direct_mode&&allocated==1&&freed==0;
  if(out)test_free(out);
 } else {
  ok=ok&&published==NULL&&allocated==freed;
  if(expected==-EINVAL) {ok=ok&&!memcmp(&config,&original,sizeof(config))&&lock_calls==0&&channel_status_calls==0;for(int i=0;i<OUTPUT_TOTAL;++i)ok=ok&&device.outputs[i]==NULL;}
  if(busy)ok=ok&&device.outputs[OUTPUT_HDMI_MULTI]==&previous;
 }
 emit(name,ok,rc);
 if(rc==0&&expected!=0&&published)test_free(published);
}
int main(void) {
 run_case("unsupported-HDMI-bypass-rate",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,12345,AUDIO_CHANNEL_OUT_STEREO,6,1,0,0,0,-EINVAL,0,0,0);
 run_case("supported-HDMI-NLPCM",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,48000,AUDIO_CHANNEL_OUT_STEREO,6,1,1,0,0,0,OUTPUT_HDMI_MULTI,48000,NLPCM);
 run_case("supported-HDMI-HBR",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,192000,AUDIO_CHANNEL_OUT_7POINT1,6,1,1,0,0,0,OUTPUT_HDMI_MULTI,192000,HBR);
 run_case("HDMI-no-bypass-defaults",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,0,0,6,0,1,0,0,0,OUTPUT_HDMI_MULTI,44100,LPCM);
 run_case("SPDIF-supported-rate",AUDIO_DEVICE_OUT_SPDIF,AUDIO_OUTPUT_FLAG_DIRECT,32000,AUDIO_CHANNEL_OUT_STEREO,8,0,1,0,0,0,OUTPUT_HDMI_MULTI,32000,LPCM);
 run_case("SPDIF-existing-rate-fallback",AUDIO_DEVICE_OUT_SPDIF,AUDIO_OUTPUT_FLAG_DIRECT,96000,AUDIO_CHANNEL_OUT_STEREO,8,0,1,0,0,0,OUTPUT_HDMI_MULTI,44100,LPCM);
 run_case("direct-without-passthrough-mode",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,48000,AUDIO_CHANNEL_OUT_STEREO,0,0,1,0,0,0,OUTPUT_LOW_LATENCY,44100,LPCM);
 run_case("deep-buffer",AUDIO_DEVICE_OUT_SPEAKER,AUDIO_OUTPUT_FLAG_DEEP_BUFFER,44100,AUDIO_CHANNEL_OUT_STEREO,0,0,1,0,0,0,OUTPUT_DEEP_BUF,44100,LPCM);
 run_case("default-speaker",AUDIO_DEVICE_NONE,0,44100,AUDIO_CHANNEL_OUT_STEREO,0,0,1,0,0,0,OUTPUT_LOW_LATENCY,44100,LPCM);
 run_case("busy-HDMI-slot",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,48000,AUDIO_CHANNEL_OUT_STEREO,6,1,1,1,0,-EBUSY,0,0,0);
 run_case("allocation-failure",AUDIO_DEVICE_OUT_AUX_DIGITAL,AUDIO_OUTPUT_FLAG_DIRECT,48000,AUDIO_CHANNEL_OUT_STEREO,6,1,1,0,1,-ENOMEM,0,0,0);
 printf("RESULT passed=%d failed=%d\n",passed,failed);return failed?1:0;
}
'''
def run():
 body=extract(PATCHED)
 declarations=[]
 special={'out_get_sample_rate':'getter_rate','out_get_format':'getter_format','out_get_channels':'getter_channels'}
 for common,field,name in re.findall(r'out->stream\.(common\.)?(\w+)\s*=\s*(\w+);',body):
  owner='struct audio_stream' if common else 'struct audio_stream_out'
  declarations.append('__typeof__(((%s*)0)->%s) %s%s;\n'%(owner,field,name,' = '+special[name] if name in special else ''))
 results=[]
 for label,p in [('baseline',BASE),('patched',PATCHED)]:
  fn=extract(p);(ROOT/(label+'-function.c.txt')).write_text(fn)
  text=PRELUDE+''.join(declarations)+'\n#define calloc test_calloc\n#define free test_free\n#define pthread_mutex_lock test_mutex_lock\n#define pthread_mutex_unlock test_mutex_unlock\n'+fn+'\n#undef calloc\n#undef free\n#undef pthread_mutex_lock\n#undef pthread_mutex_unlock\n'+TEST
  source=ROOT/(label+'-harness.c');source.write_text(text)
  cmd=['cc','-std=gnu99','-O0','-Wall','-Wextra','-ftrivial-auto-var-init=zero','-D__unused=__attribute__((unused))','-I'+str(TREE/'hardware/libhardware/include'),'-I'+str(TREE/'system/media/audio/include'),'-I'+str(TREE/'system/core/include'),'-I'+str(TREE/'external/tinyalsa/include'),str(source),'-o',str(ROOT/(label+'-test'))]
  c=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(ROOT/(label+'-compile.log')).write_bytes(c.stdout)
  if c.returncode:print(c.stdout.decode());raise SystemExit(c.returncode)
  r=subprocess.run([str(ROOT/(label+'-test'))],stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(ROOT/(label+'-runtime.log')).write_bytes(r.stdout);print(label,r.stdout.decode())
  m=re.search(rb'RESULT passed=(\d+) failed=(\d+)',r.stdout);expected=(10,1) if label=='baseline' else (11,0);actual=tuple(map(int,m.groups())) if m else None;assert actual==expected,(label,actual)
  results.append({'label':label,'source':str(p),'source_sha256':digest(p),'function_sha256':hashlib.sha256(fn.encode()).hexdigest(),'compiler_command':cmd,'exit_code':r.returncode,'passed':actual[0],'failed':actual[1],'expected_result_met':True})
 report={'scope':'host function-boundary regression using actual extracted function, real public Android/tinyalsa header types, simplified private stream/device layouts and recording property/rate/channel-status/lock/allocation boundaries; no device IO or real Android ABI validation','baseline_instrumentation':'GCC14 -ftrivial-auto-var-init=zero initializes otherwise uninitialized enum to safe zero for deterministic baseline rejection test; not a sanitizer finding or prediction of uninstrumented UB behavior','checks':results,'status':'pass'}
 (ROOT/'regression-result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':run()
