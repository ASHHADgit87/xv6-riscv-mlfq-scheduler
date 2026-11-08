// mlfqdemo - visual demonstration of scheduler behaviour.
// Starts 2 CPU hogs and 1 I/O job, then the parent samples every 2 ticks and
// prints each child's queue level and CPU ticks. Under MLFQ the hogs sink to
// level 2 while the I/O job stays at level 0; under RR everything stays at 0.
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
  int pids[3];
  char *role[3] = {"cpu-A", "cpu-B", "io   "};

  int t0 = uptime();
  for (int i = 0; i < 3; i++) {
    pids[i] = fork();
    if (pids[i] == 0) {
      if (i < 2)
        count_primes(limit);
      else
        file_churn(getpid(), 100);
      exit(0);
    }
  }

  printf("tick  | %s pid prio cpu_ticks nsched | %s pid prio cpu_ticks nsched | %s pid prio cpu_ticks nsched\n",
         role[0], role[1], role[2]);
  int alive = 3;
  while (alive > 0) {
    pause(2);
    printf("%d |", uptime() - t0);
    alive = 0;
    for (int i = 0; i < 3; i++) {
      struct procinfo pi;
      if (getprocinfo(pids[i], &pi) == 0 && pi.state != 5) {  // 5 = ZOMBIE
        printf(" %s %d  L%d  %d  %d |", role[i], pi.pid, pi.priority, pi.cpu_ticks, pi.nsched);
        alive++;
      } else {
        printf(" %s done |", role[i]);
      }
    }
    printf("\n");
  }
  for (int i = 0; i < 3; i++)
    wait(0);
  printf("DEMO_DONE\n");
  exit(0);
}
