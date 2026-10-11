#include <assert.h>
#include <stdio.h>
#include "mc6809/mc6809.c"
void *part_new(size_t n) { void *p=calloc(1,n); assert(p); return p; }
static uint8_t memory[65536];
static unsigned cycles;
static char trace[2048];
static unsigned trace_length;
static void memory_cycle(void *context, _Bool read, uint16_t address) {
    struct MC6809 *cpu=context;
    assert(cycles++ < 32);
    if (read) cpu->D=memory[address]; else memory[address]=cpu->D;
    int n=snprintf(trace+trace_length,sizeof(trace)-trace_length,"%s%c%04x:%02x",trace_length?",":"",read?'r':'w',address,cpu->D);
    assert(n>0 && (unsigned)n < sizeof(trace)-trace_length);
    trace_length+=(unsigned)n;
}
static void done(void *context) { ((struct MC6809 *)context)->running=0; }
int main(void) {
 const unsigned opcodes[]={0x42,0x52,0x4b,0x5b,0x4e,0x5e};
 for(unsigned oi=0;oi<6;oi++)
 for(unsigned a=0;a<256;a++) for(unsigned cc=0;cc<256;cc++) {
  unsigned op=opcodes[oi];
  memset(memory,0,sizeof(memory));
  struct MC6809 cpu={0};
  cpu.state=mc6809_state_next_instruction; cpu.running=1;
  cpu.reg_pc=0x4000;cpu.reg_x=0x1234;cpu.reg_y=0x5678;cpu.reg_u=0x9abc;cpu.reg_s=0xdef0;cpu.reg_dp=0x42;
  MC6809_REG_A((&cpu))=op<0x50?a:0x5a;MC6809_REG_B((&cpu))=op>=0x50?a:0xa5;cpu.reg_cc=cc;
  cpu.mem_cycle=DELEGATE_AS2(void,bool,uint16,memory_cycle,&cpu);
  cpu.debug_cpu.instruction_posthook=DELEGATE_AS0(void,done,&cpu);
  memory[0x4000]=op;memory[0x4001]=0x12;
  cycles=trace_length=0;trace[0]=0;
  mc6809_run(&cpu);
  char expected[32];
  snprintf(expected,sizeof(expected),"r4000:%02x,r4001:12",op);
  assert(cycles==2 && strcmp(trace,expected)==0);
  assert(cpu.reg_pc==0x4001);
  assert(op<0x50?MC6809_REG_B((&cpu))==0xa5:MC6809_REG_A((&cpu))==0x5a);
  assert(cpu.reg_x==0x1234 && cpu.reg_y==0x5678 && cpu.reg_u==0x9abc && cpu.reg_s==0xdef0 && cpu.reg_dp==0x42);
  assert(fputc(op<0x50?MC6809_REG_A((&cpu)):MC6809_REG_B((&cpu)),stdout)!=EOF);
  assert(fputc(cpu.reg_cc,stdout)!=EOF);
 }
 assert(fflush(stdout)==0);
}
