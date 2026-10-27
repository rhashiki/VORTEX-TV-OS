#!/usr/bin/env python3
"""Read fixed local U-Boot outputs and write source-review evidence only."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import sys

OUT = Path('/workspace/build01-platform-next/uboot-sd/out')
REVIEW = Path('/workspace/build01-platform-next/uboot-research/chain-review')
sys.path.insert(0, str(OUT / 'scripts/dtc/pylibfdt'))
import libfdt

sha = lambda data: hashlib.sha256(data).hexdigest()

def prop(fdt, path, key):
    try:
        return bytes(fdt.getprop(fdt.path_offset(path), key))
    except libfdt.FdtException:
        return None

def cstr(value):
    return None if value is None else value.rstrip(b'\0').decode('ascii')

def cells(data):
    return list(struct.unpack('>' + str(len(data) // 4) + 'I', data))

def review_tree(data):
    fdt = libfdt.Fdt(data)
    details = {'size_bytes': len(data), 'sha256': sha(data),
               'version': fdt.version(), 'last_compatible_version': fdt.last_comp_version(),
               'alias_mmc0': cstr(prop(fdt, '/aliases', 'mmc0')),
               'spl_order': cstr(prop(fdt, '/chosen', 'u-boot,spl-boot-order')),
               'nodes': {}, 'active_pinconf_references': []}
    for path in ['/mmc@30000000', '/mmc@30010000', '/mmc@30020000', '/serial@11030000']:
        try:
            fdt.path_offset(path)
        except libfdt.FdtException:
            details['nodes'][path] = {'present': False}
            continue
        node = {'present': True, 'status': cstr(prop(fdt, path, 'status')),
                'reg': None if prop(fdt, path, 'reg') is None else cells(prop(fdt, path, 'reg')),
                'groups': []}
        details['nodes'][path] = node
        if node['status'] != 'okay' or path not in ['/mmc@30000000', '/serial@11030000']:
            continue
        handles = prop(fdt, path, 'pinctrl-0')
        for handle in [] if handles is None else cells(handles):
            group = fdt.node_offset_by_phandle(handle)
            group_name = fdt.get_name(group)
            node['groups'].append(group_name)
            raw_pins = cells(bytes(fdt.getprop(group, 'rockchip,pins')))
            for i in range(0, len(raw_pins), 4):
                bank, pin, function, config = raw_pins[i:i + 4]
                record = {'consumer': path, 'group': group_name, 'bank': bank,
                          'pin': pin, 'function': function, 'pinconf_phandle': config}
                try:
                    config_node = fdt.node_offset_by_phandle(config)
                    record['pinconf_node'] = fdt.get_name(config_node)
                    record['resolved'] = True
                except libfdt.FdtException:
                    record['pinconf_node'] = None
                    record['resolved'] = False
                details['active_pinconf_references'].append(record)
    refs = details['active_pinconf_references']
    details['checks'] = {
        'mmc0_is_sd_controller': details['alias_mmc0'] == '/mmc@30000000',
        'spl_order_only_mmc0': details['spl_order'] == 'mmc0',
        'sd_enabled': details['nodes']['/mmc@30000000']['status'] == 'okay',
        'emmc_disabled_or_absent': not details['nodes']['/mmc@30020000']['present'] or details['nodes']['/mmc@30020000']['status'] == 'disabled',
        'sdio_disabled_or_absent': not details['nodes']['/mmc@30010000']['present'] or details['nodes']['/mmc@30010000']['status'] == 'disabled',
        'all_active_pinconf_targets_resolve': bool(refs) and all(r['resolved'] for r in refs),
        'sd_bus4_pc2_pc5_mux1': {(r['bank'], r['pin'], r['function']) for r in refs if r['group'] == 'sdmmc-bus4'} == {(1, pin, 1) for pin in range(18, 22)},
        'uart21_pb1_pb2_mux2': {(r['bank'], r['pin'], r['function']) for r in refs if r['group'] == 'uart21-xfer'} == {(1, 9, 2), (1, 10, 2)},
    }
    return details

def elf_symbols(data):
    assert data[:6] == b'\x7fELF\x01\x01', 'Expected little-endian ELF32'
    head = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
    sections = [struct.unpack_from('<10I', data, head[5] + i * head[10]) for i in range(head[11])]
    result = {}
    for section in sections:
        if section[1] != 2:
            continue
        names = sections[section[6]]
        strings = data[names[4]:names[4] + names[5]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name_offset, value, size, info, other, index = struct.unpack_from('<IIIBBH', data, offset)
            end = strings.find(b'\0', name_offset)
            name = strings[name_offset:end].decode('ascii')
            if name:
                result[name] = {'value': value, 'size': size, 'section': index}
    return result, sections

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'final'
    tree_root = REVIEW / 'before-pinconf-fix' if mode == 'before' else OUT
    trees = {name: review_tree((tree_root / name).read_bytes()) for name in ['u-boot.dtb', 'spl/u-boot-spl.dtb', 'tpl/u-boot-tpl.dtb']}
    report = {'scope': 'Read-only inspection of real built artifacts; not a boot test or physical compatibility approval.', 'trees': trees}
    if mode != 'before':
        config_data = (OUT / '.config').read_bytes()
        config = {}
        for raw in config_data.decode().splitlines():
            if raw.startswith('CONFIG_'):
                key, value = raw.split('=', 1)
                config[key] = value
            elif re.fullmatch(r'# CONFIG_\w+ is not set', raw):
                config[raw.split()[1]] = 'n'
        required_y = ['OPTEE_LIB', 'ENV_IS_NOWHERE', 'USE_DEFAULT_ENV_FILE', 'PINCTRL_FULL', 'SPL_PINCTRL', 'SPL_PINCTRL_FULL']
        required_n = ['MMC_WRITE', 'SPL_MMC_WRITE', 'CMD_SAVEENV', 'CMD_ERASEENV', 'CMD_FASTBOOT', 'FASTBOOT', 'CMD_USB_MASS_STORAGE', 'USB', 'NET', 'MTD', 'CMD_MMC']
        report['config'] = {'sha256': sha(config_data), 'resolved_values': {key: config.get('CONFIG_' + key, 'n (not generated/dependency disabled)') for key in required_y + required_n}, 'checks': {key: config.get('CONFIG_' + key) == 'y' for key in required_y} | {key: config.get('CONFIG_' + key, 'n') == 'n' for key in required_n}, 'bootdelay': config.get('CONFIG_BOOTDELAY'), 'default_env_file': config.get('CONFIG_DEFAULT_ENV_FILE')}
        elf = (OUT / 'u-boot').read_bytes()
        symbols, sections = elf_symbols(elf)
        env_sym = symbols['default_environment']
        env_sec = sections[env_sym['section']]
        start = env_sec[4] + env_sym['value'] - env_sec[3]
        env = elf[start:start + env_sym['size']]
        entries = [item.decode() for item in env.split(b'\0') if item]
        expected_env = ['bootcmd=echo Vortex SD reference components only', 'bootdelay=-1', 'baudrate=1500000', 'stdin=serial', 'stdout=serial', 'stderr=serial', 'boot_targets=mmc0']
        write_pattern = re.compile(r'(?i)(saveenv|save_env|fastboot|rockusb|(^|_)ums($|_)|mmc_bwrite|mmc_berase|do_mmc_write|do_mmc_erase)')
        bad_symbols = sorted(name for name in symbols if write_pattern.search(name))
        command_names = sorted(name.split('_u_boot_list_2_cmd_2_', 1)[1] for name in symbols if name.startswith('_u_boot_list_2_cmd_2_'))
        report['elf'] = {'sha256': sha(elf), 'default_environment_size': len(env), 'default_environment_sha256': sha(env), 'default_environment_entries': entries, 'default_environment_exactly_expected': entries == expected_env, 'known_write_command_or_backend_symbols': bad_symbols, 'compiled_commands': command_names, 'optee_copy_fdt_nodes_symbol_present': 'optee_copy_fdt_nodes' in symbols, 'limits': ['Symbol absence covers enumerated command/backend names only, not proof that arbitrary manual code execution or hardware can never write storage.']}
        fit_data = (OUT / 'u-boot.itb').read_bytes()
        fit = libfdt.Fdt(fit_data)
        image = fit.path_offset('/images/op-tee')
        fit_total = fit.totalsize()
        offset = int.from_bytes(bytes(fit.getprop(image, 'data-offset')), 'big')
        size = int.from_bytes(bytes(fit.getprop(image, 'data-size')), 'big')
        tee = fit_data[fit_total + offset:fit_total + offset + size]
        compiled_tee = Path('/workspace/build01-platform-next/optee-build/out/core/tee-raw.bin').read_bytes()
        report['fit'] = {'sha256': sha(fit_data), 'fdt_totalsize': fit_total, 'optee_load': hex(int.from_bytes(bytes(fit.getprop(image, 'load')), 'big')), 'optee_entry': hex(int.from_bytes(bytes(fit.getprop(image, 'entry')), 'big')), 'optee_data_offset_after_fit_header': offset, 'optee_size': size, 'optee_sha256': sha(tee), 'compiled_optee_sha256': sha(compiled_tee), 'optee_payload_byte_identical_to_compiled_raw': tee == compiled_tee, 'firmware': cstr(prop(fit, '/configurations/config-1', 'firmware')), 'loadables': cstr(prop(fit, '/configurations/config-1', 'loadables'))}
        dump = subprocess.check_output([str(OUT / 'tools/dumpimage'), '-l', str(OUT / 'u-boot.itb')], text=True)
        (REVIEW / 'final-dumpimage.txt').write_text(dump)
    report['all_tree_checks_pass'] = all(all(t['checks'].values()) for t in trees.values())
    if mode != 'before':
        report['review_checks'] = {
            'all_tree_checks_pass': report['all_tree_checks_pass'],
            'all_config_checks_pass': all(report['config']['checks'].values()),
            'environment_exact': report['elf']['default_environment_exactly_expected'],
            'enumerated_write_symbols_absent': not report['elf']['known_write_command_or_backend_symbols'],
            'optee_copy_fdt_nodes_compiled': report['elf']['optee_copy_fdt_nodes_symbol_present'],
            'optee_payload_matches_compiled': report['fit']['optee_payload_byte_identical_to_compiled_raw'],
            'optee_load_entry_expected': report['fit']['optee_load'] == report['fit']['optee_entry'] == '0x68400000',
            'fit_roles_match': report['fit']['firmware'] == 'op-tee' and report['fit']['loadables'] == 'u-boot',
            'autoboot_disabled': report['config']['bootdelay'] == '-1',
        }
        report['all_static_artifact_checks_pass'] = all(report['review_checks'].values())
    report['hardware_validation'] = 'not_performed'
    output = REVIEW / ('before-pinconf-review.json' if mode == 'before' else 'built-artifact-review.json')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(output), 'all_tree_checks_pass': report['all_tree_checks_pass'], 'failed_tree_checks': {name: [key for key,value in tree['checks'].items() if not value] for name,tree in trees.items()}}, indent=2))

if __name__ == '__main__':
    run()
