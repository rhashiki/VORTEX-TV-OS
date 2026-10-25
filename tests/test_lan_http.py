"""End-to-end HTTP transport test using only JDK + Python localhost."""
import hashlib
import selectors
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "JDK needed")
class LocalTransferTest(unittest.TestCase):
    def test_pairing_token_origin_and_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = [ROOT / "app/src/main/java/os/vortex/tv/LanApkServer.java",
                   ROOT / "tests/LanApkServerHarness.java"]
            subprocess.run(["javac","-encoding","UTF-8","-d",tmp,*map(str,src)],
                           capture_output=True,text=True,check=True,timeout=30)
            p = subprocess.Popen(["java","-cp",tmp,"os.vortex.tv.LanApkServerHarness"],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                with selectors.DefaultSelector() as ready:
                    ready.register(p.stdout, selectors.EVENT_READ)
                    self.assertTrue(ready.select(timeout=5), "Java server startup timed out")
                    url=p.stdout.readline().strip()
                if not url.startswith("http://127.0.0.1:"):
                    output, err = p.communicate(timeout=5)
                    self.fail(f"Java server failed to start: {url}\n{output}\n{err}")
                with urllib.request.urlopen(url,timeout=4) as r:
                    self.assertIn("Vortex App Installer",r.read().decode("utf-8"))
                origin=url.split("/p/")[0]
                upload=url.replace("/p/","/upload/")
                payload=b"PK\x03\x04"+b"test-only-not-an-actual-apk"
                headers={"Content-Type":"application/vnd.android.package-archive"}
                bad=urllib.request.Request(upload,data=payload,method="POST",
                      headers={**headers,"Origin":"http://attacker.invalid"})
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(bad,timeout=4)
                self.assertEqual(e.exception.code,403)
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(origin+"/p/wrong-token",timeout=4)
                self.assertEqual(e.exception.code,404)
                malformed=urllib.request.Request(upload,data=b"NOT_AN_APK",method="POST",
                      headers={**headers,"Origin":origin})
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(malformed,timeout=4)
                self.assertEqual(e.exception.code,415)
                missing_origin=urllib.request.Request(upload,data=payload,method="POST",
                      headers=headers)
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(missing_origin,timeout=4)
                self.assertEqual(e.exception.code,403)
                valid=urllib.request.Request(upload,data=payload,method="POST",
                      headers={**headers,"Origin":origin})
                with urllib.request.urlopen(valid,timeout=4) as r:
                    self.assertEqual(r.status,200)
                    self.assertIn("Confirme a instalação",r.read().decode("utf-8"))
                output,err=p.communicate(timeout=7)
                self.assertEqual(p.returncode,0,err)
                self.assertIn("SHA256="+hashlib.sha256(payload).hexdigest(),output)
            finally:
                if p.poll() is None:
                    p.kill()
                p.communicate(timeout=5)

if __name__=="__main__":unittest.main()
