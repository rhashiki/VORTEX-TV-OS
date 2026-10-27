#!/usr/bin/env python3
"""Read flattened product selections; never execute Android/BSP code."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET

ROOT = Path('/workspace/build01-product-next/product-graph/tree')
OUT = Path('/workspace/build01-product-next/review/raw_inventory')

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

inputs = {}
for name in ('packages', 'copy-files', 'properties'):
    path = ROOT / 'out' / (name + '.list')
    inputs[name] = {'path': str(path), 'bytes': path.stat().st_size,
                    'sha256': sha(path), 'lines': path.read_text().splitlines()}

package_lines = [{'line': n, 'package': value} for n, value in enumerate(inputs['packages']['lines'], 1) if value]
package_counts = Counter(row['package'] for row in package_lines)
source_cache = {}
copy_lines = []
for n, value in enumerate(inputs['copy-files']['lines'], 1):
    if not value:
        continue
    bits = value.split(':')
    if len(bits) not in (2, 3):
        raise ValueError((n, value))
    source, destination = bits[:2]
    if source not in source_cache:
        path = ROOT / source
        regular_file = path.is_file()
        source_cache[source] = {
            'source': source,
            'resolved_absolute_path': str(path.resolve()),
            'is_symlink': path.is_symlink(),
            'exists_following_symlinks': path.exists(),
            'regular_file_following_symlinks': regular_file,
            'sha256': sha(path) if regular_file else None,
            'bytes': path.stat().st_size if regular_file else None,
        }
    copy_lines.append({'line': n, 'entry': value, 'source': source,
                       'destination': destination, 'owner': bits[2] if len(bits) == 3 else None,
                       'normalized_destination': posixpath.normpath(destination.lstrip('/'))})

by_pair = defaultdict(list)
by_destination = defaultdict(list)
by_normalized = defaultdict(list)
for row in copy_lines:
    by_pair[row['entry']].append(row)
    by_destination[row['destination']].append(row)
    by_normalized[row['normalized_destination']].append(row)

def collision(destination, rows):
    sources = list(dict.fromkeys(row['source'] for row in rows))
    hashes = {source: source_cache[source]['sha256'] for source in sources}
    return {'destination': destination, 'lines': [row['line'] for row in rows],
            'sources': sources, 'source_sha256': hashes,
            'all_sources_regular_files': all(source_cache[source]['regular_file_following_symlinks'] for source in sources),
            'different_existing_content': len({value for value in hashes.values() if value is not None}) > 1,
            'first_entry': rows[0]}

literal_conflicts = [collision(dest, rows) for dest, rows in by_destination.items()
                     if len({row['source'] for row in rows}) > 1]
normalized_aliases = [dict(collision(dest, rows), literal_destinations=list(dict.fromkeys(row['destination'] for row in rows)))
                      for dest, rows in by_normalized.items()
                      if len({row['destination'] for row in rows}) > 1]

category_patterns = {
    'launcher': re.compile(r'launcher', re.I),
    'bluetooth_explicit': re.compile(r'bluetooth|bluedroid|bluez|(^|[/_.-])rtkbt([/_.-]|$)|a2dp|(^|[/_.-])bt([/_.-]|$)|\.hcd$', re.I),
    'google_or_gapps_named': re.compile(r'google|gapps|gmscore|phonesky|vending|setupwizard|googleservices|googlelogin|googlepartner', re.I),
    'updater': re.compile(r'update|uncrypt|applypatch', re.I),
    'recovery': re.compile(r'recovery', re.I),
    'factory': re.compile(r'factory|rktest|rftest', re.I),
}
categories = {}
for name, pattern in category_patterns.items():
    categories[name] = {
        'match_rule': pattern.pattern,
        'packages': [row for row in package_lines if pattern.search(row['package'])],
        'copy_files': [row for row in copy_lines if pattern.search(row['source']) or pattern.search(row['destination'])],
        'properties': [{'line': n, 'value': value} for n, value in enumerate(inputs['properties']['lines'], 1) if pattern.search(value)],
    }
# javax.obex is listed separately: selection is factual; its presence alone does not prove a running Bluetooth stack.
categories['bluetooth_related_support'] = {
    'packages': [row for row in package_lines if row['package'] == 'javax.obex'],
    'note': 'Support API selection only; no module dependency or runtime conclusion.'}
categories['factory_related_generic_tools'] = {
    'packages': [row for row in package_lines if row['package'] in {'adb', 'adbd', 'fastboot', 'CtsShimPrebuilt', 'CtsShimPrivPrebuilt', 'android.test.runner'}],
    'note': 'Generic platform/debug/test tools are not evidence that a vendor factory app is selected.'}

# Permission/feature XML may carry a relevant declaration despite a generic filename.
permission_declarations = []
for row in copy_lines:
    if '/permissions/' not in row['destination'] or not row['source'].endswith('.xml') or not source_cache[row['source']]['regular_file_following_symlinks']:
        continue
    path = ROOT / row['source']
    document = ET.parse(path)
    for element in document.iter():
        if any(re.search(r'bluetooth|google', value, re.I) for value in element.attrib.values()):
            permission_declarations.append({'copy_line': row['line'], 'source': row['source'],
                'destination': row['destination'], 'element': element.tag,
                'attributes': dict(element.attrib)})

missing_sources = [dict(status, lines=[row['line'] for row in copy_lines if row['source'] == source],
                        destinations=list(dict.fromkeys(row['destination'] for row in copy_lines if row['source'] == source)))
                   for source, status in source_cache.items() if not status['regular_file_following_symlinks']]
missing_entries = [row for row in copy_lines if not source_cache[row['source']]['regular_file_following_symlinks']]
effective_rows = [rows[0] for rows in by_destination.values()]
missing_effective = [row for row in effective_rows if not source_cache[row['source']]['regular_file_following_symlinks']]

property_pairs = defaultdict(list)
malformed_properties = []
for n, value in enumerate(inputs['properties']['lines'], 1):
    if not value or '=' not in value or not value.split('=', 1)[0]:
        malformed_properties.append({'line': n, 'value': value})
    else:
        key, prop_value = value.split('=', 1)
        property_pairs[key].append({'line': n, 'value': prop_value})

counts = {
    'package_entries': len(package_lines), 'unique_packages': len(package_counts),
    'duplicate_package_entries_beyond_first': sum(count - 1 for count in package_counts.values()),
    'copy_entries': len(copy_lines), 'unique_copy_entry_strings': len(by_pair),
    'exact_duplicate_copy_entries_beyond_first': len(copy_lines) - len(by_pair),
    'unique_literal_destinations': len(by_destination),
    'unique_normalized_destinations': len(by_normalized),
    'leading_slash_destination_entries': sum(row['destination'].startswith('/') for row in copy_lines),
    'literal_destinations_with_multiple_sources': len(literal_conflicts),
    'normalized_destinations_with_multiple_literal_spellings': len(normalized_aliases),
    'unique_copy_sources': len(source_cache),
    'regular_copy_sources_following_symlinks': sum(status['regular_file_following_symlinks'] for status in source_cache.values()),
    'source_symlinks_to_regular_files': sum(status['is_symlink'] and status['regular_file_following_symlinks'] for status in source_cache.values()),
    'missing_or_nonregular_unique_sources': len(missing_sources),
    'missing_or_nonregular_copy_entries': len(missing_entries),
    'missing_or_nonregular_literal_first_sources': len(missing_effective),
    'property_tokens': len(inputs['properties']['lines']),
    'malformed_property_tokens': len(malformed_properties),
}
report = {
    'scope': 'Read-only selection/file audit of already flattened rk322x_box eng product lists in the supplied diagnostic tree. No conditional branch inference, BSP script execution, module dependency closure, build success, ROM approval, or hardware claims.',
    'source_existence_scope': 'Missing means absent/nonregular after resolving symlinks under the supplied product-graph tree; it does not establish absence in a complete Android checkout. All input lists were consumed exactly as present.',
    'inputs': {name: {key: value for key, value in item.items() if key != 'lines'} for name, item in inputs.items()},
    'counts': counts,
    'categories': categories,
    'bluetooth_google_permission_declarations': permission_declarations,
    'packages': package_lines,
    'duplicate_packages': [{'package': name, 'count': count, 'lines': [row['line'] for row in package_lines if row['package'] == name]} for name, count in package_counts.items() if count > 1],
    'copy_files': copy_lines,
    'source_status': list(source_cache.values()),
    'exact_duplicate_copy_entries': [{'entry': entry, 'lines': [row['line'] for row in rows]} for entry, rows in by_pair.items() if len(rows) > 1],
    'literal_destination_conflicts': literal_conflicts,
    'normalized_destination_aliases': normalized_aliases,
    'first_source_rule': {'evidence': ['build/core/Makefile:29-45', 'build/core/definitions.mk:847-849'], 'description': 'The pinned core removes exact copy-entry strings, then ignores later entries for the same literal destination. It constructs PRODUCT_OUT/destination with append-path, whose substitution collapses double slashes. Leading-slash destination aliases survive literal deduplication but generate the same output path.'},
    'leading_slash_destination_entries': [row for row in copy_lines if row['destination'].startswith('/')],
    'missing_or_nonregular_sources': missing_sources,
    'missing_or_nonregular_effective_literal_first_entries': missing_effective,
    'property_duplicate_keys': {key: rows for key, rows in property_pairs.items() if len(rows) > 1},
    'malformed_property_tokens': malformed_properties,
    'property_token_note': 'Properties were serialized by whitespace splitting in inspect.mk. The three tokens from testing.mediascanner.skiplist = /mnt/shell/emulated/Android/ are individually not key=value. This audit does not evaluate later build-property normalization or final build.prop validity.',
}
path = OUT / 'inventory.json'
path.write_text(json.dumps(report, indent=2, sort_keys=False) + '\n')

lines = [
    '# Flattened product selection and file audit', '',
    report['scope'], '', report['source_existence_scope'], '',
    '## Counts', '',
    '| Measure | Count |', '|---|---:|',
    *[f'| {key} | {value} |' for key, value in counts.items()], '',
    '## Selected feature cases', '',
    '- Launcher: `Launcher3` appears at package lines 1 and 64; no launcher COPY_FILES entries.',
    '- Bluetooth: no `Bluetooth`, `BluetoothMidiService`, `bluetooth.default`, or `libbt-vendor` package, or Bluetooth-named permission XML is selected. `audio.a2dp.default` and `javax.obex` remain; the copy list retains the A2DP HAL, 22 `.hcd` firmware files, and 7 `lib/rtkbt` plugins. The selected generic `platform.xml` still maps BLUETOOTH/BLUETOOTH_ADMIN/BLUETOOTH_STACK permissions. `ro.rk.bt_enable=false` is selected. These facts do not prove runtime/module closure.',
    '- Google/GApps: no named GApps package is selected. Three Google-named permission XML files remain in COPY_FILES (Maps, media effects, Widevine), and selected `features.xml` declares `com.google.android.feature.GOOGLE_BUILD` and `com.google.android.feature.GOOGLE_EXPERIENCE`. Permission/feature declarations alone do not establish the corresponding apps/libraries.',
    '- Updater/recovery: `uncrypt`, `applypatch`, and `recovery` are selected; the vendor `librockchip_update_jni.so` is copied. No named vendor updater app is selected.',
    '- Factory: no factory-named app/module/copy path is selected. Four `ro.factory.*` properties remain, along with generic debug/test tools recorded separately in JSON.', '',
    '## Destination cases', '',
    'Pinned `build/core/Makefile:29-45` keeps the first source for each literal destination after removing exact duplicate entry strings. Content hashes below distinguish duplicate selections from different file contents.', '',
    '| Literal destination | Lines | Sources | Existing contents differ |', '|---|---|---:|---|',
    *[f"| `{row['destination']}` | {', '.join(map(str, row['lines']))} | {len(row['sources'])} | {row['different_existing_content'] if row['all_sources_regular_files'] else 'Unknown: one source absent'} |" for row in literal_conflicts], '',
    'Six destinations begin with a slash. Four also have a relative spelling below: literal deduplication does not merge them, while `append-path` (`build/core/definitions.mk:847-849`) collapses the doubled slash in the generated output path:', '',
    *[f"- `{row['destination']}`: lines {', '.join(map(str, row['lines']))}; spellings: " + ', '.join(f'`{value}`' for value in row['literal_destinations']) + f"; existing contents differ: {row['different_existing_content']}." for row in normalized_aliases], '',
    '## Missing/nonregular source cases', '',
    '| Source | Lines |', '|---|---|',
    *[f"| `{row['source']}` | {', '.join(map(str, row['lines']))} |" for row in missing_sources], '',
    'All device/rockchip and vendor/rockchip selected sources are regular files in this tree. The 13 absent sources belong to system, kernel, hardware, or framework paths; three are later alternatives ignored by the literal first-source rule. Ten first-selected literal destinations have absent sources.', '',
    '## Property token cases', '',
    report['property_token_note'], '',
    'Heapstartsize, heapgrowthlimit, and heapsize appear with differing selected values. Heap target utilization/minfree/maxfree, HDMI enable, and U-disk visible also repeat; JSON records the original order and values without asserting final property resolution.', '',
    '## Input SHA-256', '',
    *[f"- `{name}.list`: `{item['sha256']}`" for name, item in inputs.items()], '',
    f"- Full case/source inventory: `inventory.json` (`{sha(path)}`).", '',
    'JSON includes every selected package/copy entry with original line numbers, SHA-256 for every existing unique source, exact duplicate strings, source status, first-source conflicts, normalized aliases, and property token anomalies.', '',
]
(OUT / 'inventory.md').write_text('\n'.join(lines))
manifest = {'inventory.json': sha(path), 'inventory.md': sha(OUT / 'inventory.md'), 'audit.py': sha(Path(__file__))}
(OUT / 'sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'counts': counts, 'literal_conflicts': literal_conflicts,
                  'normalized_aliases': normalized_aliases, 'missing_sources': missing_sources,
                  'categories': {key: {'packages': value.get('packages', []), 'copy_count': len(value.get('copy_files', [])), 'properties': value.get('properties', [])} for key, value in categories.items()},
                  'manifest': manifest}, indent=2))
