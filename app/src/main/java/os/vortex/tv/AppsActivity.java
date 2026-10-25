package os.vortex.tv;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Bundle;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Toast;
import java.util.List;

public final class AppsActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = Ui.background(this);
        LinearLayout content = Ui.centeredPanel(this, root, "Meus aplicativos", "Apps instalados pelo usuário");
        List<ResolveInfo> apps = UserApps.list(this);
        if (apps.isEmpty()) {
            content.addView(Ui.text(this, "Nenhum aplicativo instalado", 17, false));
            return;
        }
        PackageManager pm = getPackageManager();
        ScrollView scroll = new ScrollView(this);
        LinearLayout list = Ui.vertical(this);
        for (ResolveInfo item : apps) {
            String pkg = item.activityInfo.packageName;
            String activity = item.activityInfo.name;
            LinearLayout tile = Ui.tile(this, "▹", String.valueOf(item.loadLabel(pm)), () -> {
                try {
                    Intent launch = new Intent(Intent.ACTION_MAIN);
                    launch.setComponent(new ComponentName(pkg, activity));
                    launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(launch);
                } catch (RuntimeException ex) {
                    Toast.makeText(this, "Não foi possível abrir esse aplicativo", Toast.LENGTH_LONG).show();
                }
            });
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(Ui.dp(this, 320), Ui.dp(this, 104));
            p.bottomMargin = Ui.dp(this, 12);
            list.addView(tile, p);
        }
        scroll.addView(list);
        content.addView(scroll, new LinearLayout.LayoutParams(Ui.dp(this, 350), Ui.dp(this, 330)));
        list.getChildAt(0).requestFocus();
    }
}
