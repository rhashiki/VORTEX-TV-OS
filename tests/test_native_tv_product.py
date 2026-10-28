from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class NativeVortexTVProductTest(unittest.TestCase):
    def test_preinstalled_streaming_app_separate_from_home(self):
        product=(ROOT/"rom/vortex_product.mk").read_text()
        module=(ROOT/"rom/prebuilt/Android.mk").read_text()
        self.assertIn("PRODUCT_PACKAGES += VortexHome VortexTV",product)
        self.assertIn("LOCAL_MODULE := VortexTV",module)
        self.assertIn("LOCAL_SRC_FILES := VortexTV.apk",module)
        self.assertIn("LOCAL_CERTIFICATE := platform",module)
        self.assertIn("include $(BUILD_PREBUILT)",module)

    def test_launcher_shows_preinstalled_streaming_app(self):
        apps=(ROOT/"app/src/main/java/os/vortex/tv/UserApps.java").read_text()
        self.assertIn('"os.vortex.tv.stream".equals(app.packageName)',apps)
        self.assertIn('if (!nativeStreaming &&',apps)
        self.assertIn('ApplicationInfo.FLAG_SYSTEM',apps)

    def test_private_access_file_is_generated_in_build_not_git(self):
        product=(ROOT/"rom/vortex_product.mk").read_text()
        ignore=(ROOT/".gitignore").read_text()
        self.assertIn("system/etc/vortex-tv/catalog-access",product)
        self.assertIn("rom/prebuilt/catalog-access",ignore)
        self.assertIn("rom/prebuilt/VortexTV.apk",ignore)
        self.assertFalse((ROOT/"rom/prebuilt/catalog-access").exists())
        self.assertFalse((ROOT/"rom/prebuilt/VortexTV.apk").exists())

    def test_os_remains_unvalidated_as_firmware(self):
        readme=(ROOT/"rom/prebuilt/README.md").read_text()
        self.assertIn("não contém imagem inicializável",readme)
        self.assertIn("os.vortex.tv.stream",readme)
        self.assertIn("sem login",readme)

if __name__=="__main__":unittest.main()
