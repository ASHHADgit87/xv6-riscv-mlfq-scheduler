#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "kernel/procinfo.h"
#include "user/user.h"
#include "user/workloads.h"

int
main(int argc, char *argv[])
{
  int iters = argc > 1 ? atoi(argv[1]) : 100;
  struct procinfo pi;

  int t0 = uptime();
  int bytes = file_churn(getpid(), iters);
  int t1 = uptime();

  if (bytes < 0 || getprocinfo(0, &pi) < 0) {
    printf("iobound: failed\n");
    exit(1);
  }
  printf("iobound pid=%d iters=%d bytes=%d wall=%d ticks cpu=%d ticks (%d ms) sched=%d prio=%d (mode %s)\n",
         pi.pid, iters, bytes, t1 - t0, pi.cpu_ticks, pi.cpu_ms, pi.nsched, pi.priority,
         pi.sched_mode ? "MLFQ" : "RR");
  exit(0);
}
