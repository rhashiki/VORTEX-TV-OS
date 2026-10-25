package os.vortex.tv;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

/** API 25. Native Android widgets, no WebView and no background network service. */
final class Ui {
    private Ui() {}
    static final int WHITE = Color.rgb(248, 246, 255);
    static final int MUTED = Color.rgb(200, 196, 228);
    static int dp(Context c, int n) { return (int) (n * c.getResources().getDisplayMetrics().density + 0.5f); }
    static GradientDrawable gradient() {
        return new GradientDrawable(GradientDrawable.Orientation.TL_BR,
            new int[] { 0xFF12042E, 0xFF2B116A, 0xFF153A88, 0xFF042A54 });
    }
    static TextView text(Context c, String s, int sp, boolean bold) {
        TextView v = new TextView(c);
        v.setText(s);
        v.setTextColor(WHITE);
        v.setTextSize(sp);
        if (bold) v.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        return v;
    }
    static FrameLayout background(Activity a) {
        FrameLayout f = new FrameLayout(a);
        f.setBackground(gradient());
        f.setFocusable(false);
        a.setContentView(f);
        a.getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        return f;
    }
    static LinearLayout vertical(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }
    static GradientDrawable tileBackground(boolean focused) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(focused ? 0xCC6546CB : 0xA6202350);
        d.setCornerRadius(24f);
        d.setStroke(focused ? 3 : 1, focused ? 0xFFE4D7FF : 0x806F79B9);
        return d;
    }
    static LinearLayout tile(Activity a, String symbol, String title, final Runnable click) {
        LinearLayout t = vertical(a);
        t.setGravity(Gravity.CENTER);
        t.setPadding(dp(a, 16), dp(a, 12), dp(a, 16), dp(a, 12));
        t.setBackground(tileBackground(false));
        t.setFocusable(true);
        t.setClickable(true);
        t.setContentDescription(title);
        TextView icon = text(a, symbol, 34, false);
        icon.setGravity(Gravity.CENTER);
        TextView label = text(a, title, 16, true);
        label.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams labelP = new LinearLayout.LayoutParams(-1, -2);
        labelP.topMargin = dp(a, 11);
        t.addView(icon, new LinearLayout.LayoutParams(-1, -2));
        t.addView(label, labelP);
        t.setOnFocusChangeListener((view, focused) -> {
            view.setBackground(tileBackground(focused));
            view.setScaleX(focused ? 1.035f : 1f);
            view.setScaleY(focused ? 1.035f : 1f);
        });
        t.setOnClickListener(v -> click.run());
        return t;
    }
    static void addTile(Activity a, LinearLayout row, LinearLayout tile, boolean first) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(dp(a, 190), dp(a, 132));
        if (!first) p.leftMargin = dp(a, 18);
        row.addView(tile, p);
    }
    static LinearLayout centeredPanel(Activity a, FrameLayout root, String title, String subtitle) {
        LinearLayout p = vertical(a);
        p.setGravity(Gravity.CENTER_HORIZONTAL);
        p.setPadding(dp(a, 25), dp(a, 20), dp(a, 25), dp(a, 20));
        TextView heading = text(a, title, 28, true);
        heading.setGravity(Gravity.CENTER);
        TextView detail = text(a, subtitle, 15, false);
        detail.setTextColor(MUTED);
        detail.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams detailP = new LinearLayout.LayoutParams(-1, -2);
        detailP.topMargin = dp(a, 12);
        p.addView(heading);
        p.addView(detail, detailP);
        FrameLayout.LayoutParams fp = new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER);
        root.addView(p, fp);
        return p;
    }
}
