package os.vortex.tv;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import io.nayuki.qrcodegen.QrCode;

/** Local Wi-Fi APK transfer and USB file picker, optimized for remote-control focus. */
public final class InstallerActivity extends Activity {
    private static final int PICK_APK = 4025;
    private static final long MAX_APK_BYTES = LanApkServer.MAX_APK_BYTES;
    private LanApkServer server;
    private TextView status;
    private volatile boolean copying;
    private boolean pairingStopped;
    private boolean started;
    private boolean resumed;
    private long pairingGeneration;
    private boolean showingPairing;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showLanding();
    }

    @Override protected void onStart() {
        super.onStart();
        started = true;
        // A stopped pairing has no live server. Let the user request a new QR.
        if (pairingStopped && !copying) showLanding();
    }

    @Override protected void onResume() {
        super.onResume();
        resumed = true;
        if (pairingStopped && !copying) showLanding();
    }

    @Override protected void onPause() {
        resumed = false;
        if (server != null) {
            pairingStopped = true;
            closePairing();
        }
        super.onPause();
    }

    private void showLanding() {
        showingPairing = false;
        pairingStopped = false;
        FrameLayout root = Ui.background(this);
        LinearLayout panel = Ui.centeredPanel(this, root, "Vortex App Installer",
            "Instale APKs pelo celular ou por pendrive");
        LinearLayout wifi = Ui.tile(this, "▦", "Receber pelo celular", this::showPairing);
        LinearLayout usb = Ui.tile(this, "⇥", "Selecionar APK USB", this::pickUsb);
        LinearLayout.LayoutParams tileParams1 =
            new LinearLayout.LayoutParams(Ui.dp(this, 330), Ui.dp(this, 95));
        tileParams1.topMargin = Ui.dp(this, 24);
        panel.addView(wifi, tileParams1);
        LinearLayout.LayoutParams tileParams2 =
            new LinearLayout.LayoutParams(Ui.dp(this, 330), Ui.dp(this, 95));
        tileParams2.topMargin = Ui.dp(this, 16);
        panel.addView(usb, tileParams2);
        status = Ui.text(this, "", 14, false);
        status.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.topMargin = Ui.dp(this, 12);
        panel.addView(status, p);
        wifi.requestFocus();
    }

    private void showPairing() {
        if (copying) {
            update("Aguarde a cópia do APK terminar.");
            return;
        }
        String ip;
        try { ip = NetworkAddress.localIpv4(); }
        catch (Exception ignored) { ip = null; }
        if (ip == null) {
            Toast.makeText(this, "Conecte a TV a uma rede Wi-Fi ou Ethernet", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            closePairing();
            final long generation = pairingGeneration;
            server = new LanApkServer(ip, getCacheDir(), new LanApkServer.Listener() {
                @Override public void onStatus(String message) {
                    runOnUiThread(() -> {
                        if (started && generation == pairingGeneration) update(message);
                    });
                }
                @Override public void onComplete(File apk, String sha256) {
                    runOnUiThread(() -> {
                        // A callback queued before leaving must not install after
                        // the Activity stopped or replace a newer pairing screen.
                        if (!canShowInstaller() || generation != pairingGeneration) {
                            apk.delete();
                            return;
                        }
                        // Uploads consume the pairing once. PackageInstaller may be
                        // translucent, so onStop/onStart alone cannot clear its QR.
                        closePairing();
                        showLanding();
                        update("Arquivo recebido · SHA-256: " + sha256.substring(0, 12) + "…");
                        submitApk(apk);
                    });
                }
            });
            FrameLayout root = Ui.background(this);
            LinearLayout panel = Ui.centeredPanel(this, root, "Enviar APK para a TV",
                "Escaneie com o celular conectado à mesma rede");
            ImageView qr = new ImageView(this);
            qr.setImageBitmap(qrBitmap(server.getUrl()));
            qr.setContentDescription("QR Code do endereço " + server.getUrl());
            LinearLayout.LayoutParams imageP =
                new LinearLayout.LayoutParams(Ui.dp(this, 270), Ui.dp(this, 270));
            imageP.topMargin = Ui.dp(this, 15);
            panel.addView(qr, imageP);
            TextView address = Ui.text(this, server.getUrl(), 13, false);
            address.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams addrP = new LinearLayout.LayoutParams(-1, -2);
            addrP.topMargin = Ui.dp(this, 9);
            panel.addView(address, addrP);
            status = Ui.text(this, "Aguardando celular…", 14, false);
            status.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams statusP = new LinearLayout.LayoutParams(-1, -2);
            statusP.topMargin = Ui.dp(this, 12);
            panel.addView(status, statusP);
            showingPairing = true;
            server.start();
        } catch (Exception problem) {
            closePairing();
            Toast.makeText(this, "Não foi possível abrir o QR: " + problem.getMessage(), Toast.LENGTH_LONG).show();
            showLanding();
        }
    }

    private static Bitmap qrBitmap(String url) {
        QrCode code = QrCode.encodeText(url, QrCode.Ecc.MEDIUM);
        int quiet = 4, size = code.size + 2 * quiet, scale = Math.max(1, 300 / size);
        int pixels = size * scale;
        Bitmap bitmap = Bitmap.createBitmap(pixels, pixels, Bitmap.Config.RGB_565);
        int[] row = new int[pixels];
        for (int y = 0; y < pixels; y++) {
            for (int x = 0; x < pixels; x++) {
                int cx = x / scale - quiet, cy = y / scale - quiet;
                boolean dark = cx >= 0 && cy >= 0 && cx < code.size && cy < code.size &&
                    code.getModule(cx, cy);
                row[x] = dark ? 0xFF0B1230 : 0xFFFFFFFF;
            }
            bitmap.setPixels(row, 0, pixels, 0, y, pixels, 1);
        }
        return bitmap;
    }

    private void update(String message) {
        if (status != null) status.setText(message);
    }

    private boolean canShowInstaller() {
        return started && resumed && !isFinishing() && !isDestroyed();
    }

    private void closePairing() {
        pairingGeneration++;
        if (server != null) {
            server.close();
            server = null;
        }
    }

    private void submitApk(File apk) {
        final long generation = pairingGeneration;
        ApkInstaller.submit(this, apk, message -> {
            if (canShowInstaller() && !showingPairing && generation == pairingGeneration)
                update(message);
        });
    }

    private void pickUsb() {
        if (copying) {
            update("Aguarde a cópia do APK terminar.");
            return;
        }
        Intent select = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        select.addCategory(Intent.CATEGORY_OPENABLE);
        select.setType("*/*");
        try { startActivityForResult(select, PICK_APK); }
        catch (RuntimeException error) {
            Toast.makeText(this, "Seletor de arquivos indisponível nesta ROM", Toast.LENGTH_LONG).show();
        }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != PICK_APK || result != RESULT_OK || data == null || data.getData() == null)
            return;
        if (copying) return;
        copying = true;
        update("Copiando APK…");
        Uri uri = data.getData();
        new Thread(() -> {
            File cache = null;
            try {
                cache = File.createTempFile("vortex_usb_", ".apk", getCacheDir());
                long size = 0;
                try (InputStream src = getContentResolver().openInputStream(uri);
                     FileOutputStream dst = new FileOutputStream(cache)) {
                    if (src == null) throw new IOException("Arquivo não pode ser aberto");
                    byte[] buffer = new byte[16384];
                    int n;
                    while ((n = src.read(buffer)) != -1) {
                        size += n;
                        if (size > MAX_APK_BYTES) throw new IOException("APK acima de 512 MB");
                        dst.write(buffer, 0, n);
                    }
                }
                if (size == 0) throw new IOException("Arquivo vazio");
                File ready = cache;
                runOnUiThread(() -> {
                    copying = false;
                    if (!canShowInstaller()) {
                        ready.delete();
                        return;
                    }
                    showLanding();
                    submitApk(ready);
                });
                cache = null;
            } catch (Exception error) {
                String message = error.getMessage() == null ? "erro desconhecido" : error.getMessage();
                runOnUiThread(() -> {
                    copying = false;
                    if (canShowInstaller()) update("Erro ao abrir APK: " + message);
                });
            } finally {
                if (cache != null) cache.delete();
            }
        }, "Vortex-USB-Reader").start();
    }

    @Override protected void onStop() {
        started = false;
        if (server != null) {
            pairingStopped = true;
        }
        closePairing();
        super.onStop();
    }

    @Override public void onBackPressed() {
        if (showingPairing) {
            closePairing();
            showLanding();
        } else {
            super.onBackPressed();
        }
    }
}
