// cpubound [limit]  - standalone CPU-bound benchmark (prime counting).
#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "kernel/procinfo.h"
#include "user/user.h"
#include "user/workloads.h"

int
main(int argc, char *argv[])
{
  int limit = argc > 1 ? atoi(argv[1]) : 4000000;
  struct procinfo pi;

  int t0 = uptime();
  int primes = count_primes(limit);
  int t1 = uptime();

  if (getprocinfo(0, &pi) < 0) {
    printf("cpubound: getprocinfo failed\n");
    exit(1);
  }
  printf("cpubound pid=%d primes<%d=%d wall=%d ticks cpu=%d ticks (%d ms) sched=%d prio=%d (mode %s)\n",
         pi.pid, limit, primes, t1 - t0, pi.cpu_ticks, pi.cpu_ms, pi.nsched, pi.priority,
         pi.sched_mode ? "MLFQ" : "RR");
  exit(0);
}
