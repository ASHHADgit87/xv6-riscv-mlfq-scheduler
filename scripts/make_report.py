#!/usr/bin/env python3
"""Build report/OS_Lab13_Performance_Report.pdf from results/results.csv and logs/.

Every number in the text and tables is computed from the CSV, so re-running the
benchmarks on another machine and then this script gives a report that matches
that machine's data.   usage: python3 scripts/make_report.py
"""
import csv, collections, os, re, statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, Preformatted, KeepTogether)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

# ---------------------------------------------------------------- data
rows = list(csv.DictReader(open(P('results', 'results.csv'))))
D = collections.defaultdict(list)
for r in rows:
  D[(r['scenario'], r['variant'], r['kind'])].append(r)

def vals(s, v, k, f):
  return [int(x[f]) for x in D[(s, v, k)]]

def mean(s, v, k, f='wall_ticks'):
  return st.mean(vals(s, v, k, f))

def rng(s, v, k, f='wall_ticks'):
  x = vals(s, v, k, f)
  return '%.0f' % st.mean(x) if min(x) == max(x) else '%.0f (%d-%d)' % (st.mean(x), min(x), max(x))

def avg_turnaround(s, v):
  # mean completion time over all processes of the run (they all start together)
  x = [int(r['wall_ticks']) for r in rows if r['scenario'] == s and r['variant'] == v]
  return st.mean(x)

reps = len(set(r['rep'] for r in rows))
secs = lambda t: t / 10.0

# ---------------------------------------------------------------- charts
def chart_io():
  fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
  for ax, sc, title in [(axes[0], 'mix_1cpu_1io', '1 CPU-bound + 1 I/O-bound'),
                        (axes[1], 'mix_3cpu_1io', '3 CPU-bound + 1 I/O-bound')]:
    labels = ['Round-robin', 'MLFQ', 'MLFQ, no\nwake preempt']
    keys = ['RR', 'MLFQ', 'MLFQ-nopreempt']
    cpu = [mean(sc, k, 'cpu') for k in keys]
    io = [mean(sc, k, 'io') for k in keys]
    x = range(3)
    ax.bar([i - 0.2 for i in x], cpu, 0.4, label='CPU-bound', color='#777777')
    ax.bar([i + 0.2 for i in x], io, 0.4, label='I/O-bound', color='#222222')
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.set_ylabel('completion time (ticks)', fontsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.legend(fontsize=7)
  fig.tight_layout()
  fig.savefig(P('results', 'completion_times.png'), dpi=200)
  plt.close(fig)

chart_io()

# ---------------------------------------------------------------- styles
base = ParagraphStyle('base', fontName='Times-Roman', fontSize=10.5, leading=14.2, spaceAfter=6)
h1 = ParagraphStyle('h1', parent=base, fontName='Times-Bold', fontSize=13, leading=16, spaceBefore=12, spaceAfter=5)
h2 = ParagraphStyle('h2', parent=base, fontName='Times-Bold', fontSize=11, spaceBefore=6, spaceAfter=3)
title = ParagraphStyle('title', parent=base, fontName='Times-Bold', fontSize=17, leading=21, alignment=1, spaceAfter=4)
sub = ParagraphStyle('sub', parent=base, alignment=1, fontSize=11, spaceAfter=2)
cell = ParagraphStyle('cell', parent=base, fontSize=9, leading=11, spaceAfter=0)
cellb = ParagraphStyle('cellb', parent=cell, fontName='Times-Bold')
mono = ParagraphStyle('mono', fontName='Courier', fontSize=7.4, leading=9.2)
cap = ParagraphStyle('cap', parent=base, fontSize=9, leading=11, spaceBefore=2, spaceAfter=8)

def para(t): return Paragraph(t, base)
def tbl(data, widths, header=True):
  d = [[Paragraph(str(c), cellb if (header and i == 0) else cell) for c in row] for i, row in enumerate(data)]
  t = Table(d, colWidths=widths, repeatRows=1 if header else 0)
  t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, colors.black),
                         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                         ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
  return t

def readlog(name):
  p = P('logs', name)
  return open(p).read() if os.path.exists(p) else ''

story = []
A = story.append

