// mlfqtest - functional tests for the MLFQ scheduler and getprocinfo().
// Prints PASS/FAIL per check. Meaningful only on the MLFQ build.
#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "kernel/procinfo.h"
#include "user/user.h"
#include "user/workloads.h"

static int failures = 0;

static void
check(char *name, int ok)
{
  printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok)
    failures++;
}

// Spin for about n timer ticks without making any syscall that could block.
static void
spin_ticks(int n)
{
  int end = uptime() + n;
  volatile int x = 0;
  (void)x;
  while (uptime() < end)
    x++;
}

int
main(void)
{
  struct procinfo pi, pj;

  // 1. getprocinfo basics
  check("getprocinfo(self) succeeds", getprocinfo(0, &pi) == 0);
  check("reported pid equals getpid()", pi.pid == getpid());
  check("running on MLFQ build", pi.sched_mode == 1);
  check("new process starts at top priority (0)", pi.priority == 0);
  check("nsched >= 1 for a running process", pi.nsched >= 1);
  check("getprocinfo(explicit own pid) matches", getprocinfo(getpid(), &pj) == 0 && pj.pid == pi.pid);
  check("getprocinfo(bad pid 99999) returns -1", getprocinfo(99999, &pj) == -1);
  check("getprocinfo(bad pointer) returns -1", getprocinfo(0, (struct procinfo *)0xFFFFFFFFFFULL) == -1);

  // 2. CPU hog is demoted and its counters grow
  int before = pi.cpu_ticks;
  spin_ticks(6);
  getprocinfo(0, &pi);
  check("cpu_ticks grows while spinning", pi.cpu_ticks > before);
  check("CPU hog demoted below level 0", pi.priority > 0);
  check("CPU hog reaches the bottom queue", pi.priority == NQUEUE_LAST);
  int sum = 0;
  for (int i = 0; i < PINFO_LEVELS; i++)
    sum += pi.level_ms[i];
  // per-level values are truncated separately, so allow a few ms of rounding
  check("level_ms add up to cpu_ms", sum <= pi.cpu_ms && pi.cpu_ms - sum <= 3);
  check("time spent in bottom queue is recorded", pi.level_ms[NQUEUE_LAST] > 0);

  // 3. Child of a demoted parent starts fresh at the top
  int p2c[2];
  pipe(p2c);
  int pid = fork();
  if (pid == 0) {
    struct procinfo ci;
    getprocinfo(0, &ci);
    write(p2c[1], &ci.priority, sizeof(int));
    exit(0);
  }
  int child_prio = -1;
  read(p2c[0], &child_prio, sizeof(int));
  wait(0);
  check("child of demoted parent starts at priority 0", child_prio == 0);

  // 4. I/O-bound process keeps its priority (no demotion for yielding)
  pid = fork();
  if (pid == 0) {
    struct procinfo ci;
    file_churn(getpid(), 40);
    getprocinfo(0, &ci);
    int ok = ci.priority == 0 ? 1 : 0;
    write(p2c[1], &ok, sizeof(int));
    exit(0);
  }
  int io_ok = 0;
  read(p2c[0], &io_ok, sizeof(int));
  wait(0);
  check("I/O-bound process stays at priority 0", io_ok == 1);

  // 5. Sleeping process keeps its level
  pid = fork();
  if (pid == 0) {
    struct procinfo ci;
    for (int i = 0; i < 8; i++)
      pause(1);
    getprocinfo(0, &ci);
    int ok = ci.priority == 0 ? 1 : 0;
    write(p2c[1], &ok, sizeof(int));
    exit(0);
  }
  int sl_ok = 0;
  read(p2c[0], &sl_ok, sizeof(int));
  wait(0);
  check("sleeping process stays at priority 0", sl_ok == 1);

  // 6. Priority boost lifts the hog back to level 0 eventually
  getprocinfo(0, &pi);
  int boosted = 0;
  int deadline = uptime() + 250;
  while (uptime() < deadline && !boosted) {
    pause(1);                       // sleep so we do not demote again meanwhile
    getprocinfo(0, &pi);
    if (pi.priority == 0)
      boosted = 1;
  }
  check("periodic boost returns demoted process to level 0", boosted);

  printf(failures ? "RESULT: %d check(s) FAILED\n" : "RESULT: all checks passed\n", failures);
  exit(failures ? 1 : 0);
}
