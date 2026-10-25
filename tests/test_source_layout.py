"""Source contract checks: Android build/device verification is separate."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID="{http://schemas.android.com/apk/res/android}"
def read(path):return (ROOT/path).read_text(encoding="utf-8")

class ContractChecks(unittest.TestCase):
    def setUp(self):
        self.manifest=ET.parse(ROOT/"app/src/main/AndroidManifest.xml").getroot()

    def test_legacy_android_api(self):
        gradle=read("app/build.gradle")
        self.assertIn("minSdk 25",gradle)
        self.assertIn("targetSdk 25",gradle)

    def test_home_and_remote(self):
        cats=[v.get(ANDROID+"name") for v in self.manifest.iter("category")]
        self.assertIn("android.intent.category.HOME",cats)
        self.assertIn("android.intent.category.LEANBACK_LAUNCHER",cats)
        features={v.get(ANDROID+"name"):v.get(ANDROID+"required")
            for v in self.manifest.findall("uses-feature")}
        self.assertEqual(features["android.hardware.touchscreen"],"false")

    def test_no_google_or_bluetooth(self):
        main="\n".join(f.read_text(encoding="utf-8")
            for f in (ROOT/"app/src/main/java/os/vortex/tv").rglob("*.java"))
        for forbidden in ("BluetoothAdapter","WebView","GoogleApiClient","Firebase"):
            self.assertNotIn(forbidden,main)

    def test_lan_permission_and_nonexported_receiver(self):
        permissions=[v.get(ANDROID+"name") for v in self.manifest.findall("uses-permission")]
        self.assertIn("android.permission.INTERNET",permissions)
        receives=[v for v in self.manifest.findall(".//receiver")
            if v.get(ANDROID+"name")==".InstallResultReceiver"]
        self.assertEqual(len(receives),1)
        self.assertEqual(receives[0].get(ANDROID+"exported"),"false")

    def test_lan_session_security(self):
        server=read("app/src/main/java/os/vortex/tv/LanApkServer.java")
        for feature in ("SecureRandom","PAIR_TTL_MILLIS","SHA-256",
                        "MAX_APK_BYTES","getUsableSpace","Origin",
                        "content-length","getUrl()","File.createTempFile"):
            self.assertIn(feature,server)

    def test_qr_usb_and_package_installer(self):
        installer=read("app/src/main/java/os/vortex/tv/InstallerActivity.java")
        self.assertIn("QrCode.encodeText",installer)
        self.assertIn("Intent.ACTION_OPEN_DOCUMENT",installer)
        self.assertIn("ApkInstaller.submit",installer)
        package=read("app/src/main/java/os/vortex/tv/ApkInstaller.java")
        self.assertIn("PackageInstaller.Session",package)
        self.assertIn("session.commit",package)
        receiver=read("app/src/main/java/os/vortex/tv/InstallResultReceiver.java")
        self.assertIn("STATUS_PENDING_USER_ACTION",receiver)

    def test_home_tiles(self):
        home=read("app/src/main/java/os/vortex/tv/HomeActivity.java")
        for label in ("Instalar APK","Configurações","Energia","Meus apps"):
            self.assertIn(label,home)

    def test_no_firmware_loader_overwrite(self):
        product=read("rom/vortex_product.mk")
        self.assertNotIn("PRODUCT_COPY_FILES",product)

    def test_bootanimation_generator(self):
        gen=read("tools/bootanimation_from_video.py")
        for item in ("part0","part1","1280 720","zipfile.ZIP_STORED"):
            self.assertIn(item,gen)

if __name__=="__main__":unittest.main()
