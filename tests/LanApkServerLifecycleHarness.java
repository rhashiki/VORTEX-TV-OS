package os.vortex.tv;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.util.concurrent.atomic.AtomicInteger;

/** Test-only control channel; network behavior is exercised through real sockets. */
public final class LanApkServerLifecycleHarness {
    public static void main(String[] args) throws Exception {
        File cache = Files.createTempDirectory("vortex-lifecycle-").toFile();
        AtomicInteger complete = new AtomicInteger();
        LanApkServer transport = new LanApkServer("127.0.0.1", cache, new LanApkServer.Listener() {
            @Override public void onStatus(String message) {}
            @Override public void onComplete(File apk, String sha256) {
                complete.incrementAndGet();
                apk.delete();
            }
        }, Long.parseLong(args[0]));
        transport.start();
        System.out.println(transport.getUrl());
        System.out.flush();
        try (BufferedReader control = new BufferedReader(new InputStreamReader(System.in))) {
            String command;
            while ((command = control.readLine()) != null) {
                if (command.equals("close")) {
                    transport.close();
                    System.out.println("CLOSED");
                } else if (command.equals("state")) {
                    File[] files = cache.listFiles();
                    long size = 0;
                    if (files != null) for (File file : files) size += file.length();
                    System.out.println("STATE " + complete.get() + " " +
                        (files == null ? 0 : files.length) + " " + size);
                } else if (command.equals("exit")) {
                    break;
                } else {
                    throw new IllegalArgumentException("Unknown control command");
                }
                System.out.flush();
            }
        } finally {
            transport.close();
            File[] files = cache.listFiles();
            if (files != null) for (File file : files) file.delete();
            cache.delete();
        }
    }
}
