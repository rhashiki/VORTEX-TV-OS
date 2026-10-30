#!/usr/bin/env python3
"""Check pinned source inputs, or explicitly prepare and build a candidate Android.

Default mode never sources BSP scripts or changes the BSP. --run applies the
reviewed patch plan, materializes the product and invokes envsetup/lunch/make.
It does not download sources, install host packages, flash or mount devices.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PRODUCT = 'vortex_rk322x_sd_box'
DESTINATION = 'device/vortex/' + PRODUCT
MAX_INPUT = 4 * 1024 * 1024
MAX_TRACKED_BLOB = 1024 * 1024 * 1024


class Blocked(Exception):
    pass


def run(argv, cwd=None):
    argv = [str(x) for x in argv]
    if argv and argv[0] == 'git':
        args = argv[1:]
        if args and args[0] in ('diff', 'show'):
            args[1:1] = ['--no-ext-diff', '--no-textconv']
        argv = ['git', '--no-pager', '--no-optional-locks', '--no-replace-objects',
                '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', *args]
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=60)
    if p.returncode:
        raise Blocked('Command failed: ' + str(argv[:3]) + ': ' + p.stderr.decode('utf-8', 'replace')[-1500:])
    return p.stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path, limit=MAX_INPUT):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise Blocked('Expected a regular file, not a symlink: ' + str(path))
    if before.st_size > limit:
        raise Blocked('Input exceeds bounded size: ' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise Blocked('Input changed before inspection: ' + str(path))
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        if len(data) > limit or (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise Blocked('Input changed during inspection: ' + str(path))
        return data


def relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or '\x00' in value
            or any(x in ('', '.', '..') for x in value.split('/'))
            or PurePosixPath(value).is_absolute()):
        raise Blocked('Noncanonical relative path: ' + repr(value))
    return value


def inside(root, name):
    p = root / relative(name)
    if not p.resolve().is_relative_to(root.resolve()):
        raise Blocked('Path escapes its root: ' + name)
    return p


def snapshot(root, paths):
    result = {}
    for name in paths:
        p = inside(root, name)
        if not p.exists() and not p.is_symlink():
            result[name] = None
        else:
            data = read_regular(p)
            result[name] = {'sha256': digest(data), 'mode': '100755' if p.stat().st_mode & stat.S_IXUSR else '100644'}
    return result


def patch_paths(patch):
    data = read_regular(patch)
    if b'GIT binary patch' in data or b'Binary files ' in data:
        raise Blocked('Binary source patches are outside this driver contract')
    records = run(['git', 'apply', '--numstat', '-z', '--', patch]).split(b'\0')
    result = []
    for row in records:
        if row:
            parts = row.split(b'\t', 2)
            if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
                raise Blocked('Unsupported rename/binary patch record')
            result.append(relative(parts[2].decode('utf-8')))
    if not result:
        raise Blocked('Empty patch: ' + str(patch))
    return result


def verify_untouched_tracked(project, patched_paths):
    """Compare raw worktree bytes without Git worktree diff or clean filters."""
    count = 0
    for record in run(['git', 'ls-tree', '-r', '-z', 'HEAD'], project).split(b'\0'):
        if not record:
            continue
        metadata, raw_name = record.split(b'\t', 1)
        mode, kind, expected = metadata.split()
        name = relative(raw_name.decode('utf-8'))
        if name in patched_paths:
            continue
        p = project / name
        before = p.lstat()
        if mode == b'120000' and kind == b'blob':
            if not stat.S_ISLNK(before.st_mode):
                raise Blocked('Tracked symlink type changed: ' + name)
            data = os.fsencode(os.readlink(p))
            actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        elif mode in (b'100644', b'100755') and kind == b'blob':
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_TRACKED_BLOB:
                raise Blocked('Nonregular or oversized tracked input: ' + name)
            observed_mode = b'100755' if before.st_mode & stat.S_IXUSR else b'100644'
            if mode != observed_mode:
                raise Blocked('Tracked executable mode changed: ' + name)
            flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
            hasher = hashlib.sha1(b'blob ' + str(before.st_size).encode() + b'\0')
            with os.fdopen(os.open(p, flags), 'rb') as stream:
                opened = os.fstat(stream.fileno())
                if (not stat.S_ISREG(opened.st_mode)
                        or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
                    raise Blocked('Tracked input changed before inspection: ' + name)
                consumed = 0
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    consumed += len(block)
                    if consumed > MAX_TRACKED_BLOB:
                        raise Blocked('Tracked input exceeds bounded limit: ' + name)
                    hasher.update(block)
                after = os.fstat(stream.fileno())
                if (consumed != before.st_size
                        or (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns)):
                    raise Blocked('Tracked input changed during inspection: ' + name)
            actual = hasher.hexdigest()
        else:
            raise Blocked('Unsupported tracked object type: ' + name)
        if actual != expected.decode():
            raise Blocked('Raw tracked bytes differ outside named patches: ' + name)
        count += 1
    return count


def verify_project(project, revision, patches, generated=()):
    """Accept exactly pristine or a verified prefix of the named patch stack."""
    project = project.resolve()
    top = Path(run(['git', 'rev-parse', '--show-toplevel'], project).decode().strip()).resolve()
    if top != project:
        raise Blocked('Project is not its own Git worktree: ' + str(project))
    head = run(['git', 'rev-parse', 'HEAD'], project).decode().strip()
    if head != revision:
        raise Blocked('Wrong pinned HEAD at ' + str(project) + ': ' + head)
    if run(['git', 'diff', '--cached', '--name-only', '-z'], project):
        raise Blocked('Staged changes are not accepted: ' + str(project))
    flags = run(['git', 'ls-files', '-v', '-z'], project).split(b'\0')
    if any(row and (row[:1].islower() or row.startswith(b'S ')) for row in flags):
        raise Blocked('Assume-unchanged/skip-worktree files hide source state: ' + str(project))
    paths = sorted({name for patch in patches for name in patch_paths(patch)})
    untouched_count = verify_untouched_tracked(project, set(paths))
    unknown = set(filter(None, run(['git', 'ls-files', '--others', '--exclude-standard', '-z'], project).decode().split('\0')))
    if unknown - set(paths) - set(generated):
        raise Blocked('Untracked source inputs: ' + ', '.join(sorted(unknown - set(paths) - set(generated))[:10]))
    ignored = run(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', '-z'], project).decode().split('\0')
    if any(Path(p).name in ('Android.mk', 'Android.bp', 'AndroidProducts.mk') for p in ignored):
        raise Blocked('Ignored untracked build definitions: ' + str(project))
    states = []
    with tempfile.TemporaryDirectory(prefix='vortex-patch-check-') as temp:
        scratch = Path(temp)
        for name in paths:
            listing = run(['git', 'ls-tree', '-z', 'HEAD', '--', name], project)
            if listing:
                mode = listing.split(b' ', 1)[0].decode()
                if mode not in ('100644', '100755'):
                    raise Blocked('Patch touches a nonregular tracked object: ' + name)
                p = inside(scratch, name)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(run(['git', 'show', 'HEAD:' + name], project))
                p.chmod(0o755 if mode == '100755' else 0o644)
        states.append(snapshot(scratch, paths))
        for patch in patches:
            run(['git', 'apply', '--check', '--', patch], scratch)
            run(['git', 'apply', '--', patch], scratch)
            states.append(snapshot(scratch, paths))
    actual = snapshot(project, paths)
    matches = [i for i, state in enumerate(states) if state == actual]
    if not matches:
        raise Blocked('Source bytes do not match a pristine/fully applied patch prefix: ' + str(project))
    observed_generated = {}
    for name in generated:
        p = inside(project, name)
        if p.exists() or p.is_symlink():
            observed_generated[name] = {'sha256': digest(read_regular(p)), 'size_bytes': p.stat().st_size}
    return {'revision': head, 'applied_prefix': max(matches), 'patch_count': len(patches),
            'patches': [{'path': str(p), 'sha256': digest(read_regular(p))} for p in patches],
            'expected_final_files': states[-1], 'observed_generated_inputs': observed_generated,
            'untouched_tracked_files_raw_verified': untouched_count,
            'generated_input_origin': 'declared exception; content inventoried, generation is not authenticated'}


def profile_files(source):
    files = {}
    if source.is_symlink() or not source.is_dir():
        raise Blocked('Product template directory is absent')
    for p in source.rglob('*'):
        if p.is_symlink():
            raise Blocked('Symlink in product template: ' + str(p))
        if p.is_dir():
            continue
        if p.is_file():
            files[str(p.relative_to(source))] = read_regular(p)
        else:
            raise Blocked('Special file in product template: ' + str(p))
    if not files or len(files) > 64:
        raise Blocked('Missing or oversized product template')
    guard = ('ifeq ($(LOCAL_DIR),' + DESTINATION + ')').encode()
    if guard not in files.get('AndroidProducts.mk', b''):
        raise Blocked('AndroidProducts.mk does not guard the materialized product path')
    mk = files.get(PRODUCT + '.mk', b'')
    if not re.search(rb'^PRODUCT_DEVICE\s*:=\s*vortex_rk322x_sd_box\s*$', mk, re.M):
        raise Blocked('PRODUCT_DEVICE differs from materialized directory')
    if b'device/vortex/rk322x_sd_box' in mk:
        raise Blocked('Old product-directory prefix remains')
    return files


def verify_profile_destination(destination, files):
    if destination.is_symlink():
        raise Blocked('Symlink at product destination')
    if not destination.exists():
        return 'absent'
    if not destination.is_dir():
        raise Blocked('Existing product destination is not a directory')
    actual = {}
    for p in destination.rglob('*'):
        if p.is_symlink():
            raise Blocked('Symlink in existing product destination')
        if p.is_dir():
            continue
        if p.is_file():
            actual[str(p.relative_to(destination))] = read_regular(p)
        else:
            raise Blocked('Special file in existing product destination: ' + str(p))
    if actual and actual != files:
        raise Blocked('Existing product destination differs; it will not be overwritten')
    return 'identical' if actual else 'empty'


def existing_parent(path):
    while not path.exists():
        path = path.parent
    return path


BUILD_SHELL = r'''
set -eo pipefail
cd "$1"
export JAVA_HOME="$2"
export PATH="$6:$JAVA_HOME/bin:$PATH"
export OUT_DIR="$3"
export USE_NINJA=false USE_SOONG=false
export JACK_SERVER=false
export JACK_HOME="$3/jack-home"
export CLIENT_SETTING="$3/jack-client-settings"
unset ONE_SHOT_MAKEFILE TARGET_BUILD_APPS TARGET_BUILD_PDK PDK_FUSION_PLATFORM_ZIP
unset TARGET_CRTBEGIN_SO_O TARGET_CRTEND_SO_O TARGET_CRTBEGIN_STATIC_O TARGET_CRTBEGIN_DYNAMIC_O TARGET_CRTEND_O
unset TARGET_TOOLS_PREFIX TARGET_PREBUILT_KERNEL ACP USE_CLANG_PLATFORM_BUILD
unset ANDROID_BUILD_TOP ANDROID_PRODUCT_OUT ANDROID_HOST_OUT
if [ -n "$5" ]; then export VORTEX_REFERENCE_KERNEL_IMAGE="$5"; else unset VORTEX_REFERENCE_KERNEL_IMAGE; fi
source build/envsetup.sh
lunch vortex_rk322x_sd_box-eng
make -j"$4" droid
'''


def preflight(args):
    bsp = args.bsp_root.resolve(strict=True)
    control = args.vortex_root.resolve(strict=True)
    if control.is_relative_to(bsp):
        raise Blocked('--vortex-root must be a separate updated control checkout outside the BSP')
    overlay = inside(control, 'rom/platform-reference/vortex-r6-rockchip-experimental.xml')
    document = ET.fromstring(read_regular(overlay))
    projects = {}
    names = set()
    for element in document.findall('project'):
        name = element.get('name')
        path = relative(element.get('path'))
        revision = element.get('revision', '')
        if not name or name in names or path in projects or not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise Blocked('Critical overlay projects need unique names/paths and full commit SHAs')
        projects[path] = revision
        names.add(name)
    if document.tag != 'manifest' or not projects:
        raise Blocked('Expected a nonempty explicit critical-project overlay')
    plan_path = args.patch_plan or control / 'rom/product/full-platform-patches.json'
    plan = json.loads(read_regular(plan_path))
    if plan.get('schema_version') != 1 or not isinstance(plan.get('projects'), dict):
        raise Blocked('Unsupported patch-plan schema')
    if set(plan['projects']) - set(projects):
        raise Blocked('Patch plan names a project absent from the pinned overlay')
    specs = {}
    checks = {}
    errors = []
    for name, revision in projects.items():
        p = inside(bsp, name)
        entry = plan['projects'].get(name, {})
        if (not isinstance(entry, dict) or set(entry) - {'patches', 'generated_untracked'}
                or not isinstance(entry.get('patches', []), list)
                or not isinstance(entry.get('generated_untracked', []), list)):
            raise Blocked('Unsupported patch-plan project entry: ' + name)
        patches = [inside(control, relative(x)).resolve() for x in entry.get('patches', [])]
        generated = [relative(x) for x in entry.get('generated_untracked', [])]
        if any(Path(x).name in ('Android.mk', 'Android.bp', 'AndroidProducts.mk') for x in generated):
            raise Blocked('Generated exceptions cannot name build definitions')
        specs[name] = (revision, patches, generated)
        try:
            checks[name] = verify_project(p, revision, patches, generated)
        except (Blocked, OSError, subprocess.SubprocessError) as error:
            errors.append(name + ': ' + str(error))
    files = profile_files(inside(control, 'rom/product/rk322x_sd_box'))
    destination = inside(bsp, DESTINATION)
    profile_state = verify_profile_destination(destination, files)
    if (bsp / 'vendor/vortex/reference-libraries/Android.mk').exists():
        errors.append('The old reference-library experiment is present; this driver requires source platform providers')
    out = (args.out_dir or bsp / 'out-vortex-platform').resolve()
    if out.exists() and not out.is_dir():
        raise Blocked('Existing output path is not a directory')
    marker = out / 'vortex-full-build-inputs.json'
    identity = {'projects': projects, 'patches': {n: [{'path':str(p.relative_to(control)), 'sha256':digest(read_regular(p))} for p in v[1]] for n,v in specs.items()},
                'profile': {n:digest(v) for n,v in files.items()}}
    for base in [control, destination] + [inside(bsp, n) for n in projects]:
        if out == base.resolve() or out.is_relative_to(base.resolve()):
            errors.append('Output directory overlaps source inputs: ' + str(out))
    available = shutil.disk_usage(existing_parent(out)).free
    if available < args.min_free_gib * 2**30:
        errors.append('Available bytes %s below configured operational reserve %s GiB (not a proven AOSP minimum)' % (available,args.min_free_gib))
    java = args.jdk_home.resolve(strict=True)
    version = subprocess.run([str(java/'bin/java'),'-version'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
    java_text = (version.stdout + version.stderr).decode('utf-8', 'replace')
    compiler = subprocess.run([str(java/'bin/javac'),'-version'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
    javac_text = (compiler.stdout + compiler.stderr).decode('utf-8', 'replace')
    if (version.returncode or compiler.returncode or not re.search(r'version "1\.8\.', java_text)
            or not re.search(r'javac 1\.8\.', javac_text)):
        errors.append('An actual JDK8 with javac is required')
    python2 = (args.python2 or Path(shutil.which('python2.7') or shutil.which('python2') or '/nonexistent-python2')).resolve()
    try:
        py = subprocess.run([str(python2),'--version'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        if py.returncode or b'Python 2.7.' not in py.stdout + py.stderr:
            errors.append('A Python2.7 host executable is required')
    except OSError:
        errors.append('A Python2.7 host executable is required')
    if args.kernel_image:
        data = read_regular(args.kernel_image.resolve(), 64*1024*1024)
        if not data: errors.append('Kernel override is empty')
        identity['kernel_override'] = {'path': str(args.kernel_image.resolve()), 'sha256': digest(data), 'size_bytes': len(data)}
    else:
        identity['kernel_override'] = None
    identity['host_tool_selectors'] = {'jdk_home': str(java), 'java_version': java_text.strip(),
                                       'javac_version': javac_text.strip(), 'python2': str(python2)}
    if out.is_dir() and any(out.iterdir()):
        if not marker.is_file() or json.loads(read_regular(marker)) != identity:
            errors.append('Output input marker differs after host/kernel selection; choose a new output')
    report = {'scope':'pinned_inputs_only_not_module_closure_or_boot_approval',
              'status':'blocked' if errors else 'ready_for_candidate_build',
              'bsp_root':str(bsp),'control_root':str(control),'critical_projects':checks,
              'profile_destination':str(destination),'profile_state':profile_state,
              'out_dir':str(out),'available_bytes':available,'configured_reserve_gib':args.min_free_gib,
              'reserve_is_not_measured_platform_requirement':True,'jobs':args.jobs,
              'jdk_version':java_text.strip(), 'javac_version':javac_text.strip(),
              'kernel_override': identity['kernel_override'], 'errors':errors,
              'limits':['Only explicit overlay pins are validated; other AOSP projects are not authenticated by this preflight.',
                        'Declared generated headers are inventoried, not authenticated; other ignored generated artifacts are outside this contract.',
                        'Actual source module closure is decided by the genuine platform build, not this script.',
                        'No driver, complete image, SD media or physical compatibility is approved.']}
    return report, (bsp,control,specs,files,destination,out,identity,java,python2)


def execute(args, context, report):
    bsp,control,specs,files,destination,out,identity,java,python2 = context
    logs = (args.log_dir or bsp.parent / ('vortex-platform-logs-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))).resolve()
    if logs.exists(): raise Blocked('Log directory already exists; choose a new --log-dir')
    if (logs.is_relative_to(control) or logs.is_relative_to(destination.resolve())
            or any(logs.is_relative_to(inside(bsp,n).resolve()) for n in specs)):
        raise Blocked('Log directory must not overlap source projects')
    # Repeat all checks before the first mutation; preflight is not a lock.
    for name,(revision,patches,generated) in specs.items():
        verify_project(inside(bsp,name),revision,patches,generated)
    verify_profile_destination(destination,files)
    logs.mkdir(parents=True)
    (logs/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,(revision,patches,generated) in specs.items():
        p=inside(bsp,name)
        state=verify_project(p,revision,patches,generated)
        for patch in patches[state['applied_prefix']:]:
            run(['git','apply','--check','--',patch],p)
            run(['git','apply','--',patch],p)
        verify_project(p,revision,patches,generated)
    verify_profile_destination(destination,files)
    destination.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():
        p=inside(destination,name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    out.mkdir(parents=True,exist_ok=True)
    (out/'vortex-full-build-inputs.json').write_text(json.dumps(identity,indent=2)+'\n')
    host=logs/'host-bin';host.mkdir();(host/'python').symlink_to(python2)
    lock={'status':'not_available','reason':'repo tool or .repo directory absent; no resolved lock fabricated'}
    repo_tool=shutil.which('repo')
    if repo_tool and (bsp/'.repo').is_dir():
        p=subprocess.run([repo_tool,'manifest','-r'],cwd=bsp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
        (logs/'repo-manifest.stderr.log').write_bytes(p.stderr)
        if not p.returncode:
            try:
                tree=ET.fromstring(p.stdout);nodes=tree.findall('project')
                if not nodes or any(not re.fullmatch(r'[0-9a-f]{40}',n.get('revision','')) for n in nodes):raise ValueError('unresolved project revision')
                (logs/'manifest-r.xml').write_bytes(p.stdout)
                lock={'status':'actual_repo_manifest_r','projects':len(nodes),'sha256':digest(p.stdout)}
            except (ValueError,ET.ParseError) as error:lock={'status':'failed','reason':str(error)}
        else:lock={'status':'failed','returncode':p.returncode}
    (logs/'source-lock-status.json').write_text(json.dumps(lock,indent=2)+'\n')
    command=['bash','-c',BUILD_SHELL,'vortex-platform',str(bsp),str(java),str(out),str(args.jobs),str(args.kernel_image.resolve()) if args.kernel_image else '',str(host)]
    (logs/'command.json').write_text(json.dumps({'argv':command,'source_lock':lock,
        'known_reference_experiment_absent':True,'one_shot_and_experimental_crt_overrides_unset':True},indent=2)+'\n')
    with (logs/'build.log').open('wb') as log:
        p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for chunk in iter(lambda:p.stdout.read1(65536),b''):
            log.write(chunk);log.flush();sys.stdout.buffer.write(chunk);sys.stdout.buffer.flush()
        code=p.wait()
    result={'status':'build_command_succeeded' if not code else 'build_command_failed','returncode':code,
            'log_dir':str(logs),'out_dir':str(out),'resolved_source_lock':lock,
            'physical_boot_validation':'not_performed','sd_media_validation':'not_performed',
            'complete_rom_validation':'not_performed'}
    (logs/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return code


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bsp-root',type=Path,required=True)
    p.add_argument('--vortex-root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--jdk-home',type=Path,required=True)
    p.add_argument('--python2',type=Path)
    p.add_argument('--patch-plan',type=Path)
    p.add_argument('--out-dir',type=Path)
    p.add_argument('--log-dir',type=Path)
    p.add_argument('--kernel-image',type=Path)
    p.add_argument('--jobs',type=int,choices=(1,2),default=1)
    p.add_argument('--min-free-gib',type=float,default=10.0,help='Operational reserve, not a measured minimum for full AOSP')
    p.add_argument('--run',action='store_true',help='Apply verified source patches and invoke the actual complete-product droid target')
    args=p.parse_args(argv)
    if not 0 <= args.min_free_gib <= 100000: p.error('--min-free-gib must be finite and nonnegative')
    try:
        report,context=preflight(args)
        print(json.dumps(report,indent=2))
        if report['errors']:return 2
        return execute(args,context,report) if args.run else 0
    except (Blocked,OSError,ValueError,KeyError,ET.ParseError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'blocked','scope':'candidate_source_build_only','error':str(error)}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
