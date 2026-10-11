#include <assert.h>
#include <stdio.h>
#include "sn76489.c"
void *part_new(size_t n) { void *p=calloc(1,n); assert(p); return p; }
void *xmalloc(size_t n) { void *p=malloc(n); assert(p); return p; }

static unsigned next_noise(struct SN76489_private *s,unsigned *tick) {
 unsigned old=s->noise_lfsr,start=*tick;
 while(*tick-start<65536) {
  *tick+=16;sn76489_get_audio(s,*tick,0,NULL);
  if(s->noise_lfsr!=old) return *tick-start;
 }
 assert(0 && "missing noise shift");return 0;
}
int main(void) {
 puts("white,initial,phase,target,event,interval,lfsr,tone3");
 unsigned count=0;const unsigned targets[]={0,1,7};
 for(unsigned white=0;white<2;white++) for(unsigned initial=5;initial<=15;initial+=10) for(unsigned phase=0;phase<2*initial;phase++) for(unsigned ti=0;ti<3;ti++) {
  struct SN76489_private *s=(struct SN76489_private *)sn76489_allocate();
  sn76489_configure(&s->public,4000000,48000,4000000,0);assert(sn76489_finish(&s->public.part));
  sn76489_write(&s->public,0,0xC0|initial);sn76489_get_audio(s,64,0,NULL);
  sn76489_write(&s->public,64,0);sn76489_get_audio(s,128,0,NULL);
  sn76489_write(&s->public,128,0xE3|(white<<2));
  unsigned tick=128;next_noise(s,&tick);
  tick+=16*phase;sn76489_get_audio(s,tick,0,NULL);
  assert(is_ready(&s->public,tick));
  sn76489_write(&s->public,tick,0xC0|targets[ti]);
  assert(s->reg_val[4]==targets[ti]);
  for(unsigned event=0;event<8;event++) {
   unsigned interval=next_noise(s,&tick);assert(s->state[2]);
   printf("%u,%u,%u,%u,%u,%u,%u,%u\n",white,initial,phase,targets[ti],event,interval,s->noise_lfsr,s->state[2]);count++;
  }
  sn76489_free(&s->public.part);free(s);
 }
 assert(count==1920);assert(fflush(stdout)==0);
}
