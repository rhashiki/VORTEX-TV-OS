
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
__typeof__(((struct audio_stream*)0)->get_sample_rate) out_get_sample_rate = getter_rate;
__typeof__(((struct audio_stream*)0)->set_sample_rate) out_set_sample_rate;
__typeof__(((struct audio_stream*)0)->get_buffer_size) out_get_buffer_size;
__typeof__(((struct audio_stream*)0)->get_channels) out_get_channels = getter_channels;
__typeof__(((struct audio_stream*)0)->get_format) out_get_format = getter_format;
__typeof__(((struct audio_stream*)0)->set_format) out_set_format;
__typeof__(((struct audio_stream*)0)->standby) out_standby;
__typeof__(((struct audio_stream*)0)->dump) out_dump;
__typeof__(((struct audio_stream*)0)->set_parameters) out_set_parameters;
__typeof__(((struct audio_stream*)0)->get_parameters) out_get_parameters;
__typeof__(((struct audio_stream*)0)->add_audio_effect) out_add_audio_effect;
__typeof__(((struct audio_stream*)0)->remove_audio_effect) out_remove_audio_effect;
__typeof__(((struct audio_stream_out*)0)->get_latency) out_get_latency;
__typeof__(((struct audio_stream_out*)0)->set_volume) out_set_volume;
__typeof__(((struct audio_stream_out*)0)->write) out_write;
__typeof__(((struct audio_stream_out*)0)->get_render_position) out_get_render_position;
__typeof__(((struct audio_stream_out*)0)->get_next_write_timestamp) out_get_next_write_timestamp;
__typeof__(((struct audio_stream_out*)0)->get_presentation_position) out_get_presentation_position;

