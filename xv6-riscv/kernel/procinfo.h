#define PINFO_LEVELS 3
#define NQUEUE_LAST  (PINFO_LEVELS - 1)

struct procinfo {
  int pid;
  int state;
  int sched_mode;
  int priority;
  int cpu_ticks;
  int cpu_ms;
  int nsched;
  int level_ms[PINFO_LEVELS];
};
