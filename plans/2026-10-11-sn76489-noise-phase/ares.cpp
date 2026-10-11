#include <cassert>
#include <cstdio>
#include "sn76489.cpp"
struct Observed : ares::SN76489 {
 unsigned shift() const { return noise.lfsr; }
 unsigned tone() const { return tone2.output; }
 unsigned level() const { return noise.flip; }
 unsigned output() const { return noise.output; }
};
int main() {
 const unsigned periods[]={0,1,2,7,31,1023};
 puts("mode,white,period,event,tick,interval,lfsr,tone3,rising,clock_level,noise_output");
 unsigned count=0;
 for(unsigned mode=0;mode<4;mode++) for(unsigned white=0;white<2;white++) for(unsigned pi=0;pi<(mode==3?6:1);pi++) {
  unsigned period=mode==3?periods[pi]:7;
  Observed s;s.power();s.write(0xC0|(period&15));
  for(unsigned i=0;i<4;i++) s.clock();s.write(period>>4);
  for(unsigned i=0;i<4;i++) s.clock();s.write(0xE0|mode|(white<<2));
  unsigned old=s.shift(),last=0,events=0;
  for(unsigned tick=144;tick<4000000 && events<65;tick+=16) {
   unsigned previous=s.tone();s.clock();
   if(s.shift()!=old) {
    if(events) {
     unsigned interval=mode==3?32*(period?period:1):(512<<mode);
     assert(tick-last==interval);
     printf("%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",mode,white,period,events,tick,tick-last,s.shift(),s.tone(),!previous && s.tone(),s.level(),s.output());count++;
    }
    old=s.shift();last=tick;events++;
   }
  }
  assert(events==65);
 }
 assert(count==1152);assert(fflush(stdout)==0);
}
