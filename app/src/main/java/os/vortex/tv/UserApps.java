package os.vortex.tv;

import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

final class UserApps {
    private UserApps() {}
    static List<ResolveInfo> list(Context c) {
        PackageManager pm = c.getPackageManager();
        List<ResolveInfo> out = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        Intent[] intents = {
            new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER),
            new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        };
        for (Intent i : intents) {
            for (ResolveInfo info : pm.queryIntentActivities(i, 0)) {
                if (info.activityInfo == null || info.activityInfo.applicationInfo == null) continue;
                ApplicationInfo app = info.activityInfo.applicationInfo;
                if (c.getPackageName().equals(app.packageName)) continue;
                if ((app.flags & ApplicationInfo.FLAG_SYSTEM) != 0 &&
                    (app.flags & ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) == 0) continue;
                if (seen.add(app.packageName)) out.add(info);
            }
        }
        Collections.sort(out, (a, b) -> String.valueOf(a.loadLabel(pm))
            .compareToIgnoreCase(String.valueOf(b.loadLabel(pm))));
        return out;
    }
}
