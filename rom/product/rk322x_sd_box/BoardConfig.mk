# Generic source candidate only; not a R329Q_V8.0 board identification.
include device/rockchip/rk322x/BoardConfig.mk

TARGET_BOARD_PLATFORM_PRODUCT := box
TARGET_NO_RECOVERY := true
TARGET_RELEASETOOLS_EXTENSIONS :=
TARGET_ROCHCHIP_RECOVERY := false
TARGET_ROCKCHIP_PCBATEST := false
RECOVERY_AUTO_USB_UPDATE := false
BUILD_WITH_DRMSERVICE := false
ENABLE_KEYBOX_PROVISION := false
BOARD_HAVE_BLUETOOTH := false
BLUETOOTH_USE_BPLUS := false
BOARD_HAVE_BLUETOOTH_BCM := false
BUILD_WITH_GOOGLE_MARKET := false
BUILD_BOX_WITH_GOOGLE_MARKET := false
BUILD_WITH_GOOGLE_MARKET_ALL := false
BUILD_WITH_GOOGLE_FRP := false
BOARD_WITH_MEM_OPTIMISE := false
BOARD_USE_LOW_MEM := true

# The common BoardConfig defaults to ap6xxx. No Wi-Fi chip/firmware has been
# identified for this unit; do not retain that default as an asserted match.
BOARD_CONNECTIVITY_VENDOR :=
BOARD_CONNECTIVITY_MODULE :=
BOARD_WLAN_DEVICE :=
BOARD_WPA_SUPPLICANT_PRIVATE_LIB :=
BOARD_HOSTAPD_PRIVATE_LIB :=
WIFI_DRIVER_FW_PATH_PARAM :=
WIFI_DRIVER_FW_PATH_STA :=
WIFI_DRIVER_FW_PATH_P2P :=
WIFI_DRIVER_FW_PATH_AP :=

# A caller may supply an explicitly reviewed Image; otherwise keep the
# candidate path and let the real image build report a missing kernel.
ifneq ($(strip $(VORTEX_REFERENCE_KERNEL_IMAGE)),)
TARGET_PREBUILT_KERNEL := $(VORTEX_REFERENCE_KERNEL_IMAGE)
endif
