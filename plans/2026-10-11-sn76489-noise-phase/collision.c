#include <assert.h>
#include <stdio.h>
#include "sn76489.c"
void *part_new(size_t n) { void *p=calloc(1,n); assert(p); return p; }
void *xmalloc(size_t n) { void *p=malloc(n); assert(p); return p; }

static struct SN76489_private *prepare(unsigned earlier_mode) {
 struct SN76489_private *s=(struct SN76489_private *)sn76489_allocate();
 sn76489_configure(&s->public,4000000,48000,4000000,0);assert(sn76489_finish(&s->public.part));
 sn76489_write(&s->public,0,0xE0|earlier_mode);
 sn76489_get_audio(s,512,0,NULL);
 sn76489_write(&s->public,512,0xE0);
 return s;
}
int main(void) {
 struct SN76489_private *a=prepare(0),*b=prepare(1);
 for(unsigned i=0;i<8;i++) assert(a->reg_val[i]==b->reg_val[i]);
 for(unsigned i=0;i<4;i++) {
  assert(a->frequency[i]==b->frequency[i]);
  assert(a->counter[i]==b->counter[i]);
  assert(a->state[i]==b->state[i]);
 }
 assert(a->noise_lfsr==b->noise_lfsr && a->noise_white==b->noise_white && a->noise_tone3==b->noise_tone3);
 assert(a->reg_sel==b->reg_sel && a->nstate!=b->nstate);
 puts("earlier_mode,tick,counter,clock_level,lfsr,output");
 unsigned first_output_difference=0;
 for(unsigned tick=512;tick<=8192;tick+=16) {
  sn76489_get_audio(a,tick,0,NULL);sn76489_get_audio(b,tick,0,NULL);
  unsigned new_output_difference=!first_output_difference && a->state[3]!=b->state[3];
  if(new_output_difference) first_output_difference=tick;
  if(tick==512 || tick==768 || tick==1024 || new_output_difference) {
   printf("0,%u,%u,%u,%u,%u\n",tick,a->counter[3],a->nstate,a->noise_lfsr,a->state[3]);
   printf("1,%u,%u,%u,%u,%u\n",tick,b->counter[3],b->nstate,b->noise_lfsr,b->state[3]);
  }
  if(tick==768) assert(a->noise_lfsr!=b->noise_lfsr);
 }
 assert(first_output_difference>512);
 sn76489_free(&a->public.part);sn76489_free(&b->public.part);free(a);free(b);assert(fflush(stdout)==0);
}