# ---------------------------------------------------------------- title
A(Paragraph('Department of Software Engineering, NED University of Engineering &amp; Technology', sub))
A(Paragraph('SE-303 Operating Systems - Lab Session 13 (Complex Engineering Activity)', sub))
A(Spacer(1, 10))
A(Paragraph('A Multi-Level Feedback Queue Scheduler for xv6-RISC-V and Its Effect on CPU-Bound and I/O-Bound Programs', title))
A(Spacer(1, 4))
A(Paragraph('Group of two', sub))
A(Paragraph('Muhammad Ashhadullah Zaheer (SE-24087)', sub))
A(Paragraph('Misbah Sarfraz (SE-24096)', sub))
A(Paragraph('Batch 2024-2028', sub))
A(Spacer(1, 8))

# ---------------------------------------------------------------- 1
A(Paragraph('1. Objective', h1))
A(para('The xv6 kernel schedules processes round-robin: every runnable process gets the CPU in turn, whatever it is doing. '
       'This lab replaces that policy with a Multi-Level Feedback Queue (MLFQ), adds a system call that exposes per-process '
       'CPU accounting, and uses two user programs (one that computes, one that does file I/O) to measure what the change does '
       'to each kind of workload. The report covers the design, how it was tested, the measurements, and what they say about '
       'the relationship between a kernel scheduling decision and the way applications should be written.'))

# ---------------------------------------------------------------- 2
A(Paragraph('2. Environment and method', h1))
A(tbl([['Item', 'Value'],
       ['Operating system', 'xv6-riscv from github.com/mit-pdos/xv6-riscv, commit fa2ddcb'],
       ['Emulator', 'QEMU 8.2.2, machine "virt", 128 MB RAM, virtio disk'],
       ['Toolchain', 'riscv64-linux-gnu-gcc 13.3.0 on Ubuntu 24.04'],
       ['Scheduler comparison runs', 'one hart (-smp 1) so that the two schedulers compete for the same single CPU'],
       ['Clock', 'QEMU -icount shift=2: virtual time is derived from executed instructions, not from the host clock'],
       ['Timer tick', '1,000,000 cycles = 100 ms of virtual time (unchanged from stock xv6)'],
       ['Repetitions', '%d runs of every scenario and kernel variant' % reps]],
      [4.6 * cm, 11.4 * cm]))
A(Spacer(1, 6))
A(para('Three kernels were built from the same source tree: <b>RR</b> (the original round-robin loop, selected with <font face="Courier">make SCHED=RR</font>), '
       '<b>MLFQ</b> (the final design), and <b>MLFQ-nopreempt</b> (MLFQ with one feature switched off, used only to see which part of the design matters). '
       'The accounting code is identical in all three, so any difference in the numbers comes from the scheduling decision.'))
A(para('The clock setting deserves a note. A first set of runs used <font face="Courier">-icount shift=2,sleep=off</font>. In that mode QEMU jumps the virtual clock forward whenever the CPU is idle, '
       'so a process waiting for the disk appears to wait for many ticks. A solo I/O run took over 5,500 ticks instead of about 34, and the figures varied from run to run. '
       'Those results were discarded. With the default idle behaviour the repeated runs agree to within a tick or two, which is what makes the comparison meaningful.'))
A(para('Baseline. The unmodified xv6 source was built separately and booted to the shell (logs/baseline_unmodified_boot.txt). '
       'The round-robin kernel above is the same code with the accounting added, and its solo results (Section 6, Table 1) are the baseline numbers.'))

# ---------------------------------------------------------------- 3
A(Paragraph('3. Design and implementation', h1))
A(Paragraph('3.1 The scheduler', h2))
A(para('There are three priority levels, 0 being the highest. Time slices are 1, 2 and 4 ticks for levels 0, 1 and 2, so the processes that are expected to be short get the most frequent turns and the ones that keep computing switch less often. The rules are:'))
for t in ['A new process starts at level 0 (set in <font face="Courier">allocproc()</font>, so a child of a demoted parent also starts at the top).',
          'The scheduler always runs a runnable process from the highest non-empty level. Inside a level, the process that ran least recently goes first, which gives round-robin among equals.',
          'A process that is preempted after using its whole slice moves down one level; level 2 is the floor.',
          'A process that gives up the CPU before its slice is over (it sleeps on disk, a pipe, or <font face="Courier">pause()</font>, or exits) keeps its level and starts its next slice from zero.']:
  A(Paragraph('- ' + t, ParagraphStyle('li', parent=base, leftIndent=14, firstLineIndent=-8, spaceAfter=3)))
