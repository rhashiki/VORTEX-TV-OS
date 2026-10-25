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
        complete.await(12, TimeUnit.SECONDS);
        transport.close();
        cache.delete();
    }
}
