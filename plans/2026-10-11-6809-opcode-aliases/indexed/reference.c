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
 unsigned v[13], cases=0;
 int n;
 while((n=scanf("%x %x %x %x %x %x %x %x %x %x %x %x %x", &v[0],&v[1],&v[2],&v[3],&v[4],&v[5],&v[6],&v[7],&v[8],&v[9],&v[10],&v[11],&v[12])) != EOF) {
  assert(n==13);
  for(unsigned a=0;a<65536;a++) memory[a]=(a*73)^(a>>8)^0xa5;
  struct MC6809 cpu={0};
  cpu.state=mc6809_state_next_instruction; cpu.running=1;
  cpu.reg_pc=v[12];cpu.reg_dp=v[7];cpu.reg_x=v[8];cpu.reg_y=v[9];cpu.reg_u=v[10];cpu.reg_s=v[11];cpu.reg_cc=v[6];
  MC6809_REG_A((&cpu))=v[4]; MC6809_REG_B((&cpu))=v[5];
  cpu.mem_cycle=DELEGATE_AS2(void,bool,uint16,memory_cycle,&cpu);
  cpu.debug_cpu.instruction_posthook=DELEGATE_AS0(void,done,&cpu);
  for(unsigned i=0;i<4;i++) memory[(uint16_t)(v[12]+i)]=v[i];
  cycles=trace_length=0;trace[0]=0;
  mc6809_run(&cpu);
  for(unsigned i=0;i<13;i++) printf("%04x ",v[i]);
  printf("| %u %02x %02x %02x %02x %04x %04x %04x %04x %04x | %s | 0\n",cycles,MC6809_REG_A((&cpu)),MC6809_REG_B((&cpu)),cpu.reg_cc,cpu.reg_dp,cpu.reg_x,cpu.reg_y,cpu.reg_u,cpu.reg_s,cpu.reg_pc,trace);
  cases++;
 }
 assert(cases==96800);
}
