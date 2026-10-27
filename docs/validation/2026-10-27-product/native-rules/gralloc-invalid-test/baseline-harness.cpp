
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

constexpr int HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED = 34;
constexpr int HAL_PIXEL_FORMAT_YCrCb_420_SP = 17;
constexpr int HAL_PIXEL_FORMAT_YV12 = 842094169;
constexpr int HAL_PIXEL_FORMAT_YCrCb_NV12 = 21;
constexpr int HAL_PIXEL_FORMAT_YCrCb_NV12_10 = 23;
constexpr int HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO = 22;
constexpr int HAL_PIXEL_FORMAT_YCbCr_420_888 = 35;
constexpr int HAL_PIXEL_FORMAT_RGBA_8888 = 1;
constexpr int HAL_PIXEL_FORMAT_RGBX_8888 = 2;
constexpr int HAL_PIXEL_FORMAT_BGRA_8888 = 5;
constexpr int HAL_PIXEL_FORMAT_RGB_888 = 3;
constexpr int HAL_PIXEL_FORMAT_RGB_565 = 4;
constexpr int GRALLOC_USAGE_HW_VIDEO_ENCODER = 65536;
constexpr int GRALLOC_USAGE_HW_FB = 4096;
constexpr int GRALLOC_USAGE_EXTERNAL_DISP = 8192;
constexpr int GRALLOC_USAGE_PRIVATE_0 = 268435456;
constexpr int GRALLOC_USAGE_PRIVATE_1 = 536870912;