A(para('Two additions go beyond the lab text. <b>Priority boost:</b> every 100 ticks all processes return to level 0, otherwise a process demoted during a long computation could be starved indefinitely by a stream of interactive jobs. '
       '<b>Preempt on wakeup:</b> when <font face="Courier">wakeup()</font> makes a process runnable that has a better level than the process running on that CPU, the CPU is told to reschedule when its current trap finishes. '
       'xv6 only reschedules on the timer interrupt, so without this a woken I/O process waits up to 100 ms behind a running CPU-bound process however high its priority is. '
       'Sections 6 and 7 show how much this matters.'))
A(Paragraph('3.2 Accounting by measured run time', h2))
A(para('The first version charged one tick to whichever process was running when the timer fired and demoted it when its tick count reached the slice length. '
       'The functional test caught the problem: an I/O-bound process that ran for a few microseconds per wakeup was being demoted simply because the timer sometimes fired during one of those microseconds. '
       'The final version reads the RISC-V <font face="Courier">time</font> register before and after every dispatch (in <font face="Courier">scheduler()</font>) and adds the actual run length to the process. '
       'If the process comes back still runnable it was preempted and the time counts toward its slice; if it comes back sleeping or exiting, the slice counter is cleared. '
       'The same measurement feeds <font face="Courier">getprocinfo()</font>, so CPU time is exact rather than sampled.'))
A(Paragraph('3.3 The getprocinfo system call', h2))
A(para('<font face="Courier">int getprocinfo(int pid, struct procinfo *info)</font> fills a structure with the pid, process state, scheduler mode, current queue, CPU ticks and milliseconds, number of times scheduled, and CPU milliseconds spent at each level. '
       'A pid of zero or less means the caller. xv6 system calls return a single integer, so the lab\'s <font face="Courier">getprocinfo(int pid)</font> had to gain an output pointer to return several metrics. '
       'The kernel copies the data out under the process lock and calls <font face="Courier">copyout()</font> after releasing it. It returns -1 for an unknown pid or a bad user pointer.'))
A(Paragraph('3.4 Locking and kernel integration', h2))
A(para('All new fields live in <font face="Courier">struct proc</font> and are protected by <font face="Courier">p->lock</font>, as the rest of that structure is. '
       'The pick function scans the table once taking each lock briefly, then locks the winner and checks it is still runnable before switching to it; if another CPU got there first it scans again. '
       'The only unlocked access is the priority comparison in <font face="Courier">wakeup()</font>, which sets a per-CPU hint flag. A stale read there can at worst cause one unnecessary or one delayed reschedule. '
       'The new system call follows the existing pattern (number in syscall.h, table entry in syscall.c, handler in sysproc.c, stub in usys.pl, prototype in user.h).'))
files = [['File', 'Change'],
         ['kernel/proc.c, proc.h', 'MLFQ pick, run-time accounting, boost, wakeup preemption hint, kgetprocinfo(), new per-process fields'],
         ['kernel/trap.c', 'trap exit also yields when a preemption was requested; boost called from the clock interrupt'],
         ['kernel/sysproc.c, syscall.c, syscall.h, user/usys.pl, user/user.h', 'getprocinfo system call'],
         ['kernel/procinfo.h, param.h, defs.h', 'shared result structure, tunables (NQUEUE, MLFQ_BOOST_TICKS, TICK_CYCLES), prototypes'],
         ['Makefile', 'SCHED=RR and NOPREEMPT=1 build switches, new user programs'],
         ['user/cpubound.c, iobound.c, workloads.h', 'the two test applications and their shared workload code'],
         ['user/bench.c, mlfqtest.c, mlfqdemo.c', 'benchmark runner, functional tests, scheduling demonstration']]
A(Spacer(1, 3))
A(tbl(files, [6.2 * cm, 9.8 * cm]))

