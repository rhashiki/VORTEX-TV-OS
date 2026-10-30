#!/usr/bin/env python3
"""Read-only build-capacity snapshot, not a firmware or minimum-size validator."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
REPO = Path('/workspace/vortex-build')


def command(argv):
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=30)
    return {'argv': argv, 'exit_code': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr}


def main():
    base = REPO / 'rom/platform-reference/aosp-r6-default.xml'
    overlay = REPO / 'rom/platform-reference/vortex-r6-rockchip-experimental.xml'
    base_xml = ET.parse(base).getroot()
    overlay_xml = ET.parse(overlay).getroot()
    projects = {e.get('name'): dict(e.attrib) for e in base_xml.findall('project')}
    removed = []
    for e in overlay_xml.findall('remove-project'):
        name = e.get('name')
        removed.append(name)
        del projects[name]
    for e in overlay_xml.findall('project'):
        assert e.get('name') not in projects
        projects[e.get('name')] = dict(e.attrib)
    paths = [p['path'] for p in projects.values()]
    assert len(paths) == len(set(paths))
    filter_excluded = [p for p in projects.values()
                       if {'darwin', 'notdefault'} & set(p.get('groups', '').split(','))]
    cgroup = Path('/sys/fs/cgroup')
    cpu_quota, cpu_period = (cgroup / 'cpu.max').read_text().split()
    memory_limit = (cgroup / 'memory.max').read_text().strip()
    disk = shutil.disk_usage('/workspace')
    reads = [
        command(['findmnt', '-b', '-o', 'TARGET,SOURCE,FSTYPE,SIZE,AVAIL,OPTIONS']),
        command(['lsblk', '-b', '-o', 'NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS']),
        command(['df', '-B1', '/workspace', '/tmp', '/dev/shm']),
        command(['docker', 'info', '--format', '{{json .Driver}} {{json .DockerRootDir}} {{json .MemTotal}} {{json .NCPU}}']),
        command(['df', '-B1', '/var/lib/docker', '/workspace']),
    ]
    (ROOT / 'host-command-results.json').write_text(json.dumps(reads, indent=2) + '\n')
    result = {
        'schema_version': 1,
        'observed_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'capacity_and_declared_source_inventory_only',
        'host': {
            'workspace_disk_total_bytes': disk.total,
            'workspace_disk_used_bytes': disk.used,
            'workspace_disk_free_bytes': disk.free,
            'memory_limit_bytes': int(memory_limit) if memory_limit != 'max' else None,
            'memory_current_bytes': int((cgroup / 'memory.current').read_text()),
            'cpu_quota_cores': int(cpu_quota) / int(cpu_period) if cpu_quota != 'max' else None,
            'host_visible_cpu_count': command(['getconf', '_NPROCESSORS_ONLN'])['stdout'].strip(),
            'swap_current_bytes': int((cgroup / 'memory.swap.current').read_text()),
            'swap_devices': Path('/proc/swaps').read_text(),
            'separate_writable_persistent_mount_observed': False,
            'tmpfs_is_additional_persistent_build_disk': False,
        },
        'manifest': {
            'base_projects': len(base_xml.findall('project')),
            'removed_projects': len(removed),
            'overlay_projects': len(overlay_xml.findall('project')),
            'composed_projects': len(projects),
            'by_top_level_path': dict(sorted(Counter(p['path'].split('/')[0] for p in projects.values()).items())),
            'fully_pinned_overlay_projects': sum(len(p.get('revision', '')) == 40 for p in projects.values()),
            'remaining_default_tag_projects': sum(not p.get('revision') for p in projects.values()),
            'default_minus_darwin_excluded_count': len(filter_excluded),
            'default_minus_darwin_remaining_count': len(projects) - len(filter_excluded),
            'filter_is_not_transitive_module_dependency_closure': True,
            'repo_manifest_r_lock_produced': False,
        },
        'runtime_capabilities': {
            'managed_environment_status': 'connected, running, observations_current true',
            'network_policy': 'unrestricted/enforced',
            'configured_capabilities': [],
            'configured_outbound_identities': [],
            'configured_secrets': [],
            'available_environment_tool_scope': 'status and diagnostics; no attached storage/VM creation tool found',
        },
        'conclusions': {
            'normal_complete_repo_sync_and_platform_build': 'capacity_not_satisfied_by_current_environment',
            'exact_minimum_custom_product_bytes': 'not_measured',
            'bounded_selected_source_build_experiments': 'possible, subject to actual module dependencies and free-space limits',
            'rom_image_built': False,
            'no_old_sources_or_artifacts_deleted': True,
            'no_disk_mount_or_resource_configuration_changed': True,
        },
        'input_hashes': {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (base, overlay)
        },
    }
    (ROOT / 'manifest-selected-projects.json').write_text(json.dumps({
        'scope': 'declared_manifest_composition_not_resolved_lock',
        'projects': sorted(projects.values(), key=lambda p: p['path']),
        'default_minus_darwin_exclusions': sorted(filter_excluded, key=lambda p: p['path']),
    }, indent=2) + '\n')
    (ROOT / 'capacity.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
