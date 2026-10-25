package os.vortex.tv;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.PowerManager;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextClock;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.List;

/** Native TV shell; D-pad handled by Android's focus navigation. */
public final class HomeActivity extends Activity {
    private ScrollView scroll;
    private String appsSignature;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        refreshApps();
    }
    @Override protected void onResume() {
        super.onResume();
        refreshApps();
    }
    private void refreshApps() {
        List<ResolveInfo> apps = UserApps.list(this);
        String signature = UserApps.signature(this, apps);
        if (scroll == null || !signature.equals(appsSignature)) {
            appsSignature = signature;
            render(apps);
        }
    }
    private void render(List<ResolveInfo> apps) {
        View current = getCurrentFocus();
        Object focusedTag = current == null ? null : current.getTag();
        int oldScroll = scroll == null ? 0 : scroll.getScrollY();
        FrameLayout root = Ui.background(this);
        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setPadding(Ui.dp(this, 58), Ui.dp(this, 32), Ui.dp(this, 58), 0);
        TextView brand = Ui.text(this, "VORTEX TV OS", 23, true);
        brand.setLetterSpacing(0.15f);
        top.addView(brand, new LinearLayout.LayoutParams(0, -2, 1f));
        LinearLayout clockPanel = Ui.vertical(this);
        clockPanel.setGravity(Gravity.RIGHT);
        TextClock time = new TextClock(this);
        time.setFormat24Hour("HH:mm");
        time.setFormat12Hour("h:mm a");
        time.setTextSize(27);
        time.setTextColor(Ui.WHITE);
        time.setGravity(Gravity.RIGHT);
        TextClock date = new TextClock(this);
        date.setFormat24Hour("EEE, d MMM yyyy");
        date.setFormat12Hour("EEE, d MMM yyyy");
        date.setTextColor(Ui.MUTED);
        date.setTextSize(14);
        date.setGravity(Gravity.RIGHT);
        clockPanel.addView(time);
        clockPanel.addView(date);
        top.addView(clockPanel);
        root.addView(top, new FrameLayout.LayoutParams(-1, -2, Gravity.TOP));
        scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setFocusable(false);
        scroll.setDescendantFocusability(ViewGroup.FOCUS_AFTER_DESCENDANTS);
        scroll.setClipToPadding(false);
        scroll.setPadding(0, Ui.dp(this, 8), 0, Ui.dp(this, 12));
        FrameLayout.LayoutParams scrollParams = new FrameLayout.LayoutParams(-1, -1);
        scrollParams.setMargins(Ui.dp(this, 58), Ui.dp(this, 124), Ui.dp(this, 58), Ui.dp(this, 32));
        root.addView(scroll, scrollParams);
        LinearLayout grid = Ui.vertical(this);
        grid.setGravity(Gravity.CENTER);
        scroll.addView(grid, new ScrollView.LayoutParams(-1, -2));

        List<LinearLayout> tiles = new ArrayList<>();
        LinearLayout install = Ui.tile(this, "⇧", "Instalar APK",
            () -> startActivity(new Intent(this, InstallerActivity.class)));
        install.setTag("action:install");
        tiles.add(install);
        LinearLayout settings = Ui.tile(this, "⚙", "Configurações",
            () -> startActivity(new Intent(this, SettingsActivity.class)));
        settings.setTag("action:settings");
        tiles.add(settings);
        LinearLayout power = Ui.tile(this, R.drawable.ic_power, "Energia", this::powerMenu);
        power.setTag("action:power");
        tiles.add(power);
        PackageManager pm = getPackageManager();
        for (ResolveInfo app : apps) {
            String pkg = app.activityInfo.packageName;
            String activity = app.activityInfo.name;
            Drawable icon;
            try { icon = app.loadIcon(pm); }
            catch (RuntimeException ignored) { icon = pm.getDefaultActivityIcon(); }
            LinearLayout tile = Ui.tile(this, icon, UserApps.label(pm, app), () -> {
                try {
                    Intent launch = new Intent(Intent.ACTION_MAIN);
                    launch.setComponent(new ComponentName(pkg, activity));
                    launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(launch);
                } catch (RuntimeException error) {
                    Toast.makeText(this, "Não foi possível abrir esse aplicativo", Toast.LENGTH_LONG).show();
                }
            });
            tile.setTag("app:" + UserApps.component(app));
            tiles.add(tile);
        }
        int availableDp = getResources().getConfiguration().screenWidthDp - 116;
        int columns = Math.max(1, (availableDp + 18) / 208);
        int tileWidth = Math.min(190, Math.max(1, availableDp));
        LinearLayout row = null;
        for (int i = 0; i < tiles.size(); i++) {
            if (i % columns == 0) {
                row = new LinearLayout(this);
                row.setGravity(Gravity.CENTER);
                LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(-1, -2);
                if (i > 0) rowParams.topMargin = Ui.dp(this, 18);
                grid.addView(row, rowParams);
            }
            LinearLayout.LayoutParams tileParams = new LinearLayout.LayoutParams(
                Ui.dp(this, tileWidth), Ui.dp(this, 132));
            if (i % columns != 0) tileParams.leftMargin = Ui.dp(this, 18);
            row.addView(tiles.get(i), tileParams);
        }
        View restore = focusedTag == null ? null : root.findViewWithTag(focusedTag);
        View focus = restore == null ? install : restore;
        int restoreScroll = restore == null ? 0 : oldScroll;
        ScrollView renderedScroll = scroll;
        renderedScroll.post(() -> {
            renderedScroll.scrollTo(0, restoreScroll);
            focus.requestFocus();
            focus.requestRectangleOnScreen(new Rect(0, 0, focus.getWidth(), focus.getHeight()), true);
        });
    }
    private void powerMenu() {
        final String[] options = { "Reiniciar", "Desligar", "Cancelar" };
        new AlertDialog.Builder(this).setTitle("Energia").setItems(options, (d, which) -> {
            if (which == 0) {
                try {
                    PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
                    if (pm == null) throw new SecurityException("PowerManager indisponível");
                    pm.reboot(null); // Actual reboot requires permission granted in ROM.
                } catch (SecurityException ex) {
                    Toast.makeText(this, "Reinício precisa da permissão de sistema da ROM", Toast.LENGTH_LONG).show();
                }
            } else if (which == 1) {
                try {
                    Intent shutdown = new Intent("android.intent.action.ACTION_REQUEST_SHUTDOWN");
                    shutdown.putExtra("android.intent.extra.KEY_CONFIRM", true);
                    startActivity(shutdown);
                } catch (RuntimeException ex) {
                    Toast.makeText(this, "Desligamento ainda não autorizado pela ROM", Toast.LENGTH_LONG).show();
                }
            }
        }).show();
    }
}