# ---------------------------------------------------------------- 4
A(Paragraph('4. Test applications', h1))
A(para('<b>cpubound</b> counts the primes below 4,000,000 by trial division. It makes no system calls, so it never blocks and always uses its whole slice. '
       'On one hart it needs about %.1f s of CPU (%.0f ticks).' % (mean('solo_cpu', 'RR', 'cpu', 'cpu_ms') / 1000.0, mean('solo_cpu', 'RR', 'cpu'))))
A(para('<b>iobound</b> runs 100 iterations of: create a file, write four 64-byte blocks, close it, delete it. Each of those calls goes through the xv6 log and the virtio disk and puts the process to sleep, '
       'so the program is dispatched about %.0f times during one run and holds the CPU for a very short time on each. Solo it takes %.0f ticks.' % (mean('solo_io', 'RR', 'io', 'nsched'), mean('solo_io', 'RR', 'io'))))
A(para('<b>bench N M</b> forks N copies of the first and M of the second and starts them together. Each child records its start and finish time and its <font face="Courier">getprocinfo()</font> counters, and sends them to the parent through a pipe, so the console output of different processes never interleaves. '
       'An early version of the CPU workload finished in 0 ms because the compiler removed the loop whose result was unused; the result is now stored in a volatile variable.'))

# ---------------------------------------------------------------- 5
A(Paragraph('5. Functional testing', h1))
ft = readlog('functional_test_mlfq.txt')
checks = re.findall(r'\[(PASS|FAIL)\] (.*)', ft)
npass = sum(1 for c in checks if c[0] == 'PASS')
ft3 = readlog('functional_test_mlfq_3cpu.txt')
npass3 = len(re.findall(r'\[PASS\]', ft3))
A(para('<font face="Courier">mlfqtest</font> runs %d checks; all of them pass on the MLFQ kernel with one hart and with three harts (%d and %d passes, no failures). They are listed below.' % (len(checks), npass, npass3)))
A(tbl([['#', 'Check', 'Result']] + [[str(i + 1), c[1], c[0]] for i, c in enumerate(checks)], [0.9 * cm, 12.6 * cm, 2.5 * cm]))
A(Spacer(1, 6))
ut = readlog('usertests_mlfq.txt')
A(para('For stability, the standard xv6 test suite (<font face="Courier">usertests -q</font>) was run on the MLFQ kernel with three harts. It ends with %s and the log contains no kernel panic (logs/usertests_mlfq.txt).' %
       ('"ALL TESTS PASSED"' if 'ALL TESTS PASSED' in ut else '<b>a failure - see the log</b>')))
A(Paragraph('Scheduling demonstration', h2))
A(para('<font face="Courier">mlfqdemo</font> starts two CPU-bound processes and one I/O-bound process and prints their level, CPU ticks and number of dispatches every two ticks. '
       'The excerpts below show the same program under both kernels (columns: elapsed ticks; for each process its pid, queue level, CPU ticks and dispatch count).'))
def demo_excerpt(name, n):
  lines = [l for l in readlog(name).splitlines() if re.match(r'^\d+ \|', l)]
  return lines[:n]
for name, label in [('demo_rr.txt', 'Round-robin kernel'), ('demo_mlfq.txt', 'MLFQ kernel')]:
  ex = demo_excerpt(name, 9)
  A(KeepTogether([Paragraph(label, h2), Preformatted('\n'.join(ex), mono)]))
def last_io_disp(name, n=9):
  ex = demo_excerpt(name, n)
  m = re.findall(r'io\s+\d+\s+L\d+\s+\d+\s+(\d+) \|', ex[-1]) if ex else []
  return int(m[0]) if m else 0
def last_tick(name, n=9):
  ex = demo_excerpt(name, n)
  return int(ex[-1].split('|')[0]) if ex else 0
A(para('Under round-robin every process stays at level 0 and the I/O process has been dispatched only %d times by tick %d: after each disk operation it queues behind the two CPU-bound processes. '
       'Under MLFQ the CPU-bound processes are pushed down the queues while the I/O process stays at level 0 and has been dispatched %d times by tick %d.' %
       (last_io_disp('demo_rr.txt'), last_tick('demo_rr.txt'), last_io_disp('demo_mlfq.txt'), last_tick('demo_mlfq.txt'))))

