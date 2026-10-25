package os.vortex.tv;

import android.app.Activity;
import android.os.Bundle;
import android.widget.FrameLayout;

/** Build 02 placeholder. Does not open network sockets yet. */
public final class InstallerActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = Ui.background(this);
        Ui.centeredPanel(this, root, "Vortex App Installer",
            "Recebimento por QR Code e instalação: implementação prevista para a Build 02.");
    }
}
