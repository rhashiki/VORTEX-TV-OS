"""Acquire only genuine pinned r6 update-engine binder definitions, with blob verification."""
from pathlib import Path
import base64
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = 'https://android.googlesource.com/platform/system/update_engine'
TAG = 'android-7.1.2_r6'
LIMIT = 1024 * 1024


def get(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        value = response.read(LIMIT + 1)
    assert len(value) <= LIMIT
    return value


def metadata(url):
    return json.loads(get(url).decode().split('\n', 1)[1])


revision = metadata(REPO + '/+/' + TAG + '?format=JSON')['commit']
files = []


def visit(path):
    listing = metadata(REPO + '/+/' + revision + '/' + path + '?format=JSON')
    for entry in listing['entries']:
        name = path + '/' + entry['name']
        if entry['type'] == 'tree':
            visit(name)
            continue
        assert entry['type'] == 'blob' and entry['mode'] == 33188
        url = REPO + '/+/' + revision + '/' + name + '?format=TEXT'
        data = base64.b64decode(get(url), validate=True)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert blob == entry['id']
        target = ROOT / 'tree/system/update_engine' / name
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o644)
        files.append({'path': name, 'bytes': len(data), 'git_blob': blob,
                      'sha256': hashlib.sha256(data).hexdigest(), 'url': url})


visit('binder_bindings')
(ROOT / 'evidence/update-engine-aidl-acquisition.json').write_text(json.dumps({
    'repository': REPO, 'tag': TAG, 'revision': revision,
    'scope': 'binder_bindings only; not a complete source checkout or module registration',
    'files': files}, indent=2) + '\n')
print(revision, len(files), sum(item['bytes'] for item in files))