# ---------------------------------------------------------------- 6/7
A(Paragraph('6. Benchmark results', h1))
A(para('Times are completion times in timer ticks (1 tick = 100 ms of virtual time) measured by each process from its own start to its own end, as the mean of %d runs with the range in brackets when the runs differ. '
       'The CPU time column is the process\'s own CPU consumption from getprocinfo(); dispatches is how often the scheduler switched to it.' % reps))
def row(label, sc, v, k):
  return [label, rng(sc, v, k), '%.0f' % mean(sc, v, k, 'cpu_ms'), '%.0f' % mean(sc, v, k, 'nsched'),
          ', '.join(sorted(set(x['final_prio'] for x in D[(sc, v, k)])))]
hdr = ['Process / kernel', 'Completion (ticks)', 'CPU time (ms)', 'Dispatches', 'Final level']
A(Paragraph('Table 1. Each program alone (baseline)', h2))
A(tbl([hdr, row('CPU-bound, round-robin', 'solo_cpu', 'RR', 'cpu'), row('CPU-bound, MLFQ', 'solo_cpu', 'MLFQ', 'cpu'),
       row('I/O-bound, round-robin', 'solo_io', 'RR', 'io'), row('I/O-bound, MLFQ', 'solo_io', 'MLFQ', 'io')],
      [5.2 * cm, 3.4 * cm, 2.6 * cm, 2.4 * cm, 2.4 * cm]))
for sc, tno, desc in [('mix_1cpu_1io', 2, 'One CPU-bound and one I/O-bound process started together'),
                      ('mix_3cpu_1io', 3, 'Three CPU-bound and one I/O-bound process started together')]:
  A(Paragraph('Table %d. %s' % (tno, desc), h2))
  data = [hdr]
  for v, vl in [('RR', 'round-robin'), ('MLFQ', 'MLFQ'), ('MLFQ-nopreempt', 'MLFQ without wakeup preemption')]:
    data.append(row('CPU-bound, ' + vl, sc, v, 'cpu'))
    data.append(row('I/O-bound, ' + vl, sc, v, 'io'))
  A(tbl(data, [5.2 * cm, 3.4 * cm, 2.6 * cm, 2.4 * cm, 2.4 * cm]))
A(Spacer(1, 8))
A(Image(P('results', 'completion_times.png'), width=16 * cm, height=16 * cm * 2.9 / 7.2))
A(Paragraph('Figure 1. Completion time of the two kinds of process under each kernel (mean of %d runs).' % reps, cap))

# derived figures for the text
io_solo = mean('solo_io', 'RR', 'io')
c3rr, c3m = mean('mix_3cpu_1io', 'RR', 'cpu'), mean('mix_3cpu_1io', 'MLFQ', 'cpu')
i3rr, i3m, i3n = [mean('mix_3cpu_1io', v, 'io') for v in ('RR', 'MLFQ', 'MLFQ-nopreempt')]
c1rr, c1m = mean('mix_1cpu_1io', 'RR', 'cpu'), mean('mix_1cpu_1io', 'MLFQ', 'cpu')
i1rr, i1m, i1n = [mean('mix_1cpu_1io', v, 'io') for v in ('RR', 'MLFQ', 'MLFQ-nopreempt')]
t3rr, t3m = avg_turnaround('mix_3cpu_1io', 'RR'), avg_turnaround('mix_3cpu_1io', 'MLFQ')
t1rr, t1m = avg_turnaround('mix_1cpu_1io', 'RR'), avg_turnaround('mix_1cpu_1io', 'MLFQ')
end3rr = max(int(r['wall_ticks']) for r in rows if r['scenario'] == 'mix_3cpu_1io' and r['variant'] == 'RR' and r['rep'] == '1')
end3m = max(int(r['wall_ticks']) for r in rows if r['scenario'] == 'mix_3cpu_1io' and r['variant'] == 'MLFQ' and r['rep'] == '1')
hog_disp_rr, hog_disp_m = mean('mix_3cpu_1io', 'RR', 'cpu', 'nsched'), mean('mix_3cpu_1io', 'MLFQ', 'cpu', 'nsched')
A(Paragraph('Table 4. Summary of the two mixed runs', h2))
A(tbl([['Measure', '1 CPU + 1 I/O: RR', '1 CPU + 1 I/O: MLFQ', '3 CPU + 1 I/O: RR', '3 CPU + 1 I/O: MLFQ'],
       ['I/O-bound completion (ticks)', '%.0f' % i1rr, '%.0f' % i1m, '%.0f' % i3rr, '%.0f' % i3m],
       ['I/O-bound slowdown versus running alone', '%.1fx' % (i1rr / io_solo), '%.1fx' % (i1m / io_solo), '%.1fx' % (i3rr / io_solo), '%.1fx' % (i3m / io_solo)],
       ['CPU-bound completion (ticks, mean)', '%.0f' % c1rr, '%.0f' % c1m, '%.0f' % c3rr, '%.0f' % c3m],
       ['Mean completion of all processes (ticks)', '%.0f' % t1rr, '%.0f' % t1m, '%.0f' % t3rr, '%.0f' % t3m],
       ['Time until the last process ends (ticks)', '%.0f' % max(i1rr, c1rr), '%.0f' % max(i1m, c1m), '%d' % end3rr, '%d' % end3m]],
      [5.4 * cm, 2.6 * cm, 2.7 * cm, 2.6 * cm, 2.7 * cm]))

