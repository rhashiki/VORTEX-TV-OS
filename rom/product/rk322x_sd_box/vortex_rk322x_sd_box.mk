# Input reference only. Does not generate a bootable SD image by itself.


# Use the platform base, without the vendor/common application auto-generator,
# stock launchers, optional GApps or the vendor all-files copy list.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_minimal.mk)
$(call inherit-product, vendor/vortex/home/rom/vortex_product.mk)
$(call inherit-product, frameworks/base/data/fonts/fonts.mk)
$(call inherit-product, external/roboto-fonts/fonts.mk)
$(call inherit-product, external/noto-fonts/fonts.mk)
$(call inherit-product, frameworks/native/build/phone-xhdpi-1024-dalvik-heap.mk)

# Reference has no setup wizard. These are real SettingsProvider defaults;
# resource compilation and fresh-device first boot are still unvalidated.
PRODUCT_PACKAGE_OVERLAYS += device/vortex/rk322x_sd_box/overlay

PRODUCT_NAME := vortex_rk322x_sd_box
PRODUCT_DEVICE := vortex_rk322x_sd_box
PRODUCT_BRAND := Vortex
PRODUCT_MANUFACTURER := Vortex
PRODUCT_MODEL := Vortex RK322x SD Reference
PRODUCT_CHARACTERISTICS := tv
PRODUCT_LOCALES := pt_BR en_US
PRODUCT_AAPT_CONFIG := normal tvdpi hdpi xhdpi
PRODUCT_AAPT_PREF_CONFIG := tvdpi

# Android system components required by Settings and the confirmed Installer
# and ACTION_OPEN_DOCUMENT flows; these do not add an application drawer.
PRODUCT_PACKAGES += \
    DefaultContainerService \
    Settings \
    SystemUI \
    InputDevices \
    LatinIME \
    DocumentsUI \
    ExternalStorageProvider \
    gralloc.rk30board \
    hwcomposer.rk30board \
    libion \
    audio.primary.rk30board \
    audio.usb.default \
    audio.r_submix.default \
    power.default

PRODUCT_DEFAULT_PROPERTY_OVERRIDES += \
    ro.board.platform=rk322x \
    ro.target.product=box \
    ro.enable_boot_charger_mode=0
PRODUCT_PROPERTY_OVERRIDES += \
    ro.rk.bt_enable=false \
    ro.opengles.version=131072

# Mount selector remains supplied by the actual kernel/bootloader. Do not set
# ro.bootmode or pretend a different boot medium is SD.
PRODUCT_COPY_FILES += \
    device/vortex/rk322x_sd_box/init.vortex-sd-reference.rc:root/init.rk30board.rc \
    device/rockchip/rk322x/fstab.rk30board.bootmode.sd:root/fstab.rk30board.bootmode.sd \
    device/vortex/rk322x_sd_box/audio_policy.vortex-sd-reference.conf:system/etc/audio_policy.conf \
    vendor/rockchip/rk322x/proprietary/lib/egl/libGLES_mali.so:system/lib/egl/libGLES_mali.so \
    vendor/rockchip/rk322x/proprietary/lib/egl/egl.cfg:system/lib/egl/egl.cfg
