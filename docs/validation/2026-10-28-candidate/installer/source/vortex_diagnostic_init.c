/* SPDX-License-Identifier: Apache-2.0
 * Vortex TV OS diagnostic init. Reads metadata only; no flash backend.
 */
#define _GNU_SOURCE
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/types.h>
#include <unistd.h>

#define MAX_META 4096
#define MAX_BLOCKS 1024
/* Values verified in the pinned RK322x kernel include/uapi/linux/magic.h. */
#define VORTEX_RAMFS_MAGIC 0x858458f6UL
#define VORTEX_TMPFS_MAGIC 0x01021994UL

static void json_string(const char *s)
{
    const unsigned char *p = (const unsigned char *)s;
    if (!s) { fputs("null", stdout); return; }
    putchar('"');
    for (; *p; p++) {
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else if (*p < 32 || *p > 126) printf("\\u%04x", *p);
        else putchar(*p);
    }
    putchar('"');
}

static void event_error(const char *where, int code)
{
    fputs("{\"event\":\"error\",\"where\":", stdout); json_string(where);
    printf(",\"errno\":%d}\n", code);
}

static int path_join(char *out, size_t capacity, const char *root,
                     const char *name, const char *suffix)
{
    int n = snprintf(out, capacity, "%s/sys/class/block/%s%s", root, name, suffix);
    return n >= 0 && (size_t)n < capacity;
}

static int valid_block_name(const char *name)
{
    const unsigned char *p = (const unsigned char *)name;
    if (!*p || !strcmp(name, ".") || !strcmp(name, "..")) return 0;
    for (; *p; p++)
        if (!(isalnum(*p) || *p == '_' || *p == '-' || *p == '.' || *p == '!'))
            return 0;
    return 1;
}

static int read_meta(const char *root, const char *name, const char *suffix,
                     char out[MAX_META])
{
    char path[PATH_MAX];
    ssize_t n, probe;
    unsigned char tail;
    char descriptor_path[64];
    int fd, path_fd, saved;
    struct stat before, opened;
    if (!path_join(path, sizeof(path), root, name, suffix)) return 0;
    /* O_PATH never invokes a device I/O open. Pin and verify the inode before
     * reopening that same regular file through procfs; do not race a pathname. */
    path_fd = open(path, O_PATH | O_CLOEXEC | O_NOFOLLOW);
    if (path_fd < 0) return 0;
    if (fstat(path_fd, &before) || !S_ISREG(before.st_mode)) {
        close(path_fd); return 0;
    }
    snprintf(descriptor_path, sizeof(descriptor_path), "/proc/self/fd/%d", path_fd);
    fd = open(descriptor_path, O_RDONLY | O_CLOEXEC | O_NONBLOCK);
    if (fd < 0) { close(path_fd); return 0; }
    if (fstat(fd, &opened) || !S_ISREG(opened.st_mode) ||
        before.st_dev != opened.st_dev || before.st_ino != opened.st_ino) {
        close(fd); close(path_fd); return 0;
    }
    close(path_fd);
    n = read(fd, out, MAX_META - 1);
    saved = errno;
    probe = n >= 0 ? read(fd, &tail, 1) : -1;
    close(fd);
    errno = saved;
    if (n < 0 || probe != 0) return 0;
    out[n] = 0;
    /* Embedded NUL or non-printable metadata is not accepted. */
    for (ssize_t i = 0; i < n; i++)
        if (!out[i] || ((unsigned char)out[i] < 32 && out[i] != '\n' && out[i] != '\t'))
            return 0;
    while (n && (out[n-1] == '\n' || out[n-1] == '\r' || out[n-1] == '\t' || out[n-1] == ' '))
        out[--n] = 0;
    return 1;
}

static int decimal(const char *s, unsigned long long *value)
{
    char *end;
    const unsigned char *p = (const unsigned char *)s;
    if (!*p) return 0;
    for (; *p; p++) if (*p < '0' || *p > '9') return 0;
    errno = 0;
    *value = strtoull(s, &end, 10);
    return errno != ERANGE && !*end;
}

static const char *classify(const char *name, const char *type,
                            const char *removable, int partition)
{
    if (partition) return "partition_unverified_parent";
    if (!strncmp(name, "loop", 4) || !strncmp(name, "ram", 3) ||
        !strncmp(name, "zram", 4) || !strncmp(name, "dm-", 3) ||
        !strncmp(name, "md", 2)) return "virtual_or_mapped";
    if (type && !strcmp(type, "SD") && removable && !strcmp(removable, "1"))
        return "sd_candidate_unverified_boot_source";
    if (type && !strcmp(type, "MMC") && removable && !strcmp(removable, "0"))
        return "emmc_candidate_unverified_internal_source";
    if (!strncmp(name, "mtdblock", 8)) return "mtd_block_candidate_unverified_flash_type";
    return "unknown_no_write_target_selected";
}

