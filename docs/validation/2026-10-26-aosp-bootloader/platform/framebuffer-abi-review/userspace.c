/* Isolated ARM layout measurement of verbatim declarations; not a HAL or kernel build. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define RK30_MAX_LAYER_SUPPORT 5

#define RK_WIN_MAX_AREA 4

#define RK_MAX_BUF_NUM 11

struct rk_lcdc_post_cfg{
	u32 xpos;
	u32 ypos;
	u32 xsize;
	u32 ysize;
};

struct rk_fb_area_par {
	u8  data_format;        /*layer data fmt*/
	short ion_fd;
	unsigned int phy_addr;
	short acq_fence_fd;
	u16  x_offset;
	u16  y_offset;
	u16 xpos;		/*start point in panel  --->LCDC_WINx_DSP_ST*/
	u16 ypos;
	u16 xsize;		/* display window width/height  -->LCDC_WINx_DSP_INFO*/
	u16 ysize;
	u16 xact;		/*origin display window size -->LCDC_WINx_ACT_INFO*/
	u16 yact;
	u16 xvir;		/*virtual width/height     -->LCDC_WINx_VIR*/
	u16 yvir;
	u8  fbdc_en;
	u8  fbdc_cor_en;
	u8  fbdc_data_format;
	u16 data_space;
	u32 reserved0;
};

struct rk_fb_win_par {
	u8  win_id;
	u8  z_order;		/*win sel layer*/
	u8  alpha_mode;
	u16 g_alpha_val;
	u8  mirror_en;
	struct rk_fb_area_par area_par[RK_WIN_MAX_AREA];
	u32 reserved0;
};

struct rk_fb_win_cfg_data {
	u8  wait_fs;
	short ret_fence_fd;
	short rel_fence_fd[RK_MAX_BUF_NUM];
	struct  rk_fb_win_par win_par[RK30_MAX_LAYER_SUPPORT];
	struct  rk_lcdc_post_cfg post_cfg;
};
char measure_area[sizeof(struct rk_fb_area_par)];
char measure_win[sizeof(struct rk_fb_win_par)];
char measure_cfg[sizeof(struct rk_fb_win_cfg_data)];
char measure_tail[sizeof(struct rk_lcdc_post_cfg)];
char measure_tail_offset[__builtin_offsetof(struct rk_fb_win_cfg_data, post_cfg)];
