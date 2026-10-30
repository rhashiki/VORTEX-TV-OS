#!/usr/bin/env python3
"""Exercise the actual static ARM binary under QEMU user mode on fixtures."""
from pathlib import Path
import hashlib,json,os,re,stat,subprocess,tempfile,unittest

ROOT=Path(__file__).resolve().parent
QEMU=Path('/workspace/build01-hal-next/loader/bin/qemu-arm-static')
BINARY=ROOT/'artifacts/vortex-diagnostic-init'
EVIDENCE=ROOT/'evidence/fixture-tests'
RESULTS=[]


def snapshot(root):
    result={}
    for p in sorted(root.rglob('*')):
        s=p.lstat();kind=stat.S_IFMT(s.st_mode)
        value=os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest() if stat.S_ISREG(s.st_mode) else None
        result[str(p.relative_to(root))]=(kind,stat.S_IMODE(s.st_mode),value)
    return result


class ArmComponentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='diag-',dir=ROOT/'fixtures')
        self.root=Path(self.temp.name);(self.root/'sys/class/block').mkdir(parents=True)
        self.addCleanup(self.temp.cleanup)

    def block(self,name,**attrs):
        directory=self.root/'sys/class/block'/name;directory.mkdir()
        defaults={'size':'1024\n','ro':'0\n','removable':'0\n'};defaults.update(attrs)
        for name,value in defaults.items():
            if value is None:continue
            p=directory/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(value if isinstance(value,bytes) else value.encode())
        return directory

    def run_arm(self,expected=0,args=None):
        before=snapshot(self.root)
        command=[str(QEMU),'-strace',str(BINARY)]+(args if args is not None else ['--inventory-root',str(self.root)])
        run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
        label=self._testMethodName
        EVIDENCE.mkdir(exist_ok=True,parents=True)
        (EVIDENCE/(label+'.stdout')).write_bytes(run.stdout);(EVIDENCE/(label+'.strace')).write_bytes(run.stderr)
        trace=run.stderr.decode();self.assertEqual(run.returncode,expected,trace)
        self.assertEqual(snapshot(self.root),before,'fixture files changed')
        self.assertIsNone(re.search(r'\b(?:open|openat)\(.*(?:O_WRONLY|O_RDWR|O_CREAT|O_TRUNC|O_APPEND)',trace))
        self.assertIsNone(re.search(r'\b(?:mount|umount|reboot|unlink|rename|truncate|ftruncate|mknod|mkdir)\(',trace))
        self.assertTrue(all(int(fd) in (1,2) for fd in re.findall(r'\b(?:write|writev)\((\d+),',trace)))
        records=[json.loads(line) for line in run.stdout.splitlines()]
        for record in records:
            if record['event']=='block':self.assertFalse(record['write_target_approved'])
            if 'boot_medium_verified' in record:self.assertFalse(record['boot_medium_verified'])
        RESULTS.append({'case':label,'exit_code':run.returncode,'fixture_unchanged':True,
                        'trace_no_storage_io_or_write_flags':True,'stdout_log':label+'.stdout','trace_log':label+'.strace'})
        return records

    def only_block(self,records):
        return next(r for r in records if r['event']=='block')

    def test_sd_candidate_never_approved_as_boot(self):
        self.block('mmcblk0',**{'device/type':'SD\n','removable':'1\n'})
        record=self.only_block(self.run_arm());self.assertEqual(record['classification'],'sd_candidate_unverified_boot_source')
        self.assertEqual(record['size_bytes'],524288)

    def test_mmc_candidate_never_approved_as_internal(self):
        self.block('mmcblk1',**{'device/type':'MMC\n'})
        self.assertEqual(self.only_block(self.run_arm())['classification'],'emmc_candidate_unverified_internal_source')

    def test_unknown_vendor_nand_name_not_guessed(self):
        self.block('rknand0')
        self.assertEqual(self.only_block(self.run_arm())['classification'],'unknown_no_write_target_selected')

    def test_mtd_block_does_not_assert_nand(self):
        self.block('mtdblock0')
        self.assertEqual(self.only_block(self.run_arm())['classification'],'mtd_block_candidate_unverified_flash_type')

    def test_partition_is_not_whole_disk(self):
        self.block('mmcblk0p1',partition='1\n',**{'device/type':'SD\n','removable':'1\n'})
        self.assertEqual(self.only_block(self.run_arm())['classification'],'partition_unverified_parent')

    def test_virtual_storage_not_internal_target(self):
        self.block('loop0')
        self.assertEqual(self.only_block(self.run_arm())['classification'],'virtual_or_mapped')

    def test_inconsistent_sd_removable_stays_unknown(self):
        self.block('mmcblk0',**{'device/type':'SD\n'})
        self.assertEqual(self.only_block(self.run_arm())['classification'],'unknown_no_write_target_selected')

    def test_inconsistent_mmc_removable_stays_unknown(self):
        self.block('mmcblk0',**{'device/type':'MMC\n','removable':'1\n'})
        self.assertEqual(self.only_block(self.run_arm())['classification'],'unknown_no_write_target_selected')

    def test_size_multiply_overflow_rejected(self):
        self.block('x',size=str(2**64-1))
        self.assertIsNone(self.only_block(self.run_arm())['size_bytes'])

    def test_size_parse_overflow_rejected(self):
        self.block('x',size=str(2**64))
        self.assertIsNone(self.only_block(self.run_arm())['size_bytes'])

    def test_signed_size_rejected(self):
        self.block('x',size='-1\n')
        self.assertIsNone(self.only_block(self.run_arm())['size_bytes'])

    def test_metadata_symlink_not_followed(self):
        d=self.block('x',size=None);(self.root/'secret').write_text('123')
        (d/'size').symlink_to(self.root/'secret')
        self.assertIsNone(self.only_block(self.run_arm())['sectors_512'])

    def test_metadata_fifo_not_opened_for_io(self):
        d=self.block('x',size=None);os.mkfifo(d/'size')
        self.assertIsNone(self.only_block(self.run_arm())['sectors_512'])

    def test_metadata_directory_rejected(self):
        d=self.block('x',size=None);(d/'size').mkdir()
        self.assertIsNone(self.only_block(self.run_arm())['sectors_512'])

    def test_oversized_metadata_rejected(self):
        self.block('x',size='1'*4096)
        self.assertIsNone(self.only_block(self.run_arm())['sectors_512'])

    def test_embedded_nul_metadata_rejected(self):
        self.block('x',size=b'123\x00456')
        self.assertIsNone(self.only_block(self.run_arm())['sectors_512'])

    def test_json_quotes_and_newlines_escaped(self):
        self.block('x',**{'device/name':'a"b\\c\nd\n'})
        self.assertEqual(self.only_block(self.run_arm())['device_name'],'a"b\\c\nd')

    def test_invalid_block_name_skipped(self):
        self.block('space name');records=self.run_arm()
        self.assertEqual(records[-1]['block_records'],0)

    def test_enumeration_sorted_and_bounded(self):
        self.block('z');self.block('a');records=self.run_arm()
        self.assertEqual([r['name'] for r in records if r['event']=='block'],['a','z'])

    def test_too_many_entries_fail_before_inventory(self):
        for n in range(1025):(self.root/'sys/class/block'/('x%04d'%n)).mkdir()
        records=self.run_arm(expected=1);self.assertEqual(records[-1]['errno'],7)
        self.assertFalse(any(r['event']=='block' for r in records))

    def test_empty_inventory_selects_no_target(self):
        self.assertEqual(self.run_arm()[-1]['block_records'],0)

    def test_missing_sysfs_fails_without_fallback(self):
        (self.root/'sys/class/block').rmdir();records=self.run_arm(expected=1)
        self.assertEqual(records[-1]['where'],'sys_class_block')

    def test_relative_fixture_argument_rejected(self):
        self.assertEqual(self.run_arm(expected=64,args=['--inventory-root','relative']),[])

    def test_missing_arguments_rejected_outside_pid1(self):
        self.assertEqual(self.run_arm(expected=64,args=[]),[])


if __name__=='__main__':
    (ROOT/'fixtures').mkdir(exist_ok=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ArmComponentTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'scope':'actual static ARM Linux binary under QEMU user mode, trusted local metadata fixtures only',
            'status':'pass' if result.wasSuccessful() else 'fail','tests_run':result.testsRun,'cases':RESULTS,
            'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            'qemu_sha256':hashlib.sha256(QEMU.read_bytes()).hexdigest(),
            'limits':['PID1 mounts/root-filesystem guard/wait path not executed by this user-mode suite',
                      'No Rockchip kernel boot, internal storage driver, FlashID, partition offsets, SD identity or physical compatibility proven',
                      'Stdout is captured by the host test harness; SD logging and all installation writes remain absent']}
    (ROOT/'evidence/component-test-result.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
