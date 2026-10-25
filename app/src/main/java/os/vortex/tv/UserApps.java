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
        Collections.sort(out, (a, b) -> {
            int byLabel = label(pm, a).compareToIgnoreCase(label(pm, b));
            return byLabel != 0 ? byLabel : component(a).compareTo(component(b));
        });
        return out;
    }

    static String label(PackageManager pm, ResolveInfo app) {
        try {
            CharSequence label = app.loadLabel(pm);
            if (label != null && label.length() > 0) return label.toString();
        } catch (RuntimeException ignored) {
            // A package may have changed since the launcher query.
        }
        return app.activityInfo.packageName;
    }

    static String component(ResolveInfo app) {
        return app.activityInfo.packageName + "/" + app.activityInfo.name;
    }

    static String signature(Context context, List<ResolveInfo> apps) {
        PackageManager pm = context.getPackageManager();
        StringBuilder signature = new StringBuilder();
        for (ResolveInfo app : apps) {
            String component = component(app), label = label(pm, app);
            signature.append(component.length()).append(':').append(component)
                .append(label.length()).append(':').append(label);
            try {
                signature.append(':').append(pm.getPackageInfo(
                    app.activityInfo.packageName, 0).lastUpdateTime);
            } catch (PackageManager.NameNotFoundException ignored) {
                signature.append(":removed");
            }
            signature.append('\n');
        }
        return signature.toString();
    }
}