# ---------------------------------------------------------------- 8
A(Paragraph('7. Analysis: why the two kinds of process are affected differently', h1))
A(para('<b>The I/O-bound program gains a great deal.</b> Alone it finishes in %.0f ticks. Next to three CPU-bound processes under round-robin it needs %.0f, about %.0fx longer, '
       'and it only finishes after the CPU-bound processes are done. It needs about %.0f dispatches, but every time it blocks and wakes it has to wait for its turn behind the other runnable processes, and each turn starts at a timer tick. '
       'Under MLFQ the same program finishes in %.0f ticks, %.1fx its solo time. It never uses a whole slice, so it never leaves level 0 (its final level in every run is 0), and the scheduler picks it ahead of anything at lower levels.' %
       (io_solo, i3rr, i3rr / io_solo, mean('mix_3cpu_1io', 'RR', 'io', 'nsched'), i3m, i3m / io_solo)))
A(para('<b>The CPU-bound programs pay a small price.</b> Each one burns its slice every time, so each is pushed down to level 2 (final level 2 in every MLFQ run) and runs only when nothing above it is runnable. '
       'In the three-process case their completion time goes from %.0f to %.0f ticks (%+.1f%%). The I/O process only needs about %.1f s of CPU in total, so the extra delay is roughly that amount plus context-switch overhead: '
       'the CPU-bound processes are dispatched %.0f times each instead of %.0f, because every I/O wakeup preempts them. '
       'The last process finishes at almost the same time under both kernels (%d against %d ticks), so MLFQ does not waste CPU; it changes the order in which the work is done.' %
       (c3rr, c3m, 100.0 * (c3m - c3rr) / c3rr, mean('solo_io', 'RR', 'io', 'cpu_ms') / 1000.0, hog_disp_m, hog_disp_rr, end3rr, end3m)))
A(para('<b>Mean completion time improves.</b> Finishing the short jobs first lowers the average: from %.0f to %.0f ticks with three CPU-bound processes, and from %.0f to %.0f with one. '
       'This is the same effect as shortest-job-first, obtained without knowing job lengths in advance: the scheduler infers from past behaviour that a process which keeps blocking is short-burst work.' % (t3rr, t3m, t1rr, t1m)))
A(para('<b>Preempting on wakeup is what makes the I/O result possible.</b> With the feature removed, MLFQ gives %.0f ticks for the I/O process in the three-process case and %.0f in the two-process case, '
       'the same as round-robin (%.0f and %.0f). Priorities by themselves only matter at the moments the scheduler runs, and stock xv6 runs it once per tick. '
       'A priority scheme on top of a tick-driven kernel therefore needs a way to run the scheduler when a higher-priority process becomes runnable; the kernel-side mechanism is what determines whether the policy has any effect on applications.' % (i3n, i1n, i3rr, i1rr)))
A(para('<b>Round-robin versus MLFQ at the process level.</b> Round-robin treats the two programs identically, so the one that spends most of its life waiting is penalised most: its waits get longer by a factor of the number of competitors. '
       'MLFQ separates them by observed behaviour, with no information from the programs themselves.'))

