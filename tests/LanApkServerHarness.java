package os.vortex.tv;
import java.io.File;
import java.nio.file.Files;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Isolated JDK transport test harness; never packaged in Android app. */
public final class LanApkServerHarness {
    public static void main(String[] args) throws Exception {
        File cache = Files.createTempDirectory("vortex-lan-test").toFile();
        CountDownLatch complete = new CountDownLatch(1);
        LanApkServer transport = new LanApkServer("127.0.0.1", cache, new LanApkServer.Listener() {
            @Override public void onStatus(String message) {}
            @Override public void onComplete(File apk, String sha256) {
                System.out.println("SHA256=" + sha256);
                System.out.flush();
                apk.delete();
                complete.countDown();
            }
        });
        transport.start();
        System.out.println(transport.getUrl());
        System.out.flush();
        if (!complete.await(12, TimeUnit.SECONDS))
            throw new IllegalStateException("No successful upload before timeout");
        if (args.length > 0 && "--hold-after-upload".equals(args[0])) {
            // Keep the JVM alive so a second connection tests the transport's
            // one-shot close rather than process teardown. Never wait indefinitely.
            CountDownLatch release = new CountDownLatch(1);
            Thread control = new Thread(() -> {
                try { System.in.read(); }
                catch (java.io.IOException ignored) {}
                finally { release.countDown(); }
            }, "Vortex-Test-Control");
            control.setDaemon(true);
            control.start();
            if (!release.await(7, TimeUnit.SECONDS))
                throw new IllegalStateException("Test did not release harness before timeout");
        }
        transport.close();
        cache.delete();
    }
}
