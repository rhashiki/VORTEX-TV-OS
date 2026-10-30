"""Acquire the real pinned AOSP r6 host toolchain under a strict disk budget."""
from pathlib import Path
import hashlib
import json
import os
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'evidence'
PIN = '73ca99196723f810dad42390d154654354f57c16'
REPOSITORY = 'https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8'
URL = REPOSITORY + '/+archive/' + PIN + '.tar.gz'
ARCHIVE = ROOT / 'host-gcc48-r6.tar.gz'
MIRROR = ROOT / 'tree'
DESTINATION = MIRROR / 'prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8'
BIONIC_SOURCE = Path('/workspace/build01-platform-next/research/rockchip-bionic/libc/include/stdatomic.h')
ARCHIVE_SHA256 = '78ef70ce6a6af1b0f07cb63430bea28102aaa294075b61dcd7817f577087c541'
EXTERNAL_LINK = ('sysroot/usr/include/stdatomic.h', '../../../../../../../../bionic/libc/include/stdatomic.h')
MAX_ARCHIVE = 150 * 1024 * 1024
MAX_TOTAL = 400 * 1024 * 1024


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


if not ARCHIVE.exists():
    total = 0
    temporary = ARCHIVE.with_suffix('.partial')
    try:
        with urllib.request.urlopen(URL, timeout=80) as source, temporary.open('wb') as output:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ARCHIVE:
                    raise RuntimeError('Archive exceeds bounded acquisition budget')
                output.write(chunk)
        temporary.rename(ARCHIVE)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

assert ARCHIVE.stat().st_size <= MAX_ARCHIVE
assert sha(ARCHIVE) == ARCHIVE_SHA256, 'Cached pinned archive changed'
with tarfile.open(ARCHIVE, 'r:gz') as archive:
    members = archive.getmembers()
    payload_size = sum(member.size for member in members if member.isfile())
    summary = {'repository': REPOSITORY, 'revision': PIN, 'tag': 'android-7.1.2_r6',
               'url': URL, 'archive_bytes': ARCHIVE.stat().st_size, 'archive_sha256': sha(ARCHIVE),
               'regular_payload_bytes': payload_size, 'members': len(members),
               'combined_archive_and_payload_bytes': ARCHIVE.stat().st_size + payload_size,
               'budget_bytes': MAX_TOTAL}
    (EVIDENCE / 'archive-inventory.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)
    assert summary['combined_archive_and_payload_bytes'] <= MAX_TOTAL, 'Whole toolchain exceeds budget; no extraction performed'
    base = DESTINATION.absolute()
    mirror_base = MIRROR.absolute()
    if DESTINATION.exists():
        raise RuntimeError('Extraction destination already exists; inspect rather than overwrite it')
    names = set()
    links = []
    for member in members:
        name = member.name.rstrip('/')
        assert name and not name.startswith('/') and '\\' not in name
        assert all(p not in ('', '.', '..') for p in name.split('/')), member.name
        assert name not in names, member.name
        names.add(name)
        path = Path(os.path.normpath(str(DESTINATION / name)))
        assert path == base or base in path.parents, member.name
        assert member.isdir() or member.isfile() or member.issym() or member.islnk(), member.name
        if member.issym():
            assert not member.linkname.startswith('/')
            target = Path(os.path.normpath(str(path.parent / member.linkname)))
            if not (target == base or base in target.parents):
                assert (name, member.linkname) == EXTERNAL_LINK, (name, member.linkname)
                assert target == MIRROR / 'bionic/libc/include/stdatomic.h'
            assert target == mirror_base or mirror_base in target.parents
            links.append(member)
        elif member.islnk():
            target = Path(os.path.normpath(str(DESTINATION / member.linkname)))
            assert target == base or base in target.parents, (member.name, member.linkname)
    # None of the archive paths may be a child of a symlink member.
    link_names = {m.name.rstrip('/') for m in links}
    for name in names:
        assert not any(parent in link_names for parent in [str(p) for p in Path(name).parents if str(p) != '.']), name
    assert not MIRROR.exists(), 'Use a fresh task-owned mirror to avoid following existing paths'
    DESTINATION.mkdir(parents=True)
    archive.extractall(DESTINATION, members=[m for m in members if not m.issym()], filter='data')
    # Preserve the exact upstream cross-project link. Supply only the genuine
    # selected Bionic header at its normal AOSP path; do not rewrite the link.
    bionic_target = MIRROR / 'bionic/libc/include/stdatomic.h'
    bionic_target.parent.mkdir(parents=True)
    bionic_target.write_bytes(BIONIC_SOURCE.read_bytes())
    os.chmod(bionic_target, 0o644)
    for member in links:
        path = DESTINATION / member.name
        path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(member.linkname, path)
    # Resolve the completed graph only after all symlinks are present. Existing
    # targets stay inside the mirror; upstream optional unresolved links remain
    # unchanged and are explicitly recorded rather than replaced.
    link_records = []
    for member in links:
        path = DESTINATION / member.name
        try:
            target = path.resolve(strict=True)
            assert target == mirror_base or mirror_base in target.parents, member.name
            resolution = {'status': 'resolved_within_mirror', 'target': str(target)}
        except RuntimeError:
            # This exact pinned sysroot ships optional self-referential host
            # library links. Preserve them; do not supply another host ABI.
            assert member.name.startswith(('sysroot/usr/lib/', 'sysroot/usr/lib32/'))
            assert member.linkname == Path(member.name).name
            resolution = {'status': 'preserved_upstream_self_reference', 'target': None}
        except FileNotFoundError:
            target = path.resolve(strict=False)
            assert target == mirror_base or mirror_base in target.parents, member.name
            resolution = {'status': 'preserved_upstream_dangling_reference', 'target': str(target)}
        link_records.append({'path': member.name, 'link_target': os.readlink(path),
                             'resolution': resolution,
                             'cross_project': (member.name, member.linkname) == EXTERNAL_LINK})
    (EVIDENCE / 'extracted-symlinks.json').write_text(json.dumps(link_records, indent=2) + '\n')
    (EVIDENCE / 'bionic-header-provenance.json').write_text(json.dumps({
        'source': str(BIONIC_SOURCE),
        'source_revision': '8b2e5b977118ebb8447cdf429c4a6be534c4fd1b',
        'repository': 'https://github.com/rockchip-android/bionic',
        'mirror_path': str(bionic_target),
        'sha256': sha(bionic_target),
        'bytes': bionic_target.stat().st_size,
        'upstream_symlink_preserved': list(EXTERNAL_LINK),
        'scope': 'Exact selected Bionic header fulfills the toolchain cross-project path; no fabricated or Debian header alias.'
    }, indent=2) + '\n')
print('Extracted genuine toolchain in an isolated AOSP-layout mirror without altering existing prebuilts.', flush=True)
