from pathlib import Path
root=Path('/workspace/build01-hal-next/hwc-format/source')
replacements={
'rk_hwcomposer.cpp':[
(b'ALOGD("line=%d,scale over[%d,%d]",__LINE__,hfactor,vfactor);',b'ALOGD("line=%d,scale over[%f,%f]",__LINE__,hfactor,vfactor);',1),
(b'ALOGD("layer[%d],name=%s,hanlde=%x,tra=%d,flag=%d",i,layer->LayerName,handle,layer->transform,layer->flags);',b'ALOGD("layer[%d],name=%s,hanlde=%p,tra=%d,flag=%d",i,layer->LayerName,(void *)handle,layer->transform,layer->flags);',1),
(b'ALOGD("layer[%d],fmt=%d,usage=%x,protect=%x",i,handle->format,handle->usage,GRALLOC_USAGE_PROTECTED);',b'ALOGD("layer[%d],fmt=%d,usage=%x,protect=%llx",i,handle->format,handle->usage,(unsigned long long)GRALLOC_USAGE_PROTECTED);',1),
(b'ALOGD("rga policy skip,flag=%x,hanlde=%x",layer->flags,handle);',b'ALOGD("rga policy skip,flag=%x,hanlde=%p",layer->flags,(void *)handle);',1),
(b'ALOGD("policy skip,flag=%x,hanlde=%x,line=%d,name=%s",layer->flags,handle,__LINE__,layer->LayerName);',b'ALOGD("policy skip,flag=%x,hanlde=%p,line=%d,name=%s",layer->flags,(void *)handle,__LINE__,layer->LayerName);',2),
(b'ALOGD("line=%d,handle=%d",__LINE__,handle);',b'ALOGD("line=%d,handle=%p",__LINE__,(void *)handle);',2),
(b'ALOGD("policy skip,flag=%x,hanlde=%x,line=%d",layer->flags,handle,__LINE__);',b'ALOGD("policy skip,flag=%x,hanlde=%p,line=%d",layer->flags,(void *)handle,__LINE__);',1),
(b'ALOGD("policy skip,flag=%x,hanlde=%x,tra=%d,num=%d,line=%d",\n                    layer->flags,handle,layer->transform,list->numHwLayers,__LINE__);',b'ALOGD("policy skip,flag=%x,hanlde=%p,tra=%d,num=%d,line=%d",\n                    layer->flags,(void *)handle,layer->transform,list->numHwLayers,__LINE__);',1),
(b'ALOGD("vop_gpu skip,flag=%x,hanlde=%x",layer->flags);',b'ALOGD("vop_gpu skip,flag=%x,hanlde=%p",layer->flags,(void *)handle);',1),
(b'ALOGV("fbLyaer = %x,num=%d",fbLayer,list->numHwLayers);',b'ALOGV("fbLyaer = %p,num=%d",(void *)fbLayer,list->numHwLayers);',1),
],
'rk_hwcomposer_blit.cpp':[
(b'srcLogical=%x,srcFormat=%d',b'srcLogical=%p,srcFormat=%d',2),
(b'dstLogical=%x,dstPhysical=%x,dstFormat=%d',b'dstLogical=%p,dstPhysical=%x,dstFormat=%d',2),
],
'hwc_rga.cpp':[
(b'src_addr=0x%x,dst rect[%d,%d,%d,%d],dst_addr=0x%x',b'src_addr=%p,dst rect[%d,%d,%d,%d],dst_addr=%p',1),
],
'rk_hwc_com.cpp':[
(b'video info phy_addr=%p,w=%d,h=%d',b'video info phy_addr=0x%x,w=%d,h=%d',1),
]}
for name,rows in replacements.items():
 p=root/name;b=p.read_bytes()
 for old,new,count in rows:
  assert b.count(old)==count,(name,old,b.count(old),count)
  b=b.replace(old,new)
 p.write_bytes(b)
print('Changed',len(replacements),'source files by byte-preserving replacements')
