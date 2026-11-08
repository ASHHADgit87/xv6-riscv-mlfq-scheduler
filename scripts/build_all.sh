#!/usr/bin/env bash
# Build the three kernel variants used by the benchmarks into ./build
#   kernel-RR              original round-robin scheduler (baseline)
#   kernel-MLFQ            the new MLFQ scheduler (final design)
#   kernel-MLFQ-nopreempt  MLFQ without preempt-on-wakeup (ablation only)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build
cd xv6-riscv
build() { # <variant name> <make args...>
  local name=$1; shift
  make clean > /dev/null 2>&1
  make "$@" kernel/kernel fs.img > /dev/null
  cp kernel/kernel "../build/kernel-$name"
  cp fs.img "../build/fs-$name.img"
  echo "built $name"
}
build RR SCHED=RR
build MLFQ SCHED=MLFQ
build MLFQ-nopreempt SCHED=MLFQ NOPREEMPT=1
make clean > /dev/null 2>&1
