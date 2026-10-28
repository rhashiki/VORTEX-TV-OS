# AOSP 7.1.2 Rockchip RK322x product overlay FRAGMENT, not a firmware image.
# In a verified AOSP product: $(call inherit-product, vendor/vortex/home/rom/vortex_product.mk)
# Separate system packages: launcher remains os.vortex.tv,
# native streaming app uses os.vortex.tv.stream (never the same applicationId).
# Both are required; a missing VortexTV.apk must break the firmware build
# rather than silently shipping without the native streaming app.
PRODUCT_PACKAGES += VortexHome VortexTV
# OEM-provisioned catalog access. File stays outside Git; users never type a code.
# Its contents are never written to logcat or to the APK asset directory.
PRODUCT_COPY_FILES += vendor/vortex/home/rom/prebuilt/catalog-access:system/etc/vortex-tv/catalog-access
PRODUCT_PROPERTY_OVERRIDES += ro.config.low_ram=true
# Do not overwrite DDR loader, kernel, DTB, trust or NAND drivers with unverified images.
