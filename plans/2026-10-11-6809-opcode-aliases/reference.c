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
 const unsigned opcodes[]={0x12,0x1b,0x00,0x01,0x40,0x41,0x50,0x51,0x60,0x61,0x70,0x71,0x04,0x05,0x44,0x45,0x54,0x55,0x64,0x65,0x74,0x75};
 const unsigned values[]={0,1,0x7f,0x80,0xfe,0xff};
 const unsigned flags[]={0,1,0xfe,0xff};
 const unsigned pcs[]={0x4000,0xffff};
 puts("opcode value cc pc cycles a b result_cc result_pc memory trace");
 for(unsigned oi=0;oi<22;oi++) for(unsigned vi=0;vi<6;vi++)
 for(unsigned ci=0;ci<4;ci++) for(unsigned pi=0;pi<2;pi++) {
  unsigned op=opcodes[oi],v=values[vi],cc=flags[ci],pc=pcs[pi];
  memset(memory,0,sizeof(memory));
  struct MC6809 cpu={0};
  cpu.state=mc6809_state_next_instruction; cpu.running=1;
  cpu.reg_pc=pc; cpu.reg_dp=0x50; cpu.reg_x=0x50a5;
  MC6809_REG_A((&cpu))=v; MC6809_REG_B((&cpu))=v;
  cpu.reg_cc=cc;
  cpu.mem_cycle=DELEGATE_AS2(void,bool,uint16,memory_cycle,&cpu);
  cpu.debug_cpu.instruction_posthook=DELEGATE_AS0(void,done,&cpu);
  memory[pc]=op;
  memory[(uint16_t)(pc+1)]=op<0x10?0xa5:((op&0xf0)==0x60?0x84:((op&0xf0)==0x70?0x50:0x12));
  memory[(uint16_t)(pc+2)]=0xa5;
  memory[0x50a5]=v;
  cycles=trace_length=0; trace[0]=0;
  mc6809_run(&cpu);
  printf("%02x %02x %02x %04x %u %02x %02x %02x %04x %02x %s\n",op,v,cc,pc,cycles,MC6809_REG_A((&cpu)),MC6809_REG_B((&cpu)),cpu.reg_cc,cpu.reg_pc,memory[0x50a5],trace);
 }
}
