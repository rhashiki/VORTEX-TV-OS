package os.vortex.tv;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.PowerManager;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextClock;
import android.widget.TextView;
import android.widget.Toast;

/** Native TV shell; D-pad handled by Android's focus navigation. */
public final class HomeActivity extends Activity {
    private LinearLayout row;
    private int appCount = -1;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        render();
    }
    @Override protected void onResume() {
        super.onResume();
        if (row != null && UserApps.list(this).size() != appCount) render();
    }
    private void render() {
        appCount = UserApps.list(this).size();
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
        row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER);
        Ui.addTile(this, row, Ui.tile(this, "⇧", "Instalar APK",
            () -> startActivity(new Intent(this, InstallerActivity.class))), true);
        Ui.addTile(this, row, Ui.tile(this, "⚙", "Configurações",
            () -> startActivity(new Intent(this, SettingsActivity.class))), false);
        Ui.addTile(this, row, Ui.tile(this, "⏻", "Energia", this::powerMenu), false);
        if (appCount > 0) {
            Ui.addTile(this, row, Ui.tile(this, "▦", "Meus apps",
                () -> startActivity(new Intent(this, AppsActivity.class))), false);
        }
        root.addView(row, new FrameLayout.LayoutParams(-1, -2, Gravity.CENTER));
        row.getChildAt(0).requestFocus();
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
