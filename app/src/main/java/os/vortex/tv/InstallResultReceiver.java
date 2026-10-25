package os.vortex.tv;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.widget.Toast;

/** Receives a PackageInstaller session result; not exported to other apps. */
public final class InstallResultReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent result) {
        if (!ApkInstaller.STATUS_ACTION.equals(result.getAction())) return;
        int status = result.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirm = result.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirm == null) {
                Toast.makeText(context, "Confirmação de instalação indisponível", Toast.LENGTH_LONG).show();
                return;
            }
            try {
                confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(confirm);
            } catch (RuntimeException ex) {
                Toast.makeText(context, "Não foi possível abrir a confirmação de instalação", Toast.LENGTH_LONG).show();
            }
        } else if (status == PackageInstaller.STATUS_SUCCESS) {
            Toast.makeText(context, "Aplicativo instalado com sucesso", Toast.LENGTH_LONG).show();
        } else {
            String reason = result.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
            Toast.makeText(context, "Erro na instalação: " + (reason == null ? status : reason),
                Toast.LENGTH_LONG).show();
        }
    }
}
