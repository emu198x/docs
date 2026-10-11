#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "sn76489.c"
void *part_new(size_t n) { void *p=calloc(1,n); assert(p); return p; }
void *xmalloc(size_t n) { void *p=malloc(n); assert(p); return p; }
int main(int argc, char **argv) {
 assert(argc==1 || (argc==2 && strcmp(argv[1],"zero")==0));
 _Bool zero=argc==2;
 puts("channel,period,interval1,interval2");
 for(unsigned ch=0;ch<3;ch++) for(unsigned period=zero?0:1;period<(zero?1:1024);period++) {
  struct SN76489_private *s=(struct SN76489_private *)sn76489_allocate();
  sn76489_configure(&s->public,4000000,48000,4000000,0);
  assert(sn76489_finish(&s->public.part));
  sn76489_write(&s->public,0,0x80|(ch<<5)|(period&15));
  sn76489_get_audio(s,64,0,NULL);
  sn76489_write(&s->public,64,period>>4);
  assert(s->frequency[ch]==(period?period:1024));
  // Discard the first transition: power-on/startup phase is not the oracle.
  unsigned previous=s->state[ch], n=0, edges[3]={0};
  for(unsigned tick=80;tick<100000 && n<3;tick+=16) {
   sn76489_get_audio(s,tick,0,NULL);
   if(s->state[ch]!=previous) { previous=s->state[ch]; edges[n++]=tick; }
  }
  assert(n==3);
  unsigned interval=16*(period?period:1024);
  assert(edges[1]-edges[0]==interval && edges[2]-edges[1]==interval);
  printf("%u,%u,%u,%u\n",ch,period,edges[1]-edges[0],edges[2]-edges[1]);
  sn76489_free(&s->public.part); free(s);
 }
 assert(fflush(stdout)==0);
}
