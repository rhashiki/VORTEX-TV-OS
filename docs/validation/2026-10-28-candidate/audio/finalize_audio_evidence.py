"""Freeze existing successful audio build outputs without rebuilding them."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
TREE = ROOT / 'tree'
OUT = ROOT / 'out-final/target/product/generic'
EVIDENCE = ROOT / 'evidence'
PACKAGE = ROOT / 'evidence-package'
ARTIFACTS = ROOT / 'artifacts'
EVIDENCE.mkdir(exist_ok=True)
PACKAGE.mkdir(exist_ok=True)
ARTIFACTS.mkdir(exist_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def info(path):
    return {'path': str(path), 'size_bytes': path.stat().st_size, 'sha256': digest(path)}


def command(arguments):
    return subprocess.check_output(arguments, stderr=subprocess.STDOUT)


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


log = (ROOT / 'attempt-08-final-clean.log').read_text()
assert '#### make completed successfully' in log
units = re.findall(r'^target (?:thumb |arm )?(?:C\+\+|C|asm): ([^ ]+) <= (.+)$', log, re.M)
counts = dict(collections.Counter(module for module, source in units))
assert len(units) == 53 and len(counts) == 15, counts
shared_names = ['audio.primary.rk30board', 'audio.usb.default', 'audio.r_submix.default',
                'power.default', 'libtinyalsa', 'libaudioutils', 'libaudioroute',
                'libalsautils', 'libspeexresampler', 'libexpat', 'libnbaio']
hal_names = set(shared_names[:4])
static_names = ['libspeex', 'libmedia_helper', 'libunwind_llvm', 'libcompiler_rt-extras']
assert set(counts) == set(shared_names + static_names)
prefix = TREE / 'prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-'
artifact_rows = []
for module in shared_names:
    relative = Path('system/lib') / ('hw' if module in hal_names else '') / (module + '.so')
    source = OUT / relative
    target = ARTIFACTS / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    elf = command([str(prefix) + 'readelf', '-h', '-l', '-d', '-A', '-n', str(source)]).decode()
    symbols = command([str(prefix) + 'readelf', '--dyn-syms', '--wide', str(source)]).decode()
    (EVIDENCE / (module + '.elf.txt')).write_text(elf)
    (EVIDENCE / (module + '.dynsyms.txt')).write_text(symbols)
    assert 'Class:                             ELF32' in elf and 'Machine:                           ARM' in elf, module
    assert '(TEXTREL)' not in elf, module
    assert 'Tag_ABI_VFP_args: VFP registers' not in elf, module
    if module in hal_names:
        assert re.search(r'GLOBAL\s+DEFAULT\s+\d+\s+HMI\b', symbols), module
    artifact_rows.append({**info(target), 'installed_path': str(source),
                          'kind': 'HAL' if module in hal_names else 'source_shared_dependency',
                          'ELF32_ARM': True, 'hardfloat_calling_convention': False,
                          'TEXTREL': False, 'has_HMI': module in hal_names,
                          'needed': re.findall(r'Shared library: \[([^\]]+)\]', elf)})

for module in static_names:
    source = OUT / 'obj/STATIC_LIBRARIES' / (module + '_intermediates') / (module + '.a')
    target = ARTIFACTS / 'static' / source.name
    target.parent.mkdir(exist_ok=True)
    shutil.copyfile(source, target)
    artifact_rows.append({**info(target), 'installed_path': None, 'kind': 'source_static_archive'})

smoke = json.loads((ROOT / 'loader/evidence/loader-smoke-result.json').read_text())
assert smoke['status'] == 'pass' and len(smoke['checks']) == 8
for name, row in smoke['modules'].items():
    assert digest(OUT / 'system/lib/hw' / name) == row['sha256']
for row in smoke['inputs']:
    assert digest(Path(row['path'])) == row['sha256']
regression = json.loads((ROOT / 'rate-regression/regression-result.json').read_text())
assert regression['status'] == 'pass'
assert [(x['passed'], x['failed']) for x in regression['checks']] == [(10, 1), (11, 0)]

# Compiler-generated input coverage, not a complete Android source lock.
dependencies = {}
depdir = EVIDENCE / 'compiler-dependencies'
depdir.mkdir(exist_ok=True)
rules = sorted((OUT / 'obj').rglob('*.P'))
assert len(rules) == 53
for path in rules:
    target = depdir / path.relative_to(OUT / 'obj')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    logical = path.read_text().replace('\\\n', '').splitlines()[0]
    for token in logical.split(':', 1)[1].split():
        source = Path(token)
        if not source.is_absolute():
            source = TREE / source
        assert source.is_file(), str(source)
        dependencies[token] = {**info(source.resolve())}
save_json(EVIDENCE / 'compiler-inputs.json', {
    'scope': 'Observed input files from 53 genuine compiler-generated .P rules; not full BSP closure.',
    'rule_count': len(rules), 'files': dependencies})

# Exact source files in the four-C primary HAL, compared to public pinned repo.
original = Path('/workspace/build01-platform-next/research/rockchip-audio')
pin = command(['git', '-C', str(original), 'rev-parse', 'HEAD']).decode().strip()
assert pin == '03b111b6736b48ec17ffee4906caecf59323d8c1'
primary = TREE / 'hardware/rockchip/audio'
rows = []
for relative in ['Android.mk', 'tinyalsa_hal/Android.mk', 'tinyalsa_hal/audio_hw.c',
                 'tinyalsa_hal/alsa_route.c', 'tinyalsa_hal/alsa_mixer.c', 'tinyalsa_hal/audio_hw_hdmi.c']:
    before = command(['git', '-C', str(original), 'show', pin + ':' + relative])
    after = (primary / relative).read_bytes()
    if relative == 'tinyalsa_hal/audio_hw.c':
        assert before == (ROOT / 'baseline/audio_hw.c').read_bytes()
        expected = before.replace(b'                    out->config = pcm_config;\n                    out->config.rate = 44100;\n                    ALOGE("hdmi bitstream samplerate %d unsupport", config->sample_rate);',
                                  b'                    ALOGE("hdmi bitstream samplerate %d unsupport", config->sample_rate);\n                    ret = -EINVAL;\n                    goto err_open;')
        assert after == expected
    else:
        assert before == after, relative
    rows.append({'path': relative, 'upstream_sha256': hashlib.sha256(before).hexdigest(),
                 'compiled_sha256': hashlib.sha256(after).hexdigest()})
save_json(EVIDENCE / 'primary-source-provenance.json', {'repository': 'https://github.com/rockchip-android/hardware-rockchip-audio',
    'revision': pin, 'patch': '0001-audio-reject-unsupported-hdmi-bypass-rate.patch', 'files': rows})

build_original = Path('/workspace/build01-platform-next/research/rockchip-build')
build_rows = []
for path in sorted((TREE / 'build').rglob('*')):
    if path.is_file() and path.suffix != '.pyc':
        relative = path.relative_to(TREE / 'build')
        original_path = build_original / relative
        assert path.read_bytes() == original_path.read_bytes(), str(relative)
        build_rows.append({'path': str(relative), 'sha256': digest(path)})
save_json(EVIDENCE / 'build-rules-unmodified.json', {'source_revision': 'd2721c65c9282b31df7b79f85289ee6c4e636716',
    'all_build_files_match_pinned_source': True, 'files': build_rows})
warnings = [line for line in log.splitlines() if 'warning:' in line]
save_json(EVIDENCE / 'warnings.json', {'count': len(warnings), 'lines': warnings,
    'scope': 'Warnings retained in the final clean build; no zero-warning or audio-functionality claim.',
    'unresolved_examples': ['Legacy implicit get_route_config declaration and integer-to-pointer conversion.',
        'Pointer/type, format and macro redefinition warnings remain.',
        'Only unsupported HDMI bypass sample-rate uninitialized-enum path is fixed by this patch.']})

save_json(EVIDENCE / 'audio-build-result.json', {
    'scope': 'Genuine Android.mk compile/link/pack/strip/install in a thin reference tree; not a complete source-built BSP.',
    'status': 'pass', 'verified_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'clean_build': {'log': 'attempt-08-final-clean.log', 'script': 'build_audio_final.sh',
        'compilation_units': 53, 'units_by_module': counts,
        'HAL_modules': 4, 'source_shared_dependencies': 7, 'source_static_archives': 4,
        'registered_reference_prebuilt_DSO_modules': 22,
        'actually_processed_prebuilt_modules': sorted(set(re.findall(r'^target Prebuilt: ([^ ]+)', log, re.M)))},
    'toolchains': {'HAL_and_dependency_compiler': 'genuine Android Clang clang-2690385 (3.8), official revision45562a53b2a5eb7c6e8f400413d19a12c660d7b1',
        'linker_and_runtime': 'genuine Android GCC4.9 tools/runtime, revision0390252b6bcc6217966ade31d07f8b12f6f78f89',
        'shared_CRT': 'Reused pinned Bionic source CRT objects from prior reference experiment, compiled softfp with Linaro6.3.1; not source-built by this clean make.',
        'Expat_NDK_interface': 'Genuine Expat Android.mk declares LOCAL_SDK_VERSION=8 for ARM; recorded official NDK API8 sysroot subset provides headers/link interfaces, excluded from delivery.',
        'loader_probe': 'Separately compiled Bionic dynamic CRT and metadata probe with actual Android GCC4.9; see loader/evidence/probe-build.json.'},
    'regression': {'baseline_passed': 10, 'baseline_expected_failures': 1, 'patched_passed': 11,
        'instrumentation': regression['baseline_instrumentation']},
    'loader_smoke': {'cases': 8, 'result': 'pass', 'HAL_open_or_power_hook_invoked': False},
    'warning_count': len(warnings), 'artifacts': artifact_rows,
    'unresolved': ['Reference system DSOs are real API25 binaries, not source-built platform libraries; excluded from delivery.',
        'No audio playback/recording, HDMI/SPDIF/USB/power operation or physical hardware validation.',
        'No complete Android build, Android/recovery/SD image or flash operation.']})

def copy(source, relative):
    target = PACKAGE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


for path in sorted(ROOT.glob('attempt-*.log')):
    copy(path, path.name)
for path in sorted(ROOT.glob('build_audio*.sh')):
    copy(path, path.name)
for name in ['finalize_audio_evidence.py', '0001-audio-reject-unsupported-hdmi-bypass-rate.patch']:
    copy(ROOT / name, name)
shutil.copytree(EVIDENCE, PACKAGE / 'evidence', dirs_exist_ok=True)
for folder in ['loader', 'rate-regression', 'review']:
    for path in sorted((ROOT / folder).rglob('*')):
        if path.is_file() and path.suffix in ('.py', '.c', '.json', '.txt', '.md', '.log', '.d'):
            copy(path, path.relative_to(ROOT))
for path in sorted((ROOT / 'acquisition').glob('*')):
    if path.is_file() and path.suffix in ('.json', '.log'):
        copy(path, path.relative_to(ROOT))
copy(TREE / 'vendor/vortex/reference-libraries/Android.mk', Path('actual-module-definitions/reference-libraries/Android.mk'))
for relative in ['hardware/rockchip/audio/Android.mk', 'hardware/rockchip/audio/tinyalsa_hal/Android.mk',
                 'hardware/libhardware/modules/power/Android.mk', 'hardware/libhardware/modules/usbaudio/Android.mk',
                 'hardware/libhardware/modules/audio_remote_submix/Android.mk', 'external/tinyalsa/Android.mk',
                 'external/speex/Android.mk', 'external/expat/Android.mk', 'system/media/audio_route/Android.mk',
                 'system/media/audio_utils/Android.mk', 'system/media/alsa_utils/Android.mk',
                 'frameworks/av/media/libnbaio/Android.mk', 'frameworks/av/media/libmedia/Android.mk']:
    copy(TREE / relative, Path('actual-module-definitions') / relative)
for relative in ['external/speex/COPYING', 'external/speex/NOTICE', 'external/expat/NOTICE',
                 'external/tinyalsa/NOTICE', 'system/media/NOTICE', 'system/media/audio_route/NOTICE',
                 'frameworks/av/NOTICE']:
    copy(TREE / relative, Path('licenses') / relative)
for relative in ['compiler-rt/LICENSE.TXT', 'compiler-rt/NOTICE', 'libunwind_llvm/LICENSE.TXT',
                 'android-gcc49/COPYING', 'android-gcc49/COPYING3', 'android-gcc49/COPYING.LIB',
                 'android-gcc49/COPYING3.LIB', 'android-gcc49/COPYING.RUNTIME']:
    source = Path('/workspace/build01-product-next/native-rules/evidence-package/licenses') / relative
    if source.is_file():
        copy(source, Path('licenses') / relative)
copy(Path('/usr/share/common-licenses/Apache-2.0'), 'licenses/Apache-2.0')
for relative in ['tinyalsa_hal/audio_hw.c', 'tinyalsa_hal/alsa_route.c', 'tinyalsa_hal/alsa_mixer.c', 'tinyalsa_hal/audio_hw_hdmi.c']:
    text = (primary / relative).read_bytes().split(b'\n')[:28]
    target = PACKAGE / 'licenses' / (Path(relative).name + '.source-header.txt')
    target.write_bytes(b'\n'.join(text) + b'\n')

print(json.dumps({'compilation_units': 53, 'modules': 15, 'shared_artifacts': 11,
    'static_artifacts': 4, 'compiler_dependency_rules': len(rules), 'observed_inputs': len(dependencies),
    'unmodified_build_files': len(build_rows), 'retained_warnings': len(warnings),
    'staged_text_files_before_summary': len([p for p in PACKAGE.rglob('*') if p.is_file()])}, indent=2))
