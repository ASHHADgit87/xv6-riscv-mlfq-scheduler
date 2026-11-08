# xv6-riscv-mlfq-scheduler

**xv6-riscv-mlfq-scheduler** is a custom operating system scheduling implementation built with **C, RISC-V Assembly, QEMU, and Python**. It replaces the default round-robin scheduler in the xv6 kernel with a Multi-Level Feedback Queue (MLFQ). Every process is dynamically prioritized, monitored with accurate CPU accounting, and managed to prevent starvation while prioritizing I/O-bound interactive tasks.

---

# Problem Statement

Standard xv6 uses a simple round-robin scheduling policy where every runnable process receives the CPU in turn, regardless of its behavior.

This uniform approach heavily penalizes I/O-bound applications. When a process finishes waiting for a disk operation, it must wait behind all CPU-heavy processes, resulting in massive latency and poor interactive responsiveness.

A Multi-Level Feedback Queue (MLFQ) solves this by isolating processes based on their observed behavior, assigning shorter time slices to interactive tasks and longer time slices to background computations, ensuring efficient CPU utilization without requiring application-level hints.

---

# Core Integration

xv6-riscv-mlfq-scheduler uses **C**, **RISC-V Assembly**, **QEMU Emulator**, and **Python** to deliver a secure, high-performance widget platform.

### Stack Integration

| Component         | Role                                                           |
| ----------------- | -------------------------------------------------------------- |
| `C`               | Primary kernel and user-space application logic                |
| `RISC-V Assembly` | Low-level trap handling and context switching                  |
| `QEMU`            | Virtualization and hardware emulation                          |
| `Makefile`        | Compilation pipeline and emulator initialization               |
| `Python 3`        | Automated benchmarking, log parsing, and PDF report generation |
| `Matplotlib`      | Data visualization for scheduler performance                   |
| `ReportLab`       | Programmatic PDF construction                                  |

---

### Request Pipeline

Timer Interrupt → Context Switch → Update CPU Accounting → Evaluate Slice/Block → Adjust Priority Level → Dispatch Next Process

---

# Architecture

xv6-riscv-mlfq-scheduler follows a **hardware-to-user-space OS architecture**:

| Layer                 | Technology                                                          |
| --------------------- | ------------------------------------------------------------------- |
| User Space            | C binaries (`mlfqtest`, `mlfqdemo`, `bench`, `cpubound`, `iobound`) |
| System Call Interface | ECALL trap handlers (`sys_getprocinfo`)                             |
| Kernel Space          | xv6 process management (`proc.c`, `trap.c`, `scheduler`)            |
| Hardware Emulation    | QEMU (1 Hart, 128 MB RAM, Virtio Disk, Deterministic Timer)         |
| Toolchain             | riscv64-linux-gnu-gcc                                               |
| Analytics             | Python scripts (`run_benchmarks.py`, `make_report.py`)              |

---

# BaaS

xv6-riscv-mlfq-scheduler is delivered as a **Core Kernel Modification**. Developers compile the operating system and boot it via hardware emulation. Processes are automatically managed by the MLFQ logic, and their runtime metrics are exposed to user space via a custom kernel system call.

---

# Features

### Scheduler System

| Capability          | Detail                                                                       |
| ------------------- | ---------------------------------------------------------------------------- |
| Priority levels     | 3 dynamic levels (0, 1, 2) with Level 0 being the highest                    |
| Dynamic time slices | 1, 2, and 4 ticks for levels 0, 1, and 2 respectively                        |
| Priority demotion   | Processes consuming their full time slice are moved to a lower priority      |
| Periodic boosting   | All processes return to Level 0 every 100 ticks to prevent starvation        |
| Wakeup preemption   | I/O processes waking up immediately preempt lower-priority running processes |
| Run-time accounting | Microsecond-accurate CPU time tracking via RISC-V time registers             |

### Security & Hardening

| Capability         | Detail                                                                      |
| ------------------ | --------------------------------------------------------------------------- |
| System call        | `getprocinfo` retrieves detailed execution metrics from the kernel          |
| State tracking     | Captures process state, current queue, and scheduler mode                   |
| Dispatch counting  | Records the exact number of times a process was scheduled                   |
| Level distribution | Tracks milliseconds spent computing at each priority level                  |
| Input validation   | Prevents out-of-bounds metrics manipulation in user space                   |
| Tenant isolation   | Process data fully isolated within `struct proc` and protected by `p->lock` |

### Analytics & Dashboard

| Capability           | Detail                                                                 |
| -------------------- | ---------------------------------------------------------------------- |
| Workload simulation  | Isolated `cpubound` and `iobound` programs to test edge cases          |
| Concurrent execution | `bench` orchestrates N CPU and M I/O processes simultaneously          |
| Deterministic timing | QEMU `-icount` shift ensures repeatable virtual time across runs       |
| Automated reporting  | Python scripts execute QEMU, extract logs, and compile a formatted PDF |
| Profile management   | Exposes `nsched` and `cpu_ticks` directly to user processes            |

### 3D Backgrounds

| Capability     | Detail                                                            |
| -------------- | ----------------------------------------------------------------- |
| Not Applicable | Kernel modification running entirely in headless emulated console |

### Data Model

| Entity            | Key Fields                                                     |
| ----------------- | -------------------------------------------------------------- |
| `struct proc`     | `pid`, `state`, `lock`, `level`, `ticks`, `nsched`, `level_ms` |
| `struct procinfo` | `pid`, `state`, `cpu_ticks`, `cpu_ms`, `nsched`, `level_ms[3]` |

---

# API Reference

| Method    | Path              | Access     | Purpose                                                                 |
| --------- | ----------------- | ---------- | ----------------------------------------------------------------------- |
| `SYSCALL` | `sys_getprocinfo` | User Space | Populates the struct with the target process's exact scheduling metrics |

---

# Processing Capability

| Capability           | Detail                                                                            |
| -------------------- | --------------------------------------------------------------------------------- |
| Concurrent processes | Up to 64 simultaneous processes (xv6 `NPROC` limit)                               |
| CPU architecture     | Tested and verified on single-hart (1 CPU) and multi-hart (3 CPUs) configurations |
| Resolution           | 1,000,000 cycles = 100 ms of virtual time                                         |
| Functional tests     | 17 strict kernel assertions executed via `mlfqtest`                               |
| Stability            | Fully passes the native xv6 `usertests -q` suite with no kernel panics            |

---

# Tech Stack

| Layer            | Technology                    |
| ---------------- | ----------------------------- |
| Operating System | xv6-riscv                     |
| Language         | C, RISC-V Assembly            |
| Build System     | GNU Make                      |
| Emulation        | QEMU                          |
| Compiler         | gcc-riscv64-linux-gnu         |
| Scripting        | Python 3, Bash                |
| Data Processing  | Pandas, Matplotlib, ReportLab |

---

# Live Demo

Execution Instructions:

```bash
sudo apt install build-essential qemu-system-misc gcc-riscv64-linux-gnu python3
make clean
make qemu CPUS=1

# Inside xv6:
$mlfqtest$ bench 3 1

```

---

## Creator & Developer

- **Muhammad Ashhadullah Zaheer**
- LinkedIn: https://www.linkedin.com/in/muhammad-ashhadullah-zaheer-41194a340/
- **Misbah Sarfraz**
- Co-Creator & Infrastructure Developer
