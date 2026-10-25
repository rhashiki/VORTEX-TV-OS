# AOSP 7.1.2 Rockchip RK322x product overlay FRAGMENT, not a firmware image.
# In a verified AOSP product: $(call inherit-product, vendor/vortex/home/rom/vortex_product.mk)
PRODUCT_PACKAGES += VortexHome
PRODUCT_PROPERTY_OVERRIDES += ro.config.low_ram=true
# Do not overwrite DDR loader, kernel, DTB, trust or NAND drivers with unverified images.