static void emit_block(const char *root, const char *name)
{
    char size[MAX_META], ro[MAX_META], removable[MAX_META], type[MAX_META];
    char partition[MAX_META], device_name[MAX_META], path[PATH_MAX], link[PATH_MAX];
    int hs = read_meta(root, name, "/size", size);
    int hr = read_meta(root, name, "/ro", ro);
    int hm = read_meta(root, name, "/removable", removable);
    int ht = read_meta(root, name, "/device/type", type);
    int hp = read_meta(root, name, "/partition", partition);
    int hn = read_meta(root, name, "/device/name", device_name);
    unsigned long long sectors;
    ssize_t length = -1;
    if (path_join(path, sizeof(path), root, name, ""))
        length = readlink(path, link, sizeof(link)-1);
    if (length >= 0 && length < (ssize_t)sizeof(link)-1) link[length] = 0;
    else length = -1;
    fputs("{\"event\":\"block\",\"name\":", stdout); json_string(name);
    fputs(",\"classification\":", stdout);
    json_string(classify(name, ht ? type : NULL, hm ? removable : NULL, hp));
    fputs(",\"sectors_512\":", stdout); json_string(hs ? size : NULL);
    fputs(",\"size_bytes\":", stdout);
    if (hs && decimal(size, &sectors) && sectors <= ULLONG_MAX / 512)
        printf("%llu", sectors * 512);
    else fputs("null", stdout);
    fputs(",\"read_only\":", stdout); json_string(hr ? ro : NULL);
    fputs(",\"removable\":", stdout); json_string(hm ? removable : NULL);
    fputs(",\"type\":", stdout); json_string(ht ? type : NULL);
    fputs(",\"partition_number\":", stdout); json_string(hp ? partition : NULL);
    fputs(",\"device_name\":", stdout); json_string(hn ? device_name : NULL);
    fputs(",\"sysfs_link\":", stdout); json_string(length >= 0 ? link : NULL);
    fputs(",\"write_target_approved\":false}\n", stdout);
}

static int name_compare(const void *left, const void *right)
{
    return strcmp(*(const char *const *)left, *(const char *const *)right);
}

static int inventory(const char *root)
{
    char path[PATH_MAX];
    char *names[MAX_BLOCKS];
    struct dirent *entry;
    DIR *directory;
    int count = 0, saved = 0;
    if (snprintf(path, sizeof(path), "%s/sys/class/block", root) >= (int)sizeof(path))
        return 1;
    directory = opendir(path);
    if (!directory) { event_error("sys_class_block", errno); return 1; }
    errno = 0;
    while ((entry = readdir(directory))) {
        if (!valid_block_name(entry->d_name)) continue;
        if (count == MAX_BLOCKS) { saved = E2BIG; break; }
        names[count] = strdup(entry->d_name);
        if (!names[count]) { saved = ENOMEM; break; }
        count++;
        errno = 0;
    }
    if (!saved) saved = errno;
    closedir(directory);
    if (saved) {
        for (int i = 0; i < count; i++) free(names[i]);
        event_error("block_directory_read", saved); return 1;
    }
    qsort(names, (size_t)count, sizeof(names[0]), name_compare);
    for (int i = 0; i < count; i++) { emit_block(root, names[i]); free(names[i]); }
    printf("{\"event\":\"summary\",\"block_records\":%d,\"write_target_selected\":false,"
           "\"boot_medium_verified\":false}\n", count);
    return 0;
}

static void scope(const char *mode)
{
    fputs("{\"event\":\"scope\",\"version\":1,\"mode\":", stdout); json_string(mode);
    fputs(",\"block_device_io_opened\":false,\"storage_write_backend\":\"absent\",\"output\":\"stdout_only\","
          "\"boot_medium_verified\":false,\"logging_to_sd\":\"disabled_unverified_boot_identity\"}\n", stdout);
}

static void wait_forever(void)
{
    fputs("{\"event\":\"waiting\",\"installation_available\":false}\n", stdout);
    fflush(stdout);
    for (;;) pause();
}

int main(int argc, char **argv)
{
    if (getpid() != 1) {
        struct stat st;
        if (argc != 3 || strcmp(argv[1], "--inventory-root") || argv[2][0] != '/' ||
            stat(argv[2], &st) || !S_ISDIR(st.st_mode)) {
            fputs("Diagnostic component only. Use --inventory-root ABSOLUTE_FIXTURE_ROOT outside PID1.\n", stderr);
            return 64;
        }
        scope("non_pid1_inventory");
        return inventory(!strcmp(argv[2], "/") ? "" : argv[2]);
    }
    scope("pid1_initramfs_diagnostic_only");
    if (argc != 1) { event_error("pid1_arguments_not_supported", EINVAL); wait_forever(); }
    struct statfs rootfs;
    if (statfs("/", &rootfs) ||
        ((unsigned long)rootfs.f_type != VORTEX_RAMFS_MAGIC &&
         (unsigned long)rootfs.f_type != VORTEX_TMPFS_MAGIC)) {
        event_error("pid1_root_must_be_ramfs_or_tmpfs", EINVAL); wait_forever();
    }
    /* These directories belong to the unpacked RAM filesystem, not a block device. */
    if ((mkdir("/proc", 0555) && errno != EEXIST) ||
        (mkdir("/sys", 0555) && errno != EEXIST)) {
        event_error("ramfs_directories", errno); wait_forever();
    }
    const unsigned long flags = MS_RDONLY | MS_NOSUID | MS_NODEV | MS_NOEXEC;
    if (mount("proc", "/proc", "proc", flags, NULL) ||
        mount("sysfs", "/sys", "sysfs", flags, NULL)) {
        event_error("readonly_pseudofs_mount", errno); wait_forever();
    }
    (void)inventory("");
    wait_forever();
    return 0;
}
