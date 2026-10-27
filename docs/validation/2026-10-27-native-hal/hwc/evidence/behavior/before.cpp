#include <hardware/hwcomposer.h>
#include "gralloc_priv.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
bool is_not_suit_mix_policy(hwc_display_contents_1_t *list)
{
    struct private_handle_t * handle = NULL;
    hwc_layer_1_t * layer = NULL;

    if (!list)
        return true;

    if (list->numHwLayers <= 0)
        return true;

    layer = &list->hwLayers[list->numHwLayers - 1];
    if (layer)
        handle = (struct private_handle_t *)layer->handle;

    switch (handle && handle->format) {
        case HAL_PIXEL_FORMAT_RGBA_8888:
        case HAL_PIXEL_FORMAT_BGRA_8888:
            return false;
        default:
            break;
    }

    return true;
}
static char *itoa(int val, char *buf, unsigned radix)
{
	char   *p;             
	char   *firstdig;      
	char	temp;           
	unsigned   digval;

	p = buf;
	if(val <0) {
		*p++ = '-';
		val = (unsigned long)(-(long)val);
	}
	firstdig = p; 
	do {
	digval = (unsigned)(val % radix);
	val /= radix;

	if (digval > 9)
	    *p++ = (char)(digval - 10 + 'a'); 
	else
	    *p++ = (char)(digval + '0');      
	} while(val > 0);

	*p-- = '\0 ';
	do {
		temp = *p;
		*p = *firstdig;
		*firstdig = temp;
		--p;
		++firstdig;        
	} while(firstdig < p);
	return buf;
}

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
