// bench <ncpu> <nio> [primelimit] [iters]
// Runs ncpu CPU-bound and nio I/O-bound children AT THE SAME TIME and prints
// one CSV-style line per child plus a summary. Each child reports back through
// a pipe so console output from different processes never interleaves.
#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "kernel/procinfo.h"
#include "user/user.h"
#include "user/workloads.h"

struct result {
  int kind;       // 0 = cpu, 1 = io
  int pid;
  int start;      // uptime when the child began its workload
  int end;        // uptime when it finished
  int cpu_ticks;
  int cpu_ms;
  int nsched;
  int prio;
  int level_ms[PINFO_LEVELS];
  int mode;
};

int
main(int argc, char *argv[])
{
  int ncpu = argc > 1 ? atoi(argv[1]) : 1;
  int nio = argc > 2 ? atoi(argv[2]) : 1;
  int limit = argc > 3 ? atoi(argv[3]) : 4000000;
  int iters = argc > 4 ? atoi(argv[4]) : 100;
  int total = ncpu + nio;
  int fds[2];

  if (total < 1 || total > 30) {
    printf("bench: bad process count\n");
    exit(1);
  }
  pipe(fds);

  int t_start = uptime();
  for (int i = 0; i < total; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("bench: fork failed\n");
      exit(1);
    }
    if (pid == 0) {
      struct result r;
      struct procinfo pi;
      close(fds[0]);
      r.kind = i < ncpu ? 0 : 1;
      r.start = uptime();
      if (r.kind == 0)
        count_primes(limit);
      else if (file_churn(getpid(), iters) < 0)
        exit(1);
      r.end = uptime();
      getprocinfo(0, &pi);
      r.pid = pi.pid;
      r.cpu_ticks = pi.cpu_ticks;
      r.cpu_ms = pi.cpu_ms;
      r.nsched = pi.nsched;
      r.prio = pi.priority;
      r.mode = pi.sched_mode;
      for (int k = 0; k < PINFO_LEVELS; k++)
        r.level_ms[k] = pi.level_ms[k];
      write(fds[1], &r, sizeof(r));
      exit(0);
    }
  }
  close(fds[1]);

  printf("kind,pid,wall_ticks,cpu_ms,nsched,final_prio,l0_ms,l1_ms,l2_ms\n");
  struct result r;
  int cpu_wall = 0, io_wall = 0, cpu_n = 0, io_n = 0, cpu_cpu = 0, io_cpu = 0;
  int mode = -1;
  while (read(fds[0], &r, sizeof(r)) == sizeof(r)) {
    int wall = r.end - r.start;
    printf("%s,%d,%d,%d,%d,%d,%d,%d,%d\n", r.kind ? "io" : "cpu", r.pid, wall,
           r.cpu_ms, r.nsched, r.prio, r.level_ms[0], r.level_ms[1],
           r.level_ms[2]);
    mode = r.mode;
    if (r.kind == 0) {
      cpu_wall += wall; cpu_cpu += r.cpu_ms; cpu_n++;
    } else {
      io_wall += wall; io_cpu += r.cpu_ms; io_n++;
    }
  }
  while (wait(0) > 0)
    ;
  int t_end = uptime();
  printf("SUMMARY mode=%s ncpu=%d nio=%d total_wall=%d avg_cpu_wall=%d avg_io_wall=%d avg_cpu_ms_cpu=%d avg_cpu_ms_io=%d\n",
         mode ? "MLFQ" : "RR", ncpu, nio, t_end - t_start,
         cpu_n ? cpu_wall / cpu_n : 0, io_n ? io_wall / io_n : 0,
         cpu_n ? cpu_cpu / cpu_n : 0, io_n ? io_cpu / io_n : 0);
  printf("BENCH_DONE\n");
  exit(0);
}
