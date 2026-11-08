#!/usr/bin/env python3
"""Run every benchmark scenario on every scheduler build and save the data.

Needs the three kernels produced by scripts/build_all.sh in build/.
Output:  logs/raw/<scenario>__<variant>__<rep>.txt   full console transcripts
         results/results.csv                        one row per process per run
usage:   python3 scripts/run_benchmarks.py [reps]
"""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from run_xv6 import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
RAW = os.path.join(ROOT, 'logs', 'raw')
RES = os.path.join(ROOT, 'results')
os.makedirs(RAW, exist_ok=True)
os.makedirs(RES, exist_ok=True)

# Deterministic virtual time: QEMU derives the clock from executed instructions
# instead of the host clock, so results do not depend on host load or speed.
os.environ.setdefault('XV6_QEMU_EXTRA', '-icount shift=2')

VARIANTS = ['RR', 'MLFQ', 'MLFQ-nopreempt']
SCENARIOS = [                       # name, bench args, variants to run
  ('solo_cpu', 'bench 1 0', ['RR', 'MLFQ']),
  ('solo_io', 'bench 0 1', ['RR', 'MLFQ']),
  ('mix_1cpu_1io', 'bench 1 1', VARIANTS),
  ('mix_3cpu_1io', 'bench 3 1', VARIANTS),
]
reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
rows = []
for name, cmd, variants in SCENARIOS:
  for variant in variants:
    for rep in range(1, reps + 1):
      out = run(os.path.join(BUILD, 'kernel-' + variant),
                os.path.join(BUILD, 'fs-' + variant + '.img'), 1, 600,
                'BENCH_DONE', [cmd])
      with open(os.path.join(RAW, '%s__%s__%d.txt' % (name, variant, rep)), 'w') as f:
        f.write(out)
      got = 0
      for line in out.splitlines():
        m = re.match(r'^(cpu|io),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)$', line.strip())
        if m:
          rows.append([name, variant, rep] + list(m.groups()))
          got += 1
      print(name, variant, rep, 'rows', got, flush=True)
with open(os.path.join(RES, 'results.csv'), 'w', newline='') as f:
  w = csv.writer(f)
  w.writerow(['scenario', 'variant', 'rep', 'kind', 'pid', 'wall_ticks', 'cpu_ms',
              'nsched', 'final_prio', 'l0_ms', 'l1_ms', 'l2_ms'])
  w.writerows(rows)
print('DONE')
