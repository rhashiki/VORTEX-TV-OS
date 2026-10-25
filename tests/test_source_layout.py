"""Static checks only; does NOT replace Android SDK compilation or boot tests."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"

class StarterChecks(unittest.TestCase):
    def setUp(self):
        self.manifest = ET.parse(R / "app/src/main/AndroidManifest.xml").getroot()

    def test_android_api(self):
        gradle = (R / "app/build.gradle").read_text()
        self.assertIn("minSdk 25", gradle)
        self.assertIn("targetSdk 25", gradle)

    def test_home_category(self):
        categories = [x.get(ANDROID + "name") for x in self.manifest.iter("category")]
        self.assertIn("android.intent.category.HOME", categories)
        self.assertIn("android.intent.category.LEANBACK_LAUNCHER", categories)

    def test_no_touch_requirement(self):
        features = {x.get(ANDROID + "name"):x.get(ANDROID + "required")
                    for x in self.manifest.findall("uses-feature")}
        self.assertEqual(features["android.hardware.touchscreen"], "false")

    def test_no_extraneous_runtime(self):
        source = "\n".join(p.read_text() for p in (R / "app/src/main/java").rglob("*.java"))
        for forbidden in ("BluetoothAdapter", "WebView", "ServerSocket", "GoogleApiClient"):
            self.assertNotIn(forbidden, source)

    def test_launcher_tiles(self):
        text = (R / "app/src/main/java/os/vortex/tv/HomeActivity.java").read_text()
        for title in ("Instalar APK", "Configurações", "Energia"):
            self.assertIn(title, text)

    def test_installer_is_placeholder(self):
        text = (R / "app/src/main/java/os/vortex/tv/InstallerActivity.java").read_text()
        self.assertIn("Build 02", text)

    def test_no_unverified_firmware_copy(self):
        mk = (R / "rom/vortex_product.mk").read_text()
        self.assertNotIn("PRODUCT_COPY_FILES", mk)

if __name__ == "__main__":
    unittest.main()