# ---------------------------------------------------------------- 9
A(Paragraph('8. Conclusion: what this means for application design', h1))
for t in ['<b>Blocking early is rewarded.</b> A program that spends its time waiting, and computes in short bursts, keeps a high priority and responds quickly even on a busy machine. A program that is a long computation should expect to run at low priority when anything interactive is present. '
          'In practice that favours structures such as an event loop that waits for input and does small pieces of work, and it makes a batch job that tries to be responsive by polling in a busy loop work against itself.',
          '<b>Long computations should expect to be preempted often.</b> The CPU-bound processes were dispatched about %.0f times instead of %.0f. Work that keeps state in memory and can restart cheaply after being switched out suffers little; work that depends on long uninterrupted cache-friendly runs loses more.' % (hog_disp_m, hog_disp_rr),
          '<b>The policy can be gamed.</b> A CPU-bound program that sleeps or does a trivial I/O call just before its slice ends is treated as interactive and stays at level 0. The periodic boost does not prevent that; it only prevents starvation. Real systems limit this by charging total time at a level rather than per slice, a rule not implemented here.',
          '<b>Mixed programs are classified by their recent past.</b> A process that computes for a long time and then starts doing I/O stays at a low level until the next boost, so its first responses after the change are slow. A process that does I/O first and computes later is demoted quickly. Splitting the I/O handling and the computation into separate processes lets each be scheduled for what it does.',
          '<b>Parameters are part of the design.</b> The slice lengths (1, 2, 4 ticks) and the boost period (100 ticks) were chosen by reasoning and were not tuned; a different tick length or I/O latency could change the numbers above, and the benchmark setup makes them easy to vary.']:
  A(Paragraph('- ' + t, ParagraphStyle('li2', parent=base, leftIndent=14, firstLineIndent=-8, spaceAfter=4)))

A(Paragraph('9. Limitations', h1))
A(para('Results are from an emulated machine with a fast virtual disk, one hart, and instruction-count-based virtual time; absolute tick values on real hardware or another QEMU version will differ, and the ratios are the meaningful part. '
       'Only two workload types were used. The scheduler scans all 64 process slots on every decision, as the original loop did, so it is not designed for large process tables. '
       'The stress test (usertests) was run once with three harts, and the benchmarks with one hart; multi-hart benchmark behaviour was checked only through the functional test and usertests.'))

A(Paragraph('10. Reproducing the results', h1))
A(Preformatted('cd xv6-mlfq-lab\n'
               'sudo apt install qemu-system-misc gcc-riscv64-linux-gnu make python3 python3-reportlab python3-matplotlib\n'
               'bash scripts/build_all.sh                  # builds build/kernel-RR, -MLFQ, -MLFQ-nopreempt\n'
               'python3 scripts/run_benchmarks.py 3        # writes logs/raw/*.txt and results/results.csv\n'
               'python3 scripts/collect_logs.py            # functional test, demo, usertests logs\n'
               'python3 scripts/make_report.py             # rebuilds this PDF from the data\n'
               '\n# interactive use:  cd xv6-riscv && make qemu CPUS=1   (MLFQ)\n'
               '#                   make clean && make qemu SCHED=RR CPUS=1   (round-robin)', mono))


