#!/usr/bin/env python3
"""Collect the qualitative evidence: functional test, demo, baseline boot, stress test.

Writes logs/functional_test_mlfq.txt, logs/demo_mlfq.txt, logs/demo_rr.txt,
logs/baseline_unmodified_boot.txt, logs/usertests_mlfq.txt
Run after scripts/build_all.sh. The baseline log needs a pristine xv6 clone in
./baseline-xv6 (see README).
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from run_xv6 import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = lambda *a: os.path.join(ROOT, 'build', *a)
L = lambda n: os.path.join(ROOT, 'logs', n)
os.environ.setdefault('XV6_QEMU_EXTRA', '-icount shift=2')

def save(name, text):
  with open(L(name), 'w') as f:
    f.write(text)
  print('wrote', name, len(text), 'bytes', flush=True)

save('functional_test_mlfq.txt', run(B('kernel-MLFQ'), B('fs-MLFQ.img'), 1, 300, 'RESULT', ['mlfqtest']))
save('demo_mlfq.txt', run(B('kernel-MLFQ'), B('fs-MLFQ.img'), 1, 600, 'DEMO_DONE', ['mlfqdemo']))
save('demo_rr.txt', run(B('kernel-RR'), B('fs-RR.img'), 1, 600, 'DEMO_DONE', ['mlfqdemo']))
# multi-core stability: same test and demo with 3 harts
save('functional_test_mlfq_3cpu.txt', run(B('kernel-MLFQ'), B('fs-MLFQ.img'), 3, 300, 'RESULT', ['mlfqtest']))
base = os.path.join(ROOT, 'baseline-xv6')
if os.path.exists(os.path.join(base, 'kernel', 'kernel')):
  save('baseline_unmodified_boot.txt', run(os.path.join(base, 'kernel', 'kernel'),
       os.path.join(base, 'fs.img'), 3, 120, 'baseline ok', ['ls', 'echo baseline ok']))
# stress: the stock xv6 test-suite on the new scheduler (real time, 3 harts)
os.environ['XV6_QEMU_EXTRA'] = ''
save('usertests_mlfq.txt', run(B('kernel-MLFQ'), B('fs-MLFQ.img'), 3, 1500, 'ALL TESTS PASSED', ['usertests -q']))
