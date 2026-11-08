#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "riscv.h"
#include "defs.h"

void
plicinit(void)
{
  *(volatile uint32 *)(PLIC + UART0_IRQ * 4) = 1;
  *(volatile uint32 *)(PLIC + VIRTIO0_IRQ * 4) = 1;
}

void
plicinithart(void)
{
  int hart = cpuid();

  *(volatile uint32 *)PLIC_SENABLE(hart) =
    (1 << UART0_IRQ) | (1 << VIRTIO0_IRQ);

  *(volatile uint32 *)PLIC_SPRIORITY(hart) = 0;
}

int
plic_claim(void)
{
  int hart = cpuid();
  int irq = *(volatile uint32 *)PLIC_SCLAIM(hart);
  return irq;
}

void
plic_complete(int irq)
{
  int hart = cpuid();
  *(volatile uint32 *)PLIC_SCLAIM(hart) = irq;
}
