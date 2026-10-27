#!/usr/bin/env python3
"""Recheck this evidence snapshot and local final outputs; no build/boot approval."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[2]
WORK = Path('/workspace/build01-product-next')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root, name):
    rows = (root / name).read_text().splitlines()
    for row in rows:
        expected, relative = row.split('  ', 1)
        assert sha(root / relative) == expected, relative
    return len(rows)


def main():
    native = EVIDENCE / 'native-rules'
    result = {'scope': 'evidence_and_local_artifacts_only', 'checks': {}}
    checks = result['checks']
    checks['native_manifest_files'] = manifest(native, 'evidence.sha256')
    audit = json.loads((EVIDENCE / 'product-input-audit.json').read_text())
    assert audit['status'] == 'product_inputs_only'
    assert audit['package_counts'] == {'entries': 416, 'unique': 412}
    assert audit['copy_counts'] == {'entries': 13, 'unique_destinations': 13}
    checks['product_input_audit'] = audit['status']
    for name in ('packages', 'copy-files', 'properties'):
        graph = EVIDENCE / 'product-graph/evidence'
        assert (graph / ('baseline-05-' + name + '.list')).read_bytes() == (
            graph / 'rk322x_box' / (name + '.list')).read_bytes(), name
    checks['stock_lists_byte_identical'] = 3
    replay = json.loads((EVIDENCE / 'source-replay/source-replay.json').read_text())
    assert replay['pass']
    checks['replayed_files'] = sum(p['files_compared'] for p in replay['projects'])
    assert checks['replayed_files'] == 1615
    testlog = (EVIDENCE / 'regression-tests.log').read_text()
    assert re.search(r'Ran 130 tests in [0-9.]+s\s+OK\s*$', testlog)
    assert 'skipped' not in testlog
    checks['regression_tests_without_skips'] = 130
    for source, expected in (
        ('tools/audit_product_inputs.py', 'd257a32932e32cb053ba8bd50ff675729cdc2a2ad16ad866bbe8df23e713c3c9'),
        ('tests/test_product_inputs.py', '3729027c1d878e16a1fb8f5e65a96c9f060e6f83069b61b91936f36420ecbb75'),
    ):
        assert sha(REPO / source) == expected, source
    checks['auditor_reviewed_bytes'] = True
    artifacts = {
        'gralloc.rk30board.so': (30368, 'ad9df6102d59dc1e0f91fabff5dd6a0357a5b531285842e4a7ec351a1492c9ed'),
        'hwcomposer.rk30board.so': (83736, 'f6c6651d4b31a1400289117c017a1e45cee389bb6a060375783817e726f32fbf'),
    }
    for name, (size, expected) in artifacts.items():
        path = WORK / 'native-rules/artifacts' / name
        assert path.stat().st_size == size and sha(path) == expected, name
    checks['local_final_hal_artifacts'] = 2
    for p in (REPO / 'rom/product/rk322x_sd_box').rglob('*'):
        if p.is_file():
            relative = p.relative_to(REPO / 'rom/product/rk322x_sd_box')
            for target in ('profile/rk322x_sd_box', 'product-graph/tree/device/vortex/rk322x_sd_box'):
                assert p.read_bytes() == (WORK / target / relative).read_bytes(), str(relative)
    checks['profile_matches_examined_tree'] = True
    assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'app'], cwd=REPO)
    checks['app_unchanged'] = True
    subprocess.run(['git', 'diff', '--check'], cwd=REPO, check=True)
    checks['git_diff_check'] = 'pass'
    checks['new_file_local_links'] = 'pass'
    for name in ('README.md', 'docs/WORK_MODE_HANDOFF.md',
                 'docs/VALIDATION_2026-10-27_PRODUCT.md', 'rom/product/README.md',
                 'rom/platform-reference/graphics/README.md',
                 'docs/validation/2026-10-27-product/README.md'):
        p = REPO / name
        for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            if not link.startswith(('http:', 'https:', '#', 'mailto:')):
                assert (p.parent / link.split('#')[0]).exists(), (name, link)
    result['status'] = 'pass'
    result['rom_build_validation'] = 'not_performed'
    result['physical_boot_validation'] = 'not_performed'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
