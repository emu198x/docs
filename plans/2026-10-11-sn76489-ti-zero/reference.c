#include <assert.h>
#include <stdio.h>
#include "sn76489.c"
void *part_new(size_t n) { void *p=calloc(1,n); assert(p); return p; }
void *xmalloc(size_t n) { void *p=malloc(n); assert(p); return p; }
static unsigned next_edge(struct SN76489_private *s, unsigned ch, unsigned *tick) {
 unsigned start=*tick, previous=s->state[ch];
 while (*tick-start<40000) {
  *tick+=16;
  sn76489_get_audio(s,*tick,0,NULL);
  if (s->state[ch]!=previous) return *tick-start;
 }
 assert(0 && "missing edge"); return 0;
}
int main(void) {
 puts("channel,initial,phase,to_zero_first,zero_interval1,zero_interval2,from_zero_first,restored_interval1,restored_interval2");
 unsigned count=0;
 for(unsigned ch=0;ch<3;ch++) for(unsigned initial=5;initial<=15;initial+=10) for(unsigned phase=0;phase<initial;phase++) {
  struct SN76489_private *s=(struct SN76489_private *)sn76489_allocate();
  sn76489_configure(&s->public,4000000,48000,4000000,0);
  assert(sn76489_finish(&s->public.part));
  sn76489_write(&s->public,0,0x80|(ch<<5)|initial);
  unsigned tick=0;
  (void)next_edge(s,ch,&tick);
  assert(next_edge(s,ch,&tick)==16*initial);
  tick+=16*phase; sn76489_get_audio(s,tick,0,NULL);
  assert(is_ready(&s->public,tick));
  sn76489_write(&s->public,tick,0x80|(ch<<5));
  assert(s->reg_val[ch*2]==0 && s->frequency[ch]==1024);
  unsigned a=next_edge(s,ch,&tick), b=next_edge(s,ch,&tick), c=next_edge(s,ch,&tick);
  tick+=16*phase; sn76489_get_audio(s,tick,0,NULL);
  assert(is_ready(&s->public,tick));
  sn76489_write(&s->public,tick,0x80|(ch<<5)|initial);
  assert(s->reg_val[ch*2]==initial);
  unsigned d=next_edge(s,ch,&tick), e=next_edge(s,ch,&tick), f=next_edge(s,ch,&tick);
  assert(a==16*(initial-phase) && b==16384 && c==16384);
  assert(d==16*(1024-phase) && e==16*initial && f==16*initial);
  printf("%u,%u,%u,%u,%u,%u,%u,%u,%u\n",ch,initial,phase,a,b,c,d,e,f);
  sn76489_free(&s->public.part); free(s); count++;
 }
 assert(count==60); assert(fflush(stdout)==0);
}
