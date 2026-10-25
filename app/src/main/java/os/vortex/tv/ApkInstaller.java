package os.vortex.tv;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/** Android API 25 PackageInstaller session. Always requests TV confirmation. */
final class ApkInstaller {
    interface Callback { void onStatus(String message); }
    static final String STATUS_ACTION = "os.vortex.tv.INSTALL_RESULT";
    private ApkInstaller() {}

    static void submit(Activity activity, File apk, Callback callback) {
        new Thread(() -> {
            Handler main = new Handler(Looper.getMainLooper());
            try {
                PackageManager pm = activity.getPackageManager();
                PackageInfo candidate = pm.getPackageArchiveInfo(apk.getAbsolutePath(), 0);
                if (candidate == null || candidate.packageName == null || candidate.packageName.length() == 0)
                    throw new IOException("Arquivo não é um APK Android válido");
                main.post(() -> callback.onStatus("Preparando " + candidate.packageName + "..."));
                PackageInstaller installer = pm.getPackageInstaller();
                PackageInstaller.SessionParams params =
                    new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
                params.setSize(apk.length());
                int sessionId = installer.createSession(params);
                PackageInstaller.Session session = null;
                boolean committed = false;
                try {
                    session = installer.openSession(sessionId);
                    try (InputStream source = new FileInputStream(apk);
                         OutputStream target = session.openWrite("base.apk", 0, apk.length())) {
                        byte[] buffer = new byte[16384];
                        int n;
                        while ((n = source.read(buffer)) != -1) target.write(buffer, 0, n);
                        session.fsync(target);
                    }
                    Intent result = new Intent(activity, InstallResultReceiver.class);
                    result.setAction(STATUS_ACTION);
                    result.setData(Uri.parse("vortex://install/" + sessionId));
                    PendingIntent pending = PendingIntent.getBroadcast(
                        activity, sessionId, result, PendingIntent.FLAG_UPDATE_CURRENT);
                    session.commit(pending.getIntentSender());
                    committed = true;
                    main.post(() -> callback.onStatus("APK enviado ao instalador. Confirme na TV."));
                } finally {
                    if (session != null) session.close();
                    if (!committed) installer.abandonSession(sessionId);
                }
            } catch (Exception error) {
                String message = error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage();
                main.post(() -> callback.onStatus("Instalação não iniciada: " + message));
            } finally {
                apk.delete(); // Installation session has its own copy after commit.
            }
        }, "Vortex-PackageInstall").start();
    }
}
