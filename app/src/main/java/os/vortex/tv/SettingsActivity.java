package os.vortex.tv;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Toast;

public final class SettingsActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = Ui.background(this);
        LinearLayout panel = Ui.centeredPanel(this, root, "Configurações", "Ajustes básicos do dispositivo");
        String[][] opts = {
            {"Wi-Fi", Settings.ACTION_WIFI_SETTINGS},
            {"Rede", Settings.ACTION_WIRELESS_SETTINGS},
            {"Tela", Settings.ACTION_DISPLAY_SETTINGS},
            {"Som", Settings.ACTION_SOUND_SETTINGS},
            {"Data e hora", Settings.ACTION_DATE_SETTINGS},
            {"Sistema", Settings.ACTION_SETTINGS},
            {"Segurança / APKs", Settings.ACTION_SECURITY_SETTINGS}
        };
        LinearLayout grid = Ui.vertical(this);
        panel.addView(grid);
        LinearLayout firstFocus = null;
        for (int i = 0; i < opts.length; i += 2) {
            LinearLayout r = new LinearLayout(this);
            r.setOrientation(LinearLayout.HORIZONTAL);
            for (int j = i; j < Math.min(i + 2, opts.length); j++) {
                String[] item = opts[j];
                LinearLayout tile = Ui.tile(this, "›", item[0], () -> {
                    try { startActivity(new Intent(item[1])); }
                    catch (RuntimeException ex) {
                        Toast.makeText(this, "Ajuste indisponível nesta ROM", Toast.LENGTH_LONG).show();
                    }
                });
                if (firstFocus == null) firstFocus = tile;
                LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(Ui.dp(this, 230), Ui.dp(this, 100));
                p.leftMargin = Ui.dp(this, 8);
                p.topMargin = Ui.dp(this, 12);
                r.addView(tile, p);
            }
            grid.addView(r);
        }
        if (firstFocus != null) firstFocus.requestFocus();
    }
}