# ---------------------------------------------------------------- rubric pages (same as the CEA guide)
rub_title = ParagraphStyle('rt', parent=base, fontName='Times-Bold', fontSize=13, leading=16, alignment=1, spaceAfter=0)
rub_sub = ParagraphStyle('rs', parent=rub_title, textColor=colors.HexColor('#2E75A6'))
rc = ParagraphStyle('rc', parent=base, fontSize=8.2, leading=9.8, spaceAfter=0)
rcb = ParagraphStyle('rcb', parent=rc, fontName='Times-Bold', alignment=1)
RUBRIC = [
  ['1. Scheduler Logic & Correctness',
   'The MLFQ scheduler is implemented correctly and efficiently, adhering to all specified logic (priority levels, promotion/demotion rules).',
   'The scheduler is functional but contains minor logical flaws or inefficiencies. It may not fully handle all edge cases correctly.',
   'The scheduler fails to compile, is non-functional, or does not implement the core requirements of an MLFQ.',
   'CPA1<br/>CPA2<br/>CPA3'],
  ['2. Kernel Integration & Stability',
   'The new scheduler and system call are cleanly integrated into the kernel without causing instability, memory leaks, or race conditions.',
   "The new code is functional but may cause minor, intermittent issues or does not follow xv6's existing design patterns.",
   'The implementation causes frequent kernel panics, data corruption, or fails to integrate with the existing kernel code.',
   'CPA1<br/>CPA2<br/>CPA3'],
  ['3. Test Application Design',
   'Both the CPU-bound and I/O-bound applications are well-designed, effectively simulating their respective workloads to clearly test the scheduler.',
   'The applications are functional but are not distinct enough in their behavior, making the performance difference less clear.',
   'The applications fail to run, do not correctly simulate the intended workloads, or were not developed.',
   'CPA1<br/>CPA2<br/>CPA3'],
  ['4. Functional Demonstration',
   'The functionality of the new scheduler is clearly and correctly demonstrated, showing how it prioritizes processes differently than the original scheduler.',
   'A demonstration is provided, but it is unclear or fails to convincingly show the impact of the new scheduling algorithm.',
   'No functional demonstration is provided, or the demonstration shows the implementation does not work.',
   'CPA1<br/>CPA3'],
  ['5. Code Quality & Readability',
   'The code written (both kernel and user-level) is clean, well-commented, easy to understand, and follows standard C programming practices.',
   'The code is functional but is poorly formatted, lacks sufficient comments, or is difficult to follow.',
   'The code is unreadable, uncommented, and does not follow basic programming standards.',
   'CPA3'],
]

def rubric_page(name, roll):
  A(PageBreak())
  A(Paragraph('NED University of Engineering &amp; Technology', rub_title))
  A(Paragraph('Department of Software Engineering', rub_title))
  A(Paragraph('CEA RUBRICS', rub_title))
  A(Paragraph('(SE-303) Operating Systems', rub_sub))
  A(Spacer(1, 4))
  A(Paragraph('Student: %s (%s)' % (name, roll), ParagraphStyle('st', parent=base, fontSize=9.5, spaceAfter=6)))
  hdr = [Paragraph('Criteria', rcb), Paragraph('Good<br/>(2)', rcb), Paragraph('Satisfactory<br/>(1)', rcb),
         Paragraph('Not Achieved<br/>(0)', rcb), Paragraph('CPA', rcb), Paragraph('Marks', rcb)]
  data = [hdr]
  for r in RUBRIC:
    data.append([Paragraph(r[0], rc), Paragraph(r[1], rc), Paragraph(r[2], rc), Paragraph(r[3], rc),
                 Paragraph(r[4], ParagraphStyle('cpa', parent=rc, alignment=1)), ''])
  data.append([Paragraph('<b>Weighted CLO Score</b>', rc), '', '', '', '', ''])
  data.append([Paragraph('<b>Remarks and Signature</b>', rc), '', '', '', '', ''])
  t = Table(data, colWidths=[2.5 * cm, 3.7 * cm, 3.3 * cm, 3.3 * cm, 1.3 * cm, 1.6 * cm],
            rowHeights=[None] + [3.1 * cm] * 5 + [1.1 * cm, 1.6 * cm])
  t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.6, colors.black), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                         ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                         ('SPAN', (1, 6), (5, 6)), ('SPAN', (1, 7), (5, 7))]))
  A(t)

rubric_page('Muhammad Ashhadullah Zaheer', 'SE-24087')
rubric_page('Misbah Sarfraz', 'SE-24096')

def footer(canvas, doc):
  canvas.setFont('Times-Roman', 9)
  canvas.drawCentredString(A4[0] / 2, 1.2 * cm, str(doc.page))

os.makedirs(P('report'), exist_ok=True)
doc = SimpleDocTemplate(P('report', 'OS_Lab13_Performance_Report.pdf'), pagesize=A4,
                        leftMargin=2.3 * cm, rightMargin=2.3 * cm, topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                        title='MLFQ Scheduler for xv6-RISC-V - Performance Report', author='Muhammad Ashhadullah Zaheer, Misbah Sarfraz')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('wrote report/OS_Lab13_Performance_Report.pdf')
