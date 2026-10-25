package os.vortex.tv;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.Inet4Address;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/**
 * One-shot local-only pairing transport. Does not require Android, root,
 * Google services or an external server. Only runs while InstallerActivity
 * is visible. HTTPS is not provided: use only on a trusted private LAN.
 */
final class LanApkServer implements AutoCloseable {
    interface Listener {
        void onStatus(String message);
        void onComplete(File apk, String sha256);
    }
    static final long MAX_APK_BYTES = 512L * 1024 * 1024;
    private static final long RESERVE_BYTES = 64L * 1024 * 1024;
    private static final long PAIR_TTL_MILLIS = 15L * 60 * 1000;
    private final ServerSocket server;
    private final File directory;
    private final String token;
    private final String ip;
    private final Listener listener;
    private final long expiresAt;
    private volatile boolean closed;
    private Thread worker;

    LanApkServer(String ip, File cacheDir, Listener listener) throws IOException {
        if (ip == null || ip.length() == 0 || ip.indexOf(':') >= 0 || cacheDir == null || listener == null)
            throw new IllegalArgumentException("IPv4 local obrigatório");
        InetAddress local = InetAddress.getByName(ip);
        if (!(local instanceof Inet4Address) ||
            (!local.isSiteLocalAddress() && !local.isLoopbackAddress()))
            throw new IllegalArgumentException("Somente endereços IPv4 privados");
        this.ip = ip;
        this.directory = cacheDir;
        this.listener = listener;
        if (!directory.isDirectory() && !directory.mkdirs())
            throw new IOException("Não foi possível criar diretório de cache");
        this.server = new ServerSocket();
        // Do not listen on wildcard 0.0.0.0; restrict uploads to the selected LAN address.
        this.server.bind(new InetSocketAddress(local, 0), 2);
        this.server.setSoTimeout(1000);
        byte[] secret = new byte[16];
        new SecureRandom().nextBytes(secret);
        this.token = hex(secret);
        this.expiresAt = System.currentTimeMillis() + PAIR_TTL_MILLIS;
    }

    String getUrl() {
        return "http://" + ip + ":" + server.getLocalPort() + "/p/" + token;
    }

    void start() {
        if (worker != null) throw new IllegalStateException("Servidor já iniciado");
        worker = new Thread(this::runLoop, "Vortex-APK-LAN");
        worker.setDaemon(true);
        worker.start();
    }

    private void runLoop() {
        listener.onStatus("Aguardando celular na rede local");
        try {
            while (!closed && System.currentTimeMillis() < expiresAt) {
                try (Socket s = server.accept()) {
                    s.setSoTimeout(20000);
                    handle(s);
                } catch (SocketTimeoutException ignored) {
                    // Poll to expire the pairing session and exit on activity close.
                } catch (IOException problem) {
                    if (!closed) listener.onStatus("Erro de comunicação: " + problem.getMessage());
                }
            }
            if (!closed) listener.onStatus("QR expirou. Reabra o instalador para renovar.");
        } finally {
            close();
        }
    }

    private static String line(InputStream in) throws IOException {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        int c;
        while ((c = in.read()) != -1) {
            if (c == '\n') break;
            if (c == '\r') continue;
            if (b.size() >= 4096) throw new IOException("Cabeçalho muito longo");
            b.write(c);
        }
        if (c == -1) throw new IOException("Cabeçalho interrompido");
        return b.toString("US-ASCII");
    }

    private void handle(Socket socket) throws IOException {
        InputStream input = new BufferedInputStream(socket.getInputStream(), 16384);
        OutputStream output = socket.getOutputStream();
        final String request;
        try { request = line(input); }
        catch (IOException ex) { return; }
        String[] first = request.split(" ");
        if (first.length != 3 || !first[2].startsWith("HTTP/1.")) {
            respond(output, 400, "Bad Request", "text/plain; charset=utf-8", "Requisição inválida");
            return;
        }
        Map<String,String> headers = new HashMap<>();
        int total = 0;
        try {
            while (true) {
                String item = line(input);
                total += item.length();
                if (total > 8192) throw new IOException("Cabeçalhos muito longos");
                if (item.length() == 0) break;
                int colon = item.indexOf(':');
                if (colon <= 0) throw new IOException("Cabeçalho inválido");
                String key = item.substring(0, colon).trim().toLowerCase(Locale.ROOT);
                if (headers.put(key, item.substring(colon+1).trim()) != null)
                    throw new IOException("Cabeçalho duplicado");
            }
        } catch (IOException ex) {
            respond(output, 400, "Bad Request", "text/plain; charset=utf-8", "Cabeçalho inválido");
            return;
        }
        if (closed || System.currentTimeMillis() > expiresAt) {
            respond(output, 403, "Forbidden", "text/plain; charset=utf-8", "Sessão expirada");
            return;
        }
        if (first[0].equals("GET") && first[1].equals("/p/" + token)) {
            respond(output, 200, "OK", "text/html; charset=utf-8", page());
        } else if (first[0].equals("POST") && first[1].equals("/upload/" + token)) {
            upload(input, output, headers);
        } else {
            respond(output, 404, "Not Found", "text/plain; charset=utf-8", "Não encontrado");
        }
    }

