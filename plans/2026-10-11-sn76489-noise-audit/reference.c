#include <assert.h>
#include <stdio.h>
#include "sn76489.c"
void *part_new(size_t n) { void *p=calloc(1,n); assert(p); return p; }
void *xmalloc(size_t n) { void *p=malloc(n); assert(p); return p; }
int main(void) {
 const unsigned periods[]={0,1,2,7,31,1023};
 puts("mode,white,period,event,tick,interval,lfsr,tone3,rising");
 unsigned count=0;
 for(unsigned mode=0;mode<4;mode++) for(unsigned white=0;white<2;white++) for(unsigned pi=0;pi<(mode==3?6:1);pi++) {
  unsigned period=mode==3?periods[pi]:7;
  struct SN76489_private *s=(struct SN76489_private *)sn76489_allocate();
  sn76489_configure(&s->public,4000000,48000,4000000,0);
  assert(sn76489_finish(&s->public.part));
  sn76489_write(&s->public,0,0xC0|(period&15));
  sn76489_get_audio(s,64,0,NULL);
  sn76489_write(&s->public,64,period>>4);
  sn76489_get_audio(s,128,0,NULL);
  sn76489_write(&s->public,128,0xE0|mode|(white<<2));
  assert(s->reg_val[4]==period && s->reg_val[6]==(mode|(white<<2)));
  unsigned old=s->noise_lfsr, last=0, events=0;
  for(unsigned tick=144;tick<4000000 && events<65;tick+=16) {
   unsigned prev_tone=s->state[2];
   sn76489_get_audio(s,tick,0,NULL);
   if(s->noise_lfsr!=old) {
    unsigned rising=!prev_tone && s->state[2];
    if(events) {
     unsigned interval=mode==3?32*(period?period:1024):(512<<mode);
     assert(tick-last==interval);
     assert(mode!=3 || rising);
     printf("%u,%u,%u,%u,%u,%u,%u,%u,%u\n",mode,white,period,events,tick,tick-last,s->noise_lfsr,s->state[2],rising);
     count++;
    }
    old=s->noise_lfsr;last=tick;events++;
   }
  }
  assert(events==65);
  sn76489_free(&s->public.part);free(s);
 }
 assert(count==1152);assert(fflush(stdout)==0);
}
