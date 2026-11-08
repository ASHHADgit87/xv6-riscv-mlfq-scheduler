#!/usr/bin/env python3
"""Boot an xv6 image in QEMU, run shell commands, return the console output.

usage: run_xv6.py <kernel> <fs.img> <cpus> <timeout_s> <end_marker> <cmd> [<cmd> ...]

Each cmd is typed at the xv6 shell prompt one after another. The run stops
when end_marker has been seen after the last command (or on timeout) and the
whole console transcript goes to stdout. A fresh copy of fs.img is used every
time so runs never influence each other.
"""
import os, select, shutil, subprocess, sys, tempfile, time


def run(kernel, fs, cpus, timeout, marker, cmds):
  tmp = tempfile.mkdtemp()
  img = os.path.join(tmp, 'fs.img')
  shutil.copy(fs, img)
  qemu = ['qemu-system-riscv64', '-machine', 'virt', '-bios', 'none',
          '-kernel', kernel, '-m', '128M', '-smp', str(cpus), '-nographic',
          '-global', 'virtio-mmio.force-legacy=false',
          '-drive', 'file=%s,if=none,format=raw,id=x0' % img,
          '-device', 'virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0']
  extra = os.environ.get('XV6_QEMU_EXTRA', '').split()
  qemu += extra
  p = subprocess.Popen(qemu, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
  out = ''
  sent = 0
  deadline = time.time() + timeout
  try:
    while time.time() < deadline:
      r, _, _ = select.select([p.stdout], [], [], 0.2)
      if r:
        chunk = os.read(p.stdout.fileno(), 4096)
        if not chunk:
          break
        out += chunk.decode(errors='replace')
      # type the next command once a fresh prompt is showing
      if sent < len(cmds) and out.rstrip().endswith('$') and out.count('$ ') >= sent + 1:
        time.sleep(0.2)
        p.stdin.write((cmds[sent] + '\n').encode())
        p.stdin.flush()
        sent += 1
        mark_from = len(out)
      if sent == len(cmds) and marker in out[mark_from:] and out.rstrip().endswith('$'):
        break
  finally:
    p.kill()
    p.wait()
    shutil.rmtree(tmp, ignore_errors=True)
  return out


if __name__ == '__main__':
  kernel, fs, cpus, timeout, marker = sys.argv[1:6]
  sys.stdout.write(run(kernel, fs, int(cpus), float(timeout), marker, sys.argv[6:]))