static int alloc_device_alloc(alloc_device_t *dev, int w, int h, int format, int usage, buffer_handle_t *pHandle, int *pStride)
{
	if (!pHandle || !pStride)
	{
		return -EINVAL;
	}

	size_t size;
	size_t stride;
	int changeFromat = -1;

	rockchip_log(1);

	if (format == HAL_PIXEL_FORMAT_IMPLEMENTATION_DEFINED)
	{
	    if (usage & GRALLOC_USAGE_HW_VIDEO_ENCODER )
	    {
	        format = HAL_PIXEL_FORMAT_YCrCb_NV12;
	    }
	    else
	    {
	        changeFromat = format;
	        format = HAL_PIXEL_FORMAT_RGBX_8888;
	    }
	}

	if (format == HAL_PIXEL_FORMAT_YCrCb_420_SP || format == HAL_PIXEL_FORMAT_YV12
	        /* HAL_PIXEL_FORMAT_YCbCr_420_SP, HAL_PIXEL_FORMAT_YCbCr_420_P, HAL_PIXEL_FORMAT_YCbCr_422_I are not defined in Android.
	         * To enable Mali DDK EGLImage support for those formats, firstly, you have to add them in Android system/core/include/system/graphics.h.
	         * Then, define SUPPORT_LEGACY_FORMAT in the same header file(Mali DDK will also check this definition).
	         */
#ifdef SUPPORT_LEGACY_FORMAT
	        || format == HAL_PIXEL_FORMAT_YCbCr_420_SP || format == HAL_PIXEL_FORMAT_YCbCr_420_P || format == HAL_PIXEL_FORMAT_YCbCr_422_I
#endif
		|| format == HAL_PIXEL_FORMAT_YCrCb_NV12 || format == HAL_PIXEL_FORMAT_YCrCb_NV12_10
		|| format == HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO || format == HAL_PIXEL_FORMAT_YCbCr_420_888
	   )
	{
		int align = 8;
		int bpp = 0;
		int bpr = 0;

		switch (format)
		{
			case HAL_PIXEL_FORMAT_YCrCb_420_SP:
			case HAL_PIXEL_FORMAT_YCbCr_420_888:
				stride = GRALLOC_ALIGN(w, 16);
				size = GRALLOC_ALIGN(h, 16) * (stride + GRALLOC_ALIGN(stride / 2, 16));
				break;

			case HAL_PIXEL_FORMAT_YV12:
#ifdef SUPPORT_LEGACY_FORMAT
			case HAL_PIXEL_FORMAT_YCbCr_420_P:
#endif
				stride = GRALLOC_ALIGN(w, 16);
				size = GRALLOC_ALIGN(h, 2) * (stride + GRALLOC_ALIGN(stride / 2, 16));

				break;
#ifdef SUPPORT_LEGACY_FORMAT

			case HAL_PIXEL_FORMAT_YCbCr_420_SP:
				stride = GRALLOC_ALIGN(w, 16);
				size = GRALLOC_ALIGN(h, 16) * (stride + GRALLOC_ALIGN(stride / 2, 16));
				break;

			case HAL_PIXEL_FORMAT_YCbCr_422_I:
				stride = GRALLOC_ALIGN(w, 16);
				size = h * stride * 2;

				break;
#endif
			case HAL_PIXEL_FORMAT_YCrCb_NV12:
				bpp = 2;
				bpr = (w * bpp + (align-1)) & (~(align-1));
				size = bpr * h;
				stride = bpr / bpp;
				break;
			case HAL_PIXEL_FORMAT_YCrCb_NV12_10:
				stride = w;
				size = stride * h * 2;
				break;
			case HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO:
				ALOGE("unsupport format [0x%x] now", HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO);
				break;

			default:
				return -EINVAL;
		}
	}
	else
	{
		int bpp = 0;

		switch (format)
		{
			case HAL_PIXEL_FORMAT_RGBA_8888:
			case HAL_PIXEL_FORMAT_RGBX_8888:
			case HAL_PIXEL_FORMAT_BGRA_8888:
				bpp = 4;
				break;

			case HAL_PIXEL_FORMAT_RGB_888:
				bpp = 3;
				break;

			case HAL_PIXEL_FORMAT_RGB_565:
#if PLATFORM_SDK_VERSION < 19
			case HAL_PIXEL_FORMAT_RGBA_5551:
			case HAL_PIXEL_FORMAT_RGBA_4444:
#endif
				bpp = 2;
				break;

			default:
				return -EINVAL;
		}

		size_t bpr = GRALLOC_ALIGN(w * bpp, 64);
		size = bpr * h;
		stride = bpr / bpp;
	}

	int err;

#ifndef MALI_600

	if ((usage & GRALLOC_USAGE_HW_FB) && !(usage & GRALLOC_USAGE_EXTERNAL_DISP))
	{
		err = gralloc_alloc_framebuffer(dev, size, usage, pHandle);
	}
	else
#endif

	{
		err = gralloc_alloc_buffer(dev, size, usage, pHandle);
	}

	if (err < 0)
	{
		return err;
	}

	/* match the framebuffer format */
	if ((usage & GRALLOC_USAGE_HW_FB) && !(usage & GRALLOC_USAGE_EXTERNAL_DISP))
	{
#ifdef GRALLOC_16_BITS
		format = HAL_PIXEL_FORMAT_RGB_565;
#else
		format = HAL_PIXEL_FORMAT_BGRA_8888;
#endif
	}

	private_handle_t *hnd = (private_handle_t *)*pHandle;
	int               private_usage = usage & (GRALLOC_USAGE_PRIVATE_0 |
	                                  GRALLOC_USAGE_PRIVATE_1);

	switch (private_usage)
	{
		case 0:
			hnd->yuv_info = MALI_YUV_BT601_NARROW;
			break;

		case GRALLOC_USAGE_PRIVATE_1:
			hnd->yuv_info = MALI_YUV_BT601_WIDE;
			break;

		case GRALLOC_USAGE_PRIVATE_0:
			hnd->yuv_info = MALI_YUV_BT709_NARROW;
			break;

		case (GRALLOC_USAGE_PRIVATE_0 | GRALLOC_USAGE_PRIVATE_1):
			hnd->yuv_info = MALI_YUV_BT709_WIDE;
			break;
	}

	hnd->width = w;
	hnd->height = h;
	hnd->format = changeFromat >= 0 ? changeFromat : format;
	hnd->stride = stride;

	*pStride = stride;

	if (rockchip_log(0))
		ALOGD("alloc [%d,%d,%d,%d]", w, h, hnd->format, hnd->share_fd);
	return 0;
}


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
