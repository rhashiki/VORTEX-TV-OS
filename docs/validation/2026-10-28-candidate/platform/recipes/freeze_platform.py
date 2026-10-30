"""Freeze this bounded, incomplete whole-platform experiment without altering sources."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'evidence-package'
MAX_GIT_BYTES = 250 * 1024


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    return {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def copy_small(source, relative):
    if source.stat().st_size > MAX_GIT_BYTES:
        return False
    destination = PACKAGE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return True


PACKAGE.mkdir(exist_ok=False)
large = []
for source in sorted((ROOT / 'evidence').rglob('*')):
    if not source.is_file():
        continue
    relative = Path('evidence') / source.relative_to(ROOT / 'evidence')
    if not copy_small(source, relative):
        large.append({'path': str(source.relative_to(ROOT)), 'bytes': source.stat().st_size,
                      'sha256': digest(source), 'package_path': 'raw-logs/platform/' + str(source.relative_to(ROOT / 'evidence'))})

for source in sorted(ROOT.glob('*.json')) + sorted(ROOT.glob('*.sh')) + sorted(ROOT.glob('*.py')) + [ROOT / 'audit-tail.mk']:
    copy_small(source, Path('recipes') / source.name)
for source in sorted((ROOT / 'out').glob('candidate-*.list')):
    copy_small(source, Path('make-attempt-final') / source.name)

git_sources = []
for directory, subdirs, files in os.walk(ROOT / 'tree', followlinks=False):
    if '.git' not in subdirs:
        continue
    subdirs.remove('.git')
    source = Path(directory)
    git_sources.append({'path': str(source.relative_to(ROOT / 'tree')),
                        'head': command(['git', 'rev-parse', 'HEAD'], source),
                        'origin': command(['git', 'config', '--get', 'remote.origin.url'], source),
                        'status': command(['git', 'status', '--porcelain'], source)})
(PACKAGE / 'git-source-checkouts.json').write_text(json.dumps(git_sources, indent=2) + '\n')
(PACKAGE / 'large-raw-files.json').write_text(json.dumps(large, indent=2) + '\n')

artifacts = []
for module in ('core-all', 'core-oj', 'core-libart'):
    source = ROOT / 'out/target/common/obj/JAVA_LIBRARIES' / (module + '_intermediates') / 'classes-full-debug.jar'
    if not source.is_file():
        continue
    destination = ROOT / 'artifacts' / (module + '-classes-full-debug.jar')
    shutil.copyfile(source, destination)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        classes = [name for name in archive.namelist() if name.endswith('.class')]
        assert all(archive.read(name)[:4] == b'\xca\xfe\xba\xbe' for name in classes)
        entry_count = len(archive.namelist())
        major_versions = sorted({int.from_bytes(archive.read(name)[6:8], 'big') for name in classes})
    artifacts.append({'path': str(destination.relative_to(ROOT)), 'source': str(source.relative_to(ROOT)),
                      'bytes': destination.stat().st_size, 'sha256': digest(destination),
                      'zip_crc_ok': True, 'zip_entries': entry_count, 'class_entries': len(classes),
                      'class_file_major_versions': major_versions,
                      'scope': 'compiled JVM class files; no DEX, ART execution, Android image or RK3229 boot proof'})
(PACKAGE / 'java-artifacts.json').write_text(json.dumps(artifacts, indent=2) + '\n')

last = sorted((ROOT / 'evidence').glob('attempt-*.log'))[-1]
text = last.read_text(errors='replace')
errors = [line for line in text.splitlines() if 'No rule to make target' in line or 'error:' in line]
summary = {'frozen_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'scope': 'bounded genuine Android make droid attempt on incomplete source checkout',
           'baseline_vortex_commit': 'ba4afebe58e9c9cb8fd2a05dc88d142ce1b5e8fe',
           'current_main_gap': 'Main 1db0c914fda74419be097b36c1e753296bcc2bbc additionally requires private native VortexTV APK and OEM catalog-access input; neither is available here. Baseline experiment intentionally did not replace them with dummy inputs.',
           'last_attempt': last.name, 'last_errors': errors[-10:],
           'last_log_sha256': digest(last),
           'object_files_in_output': sum(1 for p in (ROOT / 'out').rglob('*.o') if p.is_file()),
           'host_object_files_in_output': sum(1 for p in (ROOT / 'out/host').rglob('*.o') if p.is_file()),
           'target_object_files_in_output': sum(1 for p in (ROOT / 'out/target').rglob('*.o') if p.is_file()),
           'native_host_aidl_linked': (ROOT / 'out/host/linux-x86/bin/aidl').is_file(),
           'free_bytes_at_freeze': shutil.disk_usage(ROOT).free,
           'source_reserve_bytes': int(3.5 * 1024**3),
           'complete_android_build': False, 'full_source_lock': False,
           'boot_or_system_image_generated': False, 'physical_target_touched': False,
           'github_actions_used': False, 'artifacts': artifacts,
           'large_logs': large}
(PACKAGE / 'checkpoint.json').write_text(json.dumps(summary, indent=2) + '\n')
(PACKAGE / 'README.md').write_text('''# Bounded whole-platform attempt\n\nThese files preserve genuine Android make/envsetup/lunch evidence on an incomplete source tree. They do not establish complete platform dependency closure, a ROM, an SD boot image or board compatibility. The final make stop is recorded in checkpoint.json. All attempts are retained, including failures. The build baseline is historical Vortex ba4afebe; current main additionally needs unavailable private native APK and OEM catalog-access inputs.\n\nThe official r6 Bison i386 prebuilt could not execute on this host. An unchanged r6 external/bison Android.mk built native GNU Bison 2.7, selected through the supported BISON override. The original prebuilt remains unchanged. Genuine historical SDK stubs/ASM5 are host build inputs, not substitute target-platform library providers.\n\nSmall raw logs and metadata are here. Files exceeding 250 KiB are indexed in large-raw-files.json and retained outside Git for the component archive. Git-source-checkouts.json records materialized repositories only; reused source trees and fragments are documented in recipes/ and acquisition metadata, not asserted to be a full repo manifest. Java artifacts contain JVM classes only; no DEX/ART execution is claimed.\n''')
entries = []
for path in sorted(PACKAGE.rglob('*')):
    if path.is_file():
        entries.append(f'{digest(path)}  {path.relative_to(PACKAGE)}\n')
(PACKAGE / 'evidence.sha256').write_text(''.join(entries))
handoff = {'evidence_package': str(PACKAGE), 'files_excluding_manifest': len(entries),
           'evidence_manifest_sha256': digest(PACKAGE / 'evidence.sha256'),
           'checkpoint': summary, 'artifacts': artifacts}
(ROOT / 'handoff.json').write_text(json.dumps(handoff, indent=2) + '\n')
print(json.dumps(handoff, indent=2))
