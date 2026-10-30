# Experimental SD product; does not identify or approve a physical board.
# The source template also lives below vendor/vortex/home in a BSP checkout.
# Register only the materialized device path, avoiding a duplicate product.
ifeq ($(LOCAL_DIR),device/vortex/vortex_rk322x_sd_box)
PRODUCT_MAKEFILES := $(LOCAL_DIR)/vortex_rk322x_sd_box.mk
endif