    private void upload(InputStream input, OutputStream output, Map<String,String> headers) throws IOException {
        String expectedOrigin = "http://" + ip + ":" + server.getLocalPort();
        String origin = headers.get("origin");
        if (!expectedOrigin.equals(origin)) {
            respond(output, 403, "Forbidden", "text/plain; charset=utf-8", "Origem não autorizada");
            return;
        }
        if (headers.containsKey("transfer-encoding") || !headers.containsKey("content-length")) {
            respond(output, 411, "Length Required", "text/plain; charset=utf-8", "Content-Length obrigatório");
            return;
        }
        String contentType = headers.get("content-type");
        if (!"application/vnd.android.package-archive".equalsIgnoreCase(contentType)) {
            respond(output, 415, "Unsupported Media Type", "text/plain; charset=utf-8", "Somente APK");
            return;
        }
        long bytes;
        try { bytes = Long.parseLong(headers.get("content-length")); }
        catch (NumberFormatException error) { bytes = -1; }
        if (bytes < 4 || bytes > MAX_APK_BYTES) {
            respond(output, 413, "Payload Too Large", "text/plain; charset=utf-8", "Arquivo inválido ou acima de 512 MB");
            return;
        }
        // PackageInstaller will create another copy, so reserve room for both.
        if (directory.getUsableSpace() < (bytes * 2 + RESERVE_BYTES)) {
            respond(output, 507, "Insufficient Storage", "text/plain; charset=utf-8", "Espaço insuficiente");
            return;
        }
        byte[] signature = new byte[4];
        int offset = 0;
        while (offset < signature.length) {
            int count = input.read(signature, offset, signature.length - offset);
            if (count < 0) throw new IOException("Arquivo interrompido");
            offset += count;
        }
        // APK must be a ZIP container; full signature validation belongs to PackageManager.
        if (signature[0] != 0x50 || signature[1] != 0x4b ||
            signature[2] != 0x03 || signature[3] != 0x04) {
            respond(output, 415, "Unsupported Media Type", "text/plain; charset=utf-8",
                "Arquivo não parece um APK");
            return;
        }
        File temp = File.createTempFile("vortex_transfer_", ".apk", directory);
        boolean completed = false;
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (OutputStream file = new FileOutputStream(temp)) {
                file.write(signature);
                digest.update(signature);
                byte[] buffer = new byte[16384];
                long remaining = bytes - 4;
                while (remaining > 0 && !closed) {
                    int read = input.read(buffer, 0, (int)Math.min(buffer.length, remaining));
                    if (read < 0) throw new IOException("Upload interrompido");
                    file.write(buffer, 0, read);
                    digest.update(buffer, 0, read);
                    remaining -= read;
                }
                if (remaining != 0) throw new IOException("Transferência interrompida");
                file.flush();
            }
            respond(output, 200, "OK", "text/plain; charset=utf-8",
                "APK recebido. Confirme a instalação na televisão.");
            listener.onStatus("APK recebido, preparando instalação");
            listener.onComplete(temp, hex(digest.digest()));
            completed = true;
            close(); // A QR session can be used once only.
        } catch (java.security.NoSuchAlgorithmException error) {
            throw new IOException("SHA-256 indisponível", error);
        } finally {
            if (!completed) temp.delete();
        }
    }

    private String page() {
        return "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            + "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            + "<title>Vortex App Installer</title><style>"
            + "body{margin:0;min-height:100vh;display:grid;place-items:center;background:linear-gradient(130deg,#18063d,#103a83);color:white;font:16px Arial,sans-serif}"
            + "main{width:min(88vw,450px);padding:28px;border:1px solid #9c82ed;border-radius:19px;background:#110f31}"
            + "input,button{width:100%;margin-top:16px}button{background:#7457d4;color:white;border:0;padding:16px;border-radius:10px;font-weight:700}"
            + "small{color:#c6c5e2}#status{min-height:2em;margin-top:16px;overflow-wrap:anywhere}"
            + "</style></head><body><main><h1>Vortex App Installer</h1>"
            + "<small>Celular e TV devem estar na mesma rede local. Arquivos APK até 512 MB.</small>"
            + "<input id='apk' type='file' accept='.apk,application/vnd.android.package-archive'>"
            + "<button id='send'>Enviar APK para a TV</button><p id='status' role='status'></p>"
            + "</main><script>"
            + "const b=document.querySelector('#send'),s=document.querySelector('#status');"
            + "b.onclick=async()=>{const f=document.querySelector('#apk').files[0];"
            + "if(!f||!f.name.toLowerCase().endsWith('.apk')){s.textContent='Selecione um APK.';return;}"
            + "if(f.size>536870912){s.textContent='APK acima de 512 MB.';return;}"
            + "b.disabled=true;s.textContent='Enviando '+f.name+'...';"
            + "try{const r=await fetch('/upload/" + token + "',{method:'POST',"
            + "headers:{'Content-Type':'application/vnd.android.package-archive'},body:f});"
            + "s.textContent=await r.text();if(!r.ok)b.disabled=false;}"
            + "catch(e){s.textContent='Falha na rede. Verifique a conexão.';b.disabled=false;}};"
            + "</script></body></html>";
    }

    private static void respond(OutputStream output, int status, String reason,
                                String type, String body) throws IOException {
        byte[] data = body.getBytes(StandardCharsets.UTF_8);
        String head = "HTTP/1.1 " + status + " " + reason + "\r\n"
            + "Content-Type: " + type + "\r\nContent-Length: " + data.length
            + "\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n"
            + "Referrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; "
            + "script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'none'\r\n"
            + "Connection: close\r\n\r\n";
        output.write(head.getBytes(StandardCharsets.US_ASCII));
        output.write(data);
        output.flush();
    }

    private static String hex(byte[] data) {
        StringBuilder s = new StringBuilder(data.length*2);
        for (byte b : data) s.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return s.toString();
    }

    @Override public void close() {
        closed = true;
        try { server.close(); } catch (IOException ignored) {}
    }
}