#define calloc test_calloc
#define free test_free
#define pthread_mutex_lock test_mutex_lock
#define pthread_mutex_unlock test_mutex_unlock
static int adev_open_output_stream(struct audio_hw_device *dev,
                                   audio_io_handle_t handle,
                                   audio_devices_t devices,
                                   audio_output_flags_t flags,
                                   struct audio_config *config,
                                   struct audio_stream_out **stream_out,
                                   const char *address __unused)
{
    struct audio_device *adev = (struct audio_device *)dev;
    struct stream_out *out;
    int ret;
    enum output_type type;

    ALOGD("audio hal adev_open_output_stream devices = 0x%x, flags = %d, samplerate = %d",
          devices, flags, config->sample_rate);
    out = (struct stream_out *)calloc(1, sizeof(struct stream_out));
    if (!out)
        return -ENOMEM;

    out->supported_channel_masks[0] = AUDIO_CHANNEL_OUT_STEREO;
    out->channel_mask = AUDIO_CHANNEL_OUT_STEREO;
    if (devices == AUDIO_DEVICE_NONE)
        devices = AUDIO_DEVICE_OUT_SPEAKER;
    out->device = devices;

    char value[PROPERTY_VALUE_MAX] = "";
    int device_mode = 0;
    if (flags & AUDIO_OUTPUT_FLAG_DIRECT) {
        property_get(MEDIA_AUDIO_DEVICE, value, "");
        if (atoi(value) == 8) {
            device_mode = SPDIF_PASSTHROUGH_MODE;
        } else if (atoi(value) == 6) {
            device_mode = HDMI_BITSTREAM_MODE;
        } else {
            device_mode = DEFAULT_MODE;
        }
        if ((devices & AUDIO_DEVICE_OUT_AUX_DIGITAL) && (device_mode == HDMI_BITSTREAM_MODE)) {
            property_get(MEDIA_CFG_AUDIO_BYPASS, value, "-1");
            if(memcmp(value, "true", 4) == 0) {
                out->channel_mask = config->channel_mask;
                if (isCurIEC958SamplerateSupport(config->sample_rate)) {
                    out->config = pcm_config_direct;
                    out->config.rate = config->sample_rate;
                    out->output_direct = true;
                    int channel = audio_channel_count_from_out_mask(config->channel_mask);

                    if (channel == 8 && config->sample_rate == 192000) {
                        out->output_direct_mode = HBR;
                    } else {
                        out->output_direct_mode = NLPCM;
                    }

                    if (channel == 8) {
                        out->config = pcm_config_direct;
                        out->config.rate = config->sample_rate;
                    } else if (config->sample_rate >= 176400) {
                        out->config.period_size = 1024 * 4;
                    } else {
                        out->config.period_size = 2048;
                    }
                    type = OUTPUT_HDMI_MULTI;
                } else {
                    out->config = pcm_config;
                    out->config.rate = 44100;
                    ALOGE("hdmi bitstream samplerate %d unsupport", config->sample_rate);
                }
                out->config.channels = audio_channel_count_from_out_mask(config->channel_mask);
                if (out->config.channels < 2)
                    out->config.channels = 2;
                out->pcm_device = PCM_DEVICE;
            } else {
                //property_get(MEDIA_CFG_AUDIO_MUL, value, "-1");
                if (config->sample_rate == 0)
                    config->sample_rate = HDMI_MULTI_DEFAULT_SAMPLING_RATE;
                if (config->channel_mask == 0)
                    config->channel_mask = AUDIO_CHANNEL_OUT_5POINT1;
                out->channel_mask = config->channel_mask;
                out->config = pcm_config_hdmi_multi;
                out->config.rate = config->sample_rate;
                out->config.channels = audio_channel_count_from_out_mask(config->channel_mask);
                out->pcm_device = PCM_DEVICE;
                out->output_direct = false;
                type = OUTPUT_HDMI_MULTI;
            }
        } else if ((devices & AUDIO_DEVICE_OUT_SPDIF) && (device_mode == SPDIF_PASSTHROUGH_MODE)) {
            out->channel_mask = config->channel_mask;
            out->config = pcm_config_direct;
            if ((config->sample_rate == 48000) ||
                    (config->sample_rate == 32000) ||
                    (config->sample_rate == 44100)) {
                out->config.rate = config->sample_rate;
                out->config.format = PCM_FORMAT_S16_LE;
                out->config.period_size = 2048;
            } else {
                out->config.rate = 44100;
                ALOGE("spdif passthrough samplerate %d is unsupport",config->sample_rate);
            }
            out->config.channels = audio_channel_count_from_out_mask(config->channel_mask);
            devices = AUDIO_DEVICE_OUT_SPDIF;
            out->pcm_device = PCM_DEVICE;
            out->output_direct = true;
            type = OUTPUT_HDMI_MULTI;
        } else {
            out->config = pcm_config;
            out->pcm_device = PCM_DEVICE;
            type = OUTPUT_LOW_LATENCY;
        }
    } else if (flags & AUDIO_OUTPUT_FLAG_DEEP_BUFFER) {
        out->config = pcm_config_deep;
        out->pcm_device = PCM_DEVICE_DEEP;
        type = OUTPUT_DEEP_BUF;
        out->output_direct_mode = LPCM;
    } else {
        out->config = pcm_config;
        out->pcm_device = PCM_DEVICE;
        type = OUTPUT_LOW_LATENCY;
        out->output_direct_mode = LPCM;
    }

    ALOGD("out->config.rate = %d, out->config.channels = %d", out->config.rate, out->config.channels);
    direct_mode.output_mode = HW_PARAMS_FLAG_LPCM;
    if ((type == OUTPUT_HDMI_MULTI) && (devices & AUDIO_DEVICE_OUT_AUX_DIGITAL) && (device_mode == HDMI_BITSTREAM_MODE)) {
        direct_mode.output_mode = HW_PARAMS_FLAG_NLPCM;
        out->config.format = PCM_FORMAT_S24_LE;
        setChanSta(out->config.rate, out->config.channels);
    } else {
        direct_mode.output_mode = HW_PARAMS_FLAG_LPCM;
        out->config.format = PCM_FORMAT_S16_LE;
    }

    out->stream.common.get_sample_rate = out_get_sample_rate;
    out->stream.common.set_sample_rate = out_set_sample_rate;
    out->stream.common.get_buffer_size = out_get_buffer_size;
    out->stream.common.get_channels = out_get_channels;
    out->stream.common.get_format = out_get_format;
    out->stream.common.set_format = out_set_format;
    out->stream.common.standby = out_standby;
    out->stream.common.dump = out_dump;
    out->stream.common.set_parameters = out_set_parameters;
    out->stream.common.get_parameters = out_get_parameters;
    out->stream.common.add_audio_effect = out_add_audio_effect;
    out->stream.common.remove_audio_effect = out_remove_audio_effect;
    out->stream.get_latency = out_get_latency;
    out->stream.set_volume = out_set_volume;
    out->stream.write = out_write;
    out->stream.get_render_position = out_get_render_position;
    out->stream.get_next_write_timestamp = out_get_next_write_timestamp;
    out->stream.get_presentation_position = out_get_presentation_position;

    out->dev = adev;
    out->dev->pre_output_device_id = OUT_DEVICE_SPEAKER;
    out->dev->pre_input_source_id = IN_SOURCE_MIC;

    config->format = out_get_format(&out->stream.common);
    config->channel_mask = out_get_channels(&out->stream.common);
    config->sample_rate = out_get_sample_rate(&out->stream.common);

    out->standby = true;
    out->nframes = 0;
    /* out->muted = false; by calloc() */
    /* out->written = 0; by calloc() */

    pthread_mutex_lock(&adev->lock_outputs);
    if (adev->outputs[type]) {
        pthread_mutex_unlock(&adev->lock_outputs);
        ret = -EBUSY;
        goto err_open;
    }
    adev->outputs[type] = out;
    pthread_mutex_unlock(&adev->lock_outputs);

    *stream_out = &out->stream;

    return 0;

err_open:
    free(out);
    *stream_out = NULL;
    return ret;
}

#undef calloc
#undef free
#undef pthread_mutex_lock
#undef pthread_mutex_unlock

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
