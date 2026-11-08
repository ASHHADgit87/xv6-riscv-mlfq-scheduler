// Shared workload kernels for cpubound, iobound and bench.
// Header-only (static functions) because xv6 has no shared library support.

// Volatile sink: without a side effect the compiler deletes the whole loop
// when the caller ignores the return value (it did, and the "CPU hog"
// finished in 0 ms). Writing the result here keeps the work real.
static volatile int prime_sink;

// ---- CPU-bound: count primes in [2, limit) by trial division ----
// Pure ALU work with zero system calls, so the process never blocks and
// always burns its whole time slice (the worst case for MLFQ demotion).
static __attribute__((unused)) int
count_primes(int limit)
{
  int count = 0;
  for (int n = 2; n < limit; n++) {
    int prime = 1;
    for (int d = 2; d * d <= n; d++) {
      if (n % d == 0) {
        prime = 0;
        break;
      }
    }
    count += prime;
  }
  prime_sink = count;
  return count;
}

// ---- I/O-bound: create, write, close and delete small files ----
// Every iteration does several syscalls that block on the virtio disk
// (log commit), so the process voluntarily sleeps long before its slice ends.
// Returns number of bytes written, or -1 on error.
static __attribute__((unused)) int
file_churn(int pid, int iterations)
{
  char name[16];
  char buf[64];
  int total = 0;

  for (int i = 0; i < sizeof(buf); i++)
    buf[i] = 'a' + (i % 26);

  // Build the name "io<pid>" by hand (xv6 has no snprintf).
  name[0] = 'i';
  name[1] = 'o';
  int len = 2;
  char digits[12];
  int nd = 0;
  int v = pid;
  do {
    digits[nd++] = '0' + (v % 10);
    v /= 10;
  } while (v > 0);
  while (nd > 0)
    name[len++] = digits[--nd];
  name[len] = 0;

  for (int i = 0; i < iterations; i++) {
    int fd = open(name, O_CREATE | O_WRONLY);
    if (fd < 0)
      return -1;
    for (int k = 0; k < 4; k++) {
      if (write(fd, buf, sizeof(buf)) != sizeof(buf)) {
        close(fd);
        return -1;
      }
      total += sizeof(buf);
    }
    close(fd);
    if (unlink(name) < 0)
      return -1;
  }
  return total;
}
