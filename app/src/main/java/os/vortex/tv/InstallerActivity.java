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

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showLanding();
    }

    private void showLanding() {
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
        String ip;
        try { ip = NetworkAddress.localIpv4(); }
        catch (Exception ignored) { ip = null; }
        if (ip == null) {
            Toast.makeText(this, "Conecte a TV a uma rede Wi-Fi ou Ethernet", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            if (server != null) server.close();
            server = new LanApkServer(ip, getCacheDir(), new LanApkServer.Listener() {
                @Override public void onStatus(String message) { runOnUiThread(() -> update(message)); }
                @Override public void onComplete(File apk, String sha256) {
                    runOnUiThread(() -> {
                        update("Arquivo recebido · SHA-256: " + sha256.substring(0, 12) + "…");
                        ApkInstaller.submit(InstallerActivity.this, apk, InstallerActivity.this::update);
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
            server.start();
        } catch (Exception problem) {
            if (server != null) server.close();
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

    private void pickUsb() {
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
                    showLanding();
                    ApkInstaller.submit(this, ready, this::update);
                });
                cache = null;
            } catch (Exception error) {
                String message = error.getMessage() == null ? "erro desconhecido" : error.getMessage();
                runOnUiThread(() -> {
                    copying = false;
                    Toast.makeText(this, "Erro ao abrir APK: " + message, Toast.LENGTH_LONG).show();
                });
            } finally {
                if (cache != null) cache.delete();
            }
        }, "Vortex-USB-Reader").start();
    }

    @Override protected void onStop() {
        if (server != null) {
            server.close();
            server = null;
        }
        super.onStop();
    }
}
