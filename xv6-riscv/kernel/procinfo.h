// Performance snapshot returned by getprocinfo().
// Shared by the kernel and user programs, so it uses only plain ints.
#define PINFO_LEVELS 3
#define NQUEUE_LAST  (PINFO_LEVELS - 1)

struct procinfo {
  int pid;
  int state;                    // enum procstate value of the target
  int sched_mode;               // 0 = round-robin build, 1 = MLFQ build
  int priority;                 // current queue, 0 = highest
  int cpu_ticks;                // CPU time consumed, in timer ticks (1 tick = 100 ms)
  int cpu_ms;                   // same CPU time in milliseconds (finer grained)
  int nsched;                   // times the scheduler switched to it
  int level_ms[PINFO_LEVELS];   // CPU ms spent in each queue level
};
