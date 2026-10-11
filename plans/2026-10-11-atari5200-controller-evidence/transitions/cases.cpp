int main() {
  unsigned failures=0, cases=0;
  puts("case,origin,phase,mode,first_edge,first_key,first_shift,first_break,edges,kbcode,skstat,irqst,passed");
  auto record=[&](const char* name,uint64 origin,unsigned phase,unsigned mode,const ATPokeyEmulator& p,bool pass){
    failures+=!pass; ++cases;
    printf("%s,%llu,%u,%u,%llu,%llu,%llu,%llu,%u,%u,%u,%u,%u\n",name,
      (unsigned long long)origin,phase,mode,(unsigned long long)p.first_edge,
      (unsigned long long)p.first_key,(unsigned long long)p.first_shift,
      (unsigned long long)p.first_break,p.edges,p.mKBCODE,p.mSKSTAT,p.mIRQST,pass);
  };
  // Absolute origins include the 32-bit wrap used by reference clock helpers.
  for(uint64 origin: {0ull,1ull,57ull,113ull,255ull,4294967095ull}) {
    for(unsigned mode=0;mode<4;++mode) {
      ATPokeyEmulator p; p.scheduler.now=origin; p.inputs(1u<<15,true);
      p.WriteByte(15,mode); p.advance(origin+81+114*127);
      bool scan=mode&2, key=mode==2;
      bool pass=p.edges==(scan?128u:0u)
        && p.first_edge==(scan?origin+81:0)
        && p.first_key==(key?origin+81+31*114:0)
        && p.first_shift==(scan?origin+81+16*114:0)
        && p.first_break==(scan?origin+81+48*114:0);
      record("startup",origin,0,mode,p,pass);
    }
    // Enabling the scanner while initialization is already clear must use
    // the running /114 phase, not restart an 81-clock delay.
    for(unsigned delay=0;delay<228;++delay) {
      ATPokeyEmulator p; p.scheduler.now=origin; p.inputs(1u<<15,true);
      p.WriteByte(15,1); p.advance(origin+delay); p.WriteByte(15,2);
      uint64 first=origin+81;
      while(first<=origin+delay) first+=114;
      p.advance(first+114*127);
      bool pass=p.first_edge==first && p.edges==128
        && p.first_key==first+31*114 && p.first_shift==first+16*114
        && p.first_break==first+48*114;
      record("enable",origin,delay,2,p,pass);
    }
  }
  // Disable at every position within one /114 period. 1 preserves the
  // divider; 0 enters initialization and restarts it on re-enable.
  for(unsigned phase=0;phase<114;++phase)
  for(unsigned mode: {0u,1u}) {
    ATPokeyEmulator p; p.inputs(1u<<15,true); p.WriteByte(15,2);
    uint64 off=81+114*127+phase;
    p.advance(off);
    uint8 old_kb=p.mKBCODE, old_irq=p.mIRQST;
    p.WriteByte(15,mode); p.inputs(0,false);
    unsigned edges=p.edges;
    p.advance(off+1000);
    bool pass=p.edges==edges && p.mKeyScanCode==0 && p.mKeyScanState==0
      && p.mKBCODE==old_kb && p.mIRQST==old_irq
      && (p.mSKSTAT&12)==4; // key released, shift retained
    p.WriteByte(15,2);
    uint64 next=off+1000+81;
    if(mode==1) {next=81; while(next<=off+1000) next+=114;}
    pass &= p.scheduler.due==next;
    p.advance(next+16*114-1);
    pass &= !(p.mSKSTAT&8); // shift sample not reached yet
    p.advance(next+16*114);
    pass &= bool(p.mSKSTAT&8) && p.mKBCODE==old_kb && p.mIRQST==old_irq;
    record("disable",0,phase,mode,p,pass);
  }
  // Selection to a released controller and back. The input mux changes
  // immediately, but previously sampled modifiers change only at their slots.
  for(unsigned phase=0;phase<64;++phase)
  for(unsigned mode: {2u,3u}) {
    ATPokeyEmulator p; p.inputs(1u<<15,true); p.WriteByte(15,mode);
    p.advance(81+114*(127+phase));
    p.mIRQST|=192; // acknowledge before changing the external input
    uint8 before=p.mSKSTAT; p.inputs(0,false);
    bool pass=p.mSKSTAT==before;
    unsigned next_code=p.mKeyScanCode&63;
    unsigned shift_distance=(16+64-next_code)%64;
    uint64 release=p.scheduler.due+shift_distance*114;
    p.advance(release-1); pass &= !(p.mSKSTAT&8);
    p.advance(release); pass &= bool(p.mSKSTAT&8);
    p.advance(p.scheduler.now+64*114); // sample released Break too
    pass &= bool(p.mIRQST&128) && !p.mbBreakKeyLatchedState;
    p.inputs(1u<<15,true);
    next_code=p.mKeyScanCode&63;
    unsigned break_distance=(48+64-next_code)%64;
    uint64 repress=p.scheduler.due+break_distance*114;
    p.advance(repress-1); pass &= bool(p.mIRQST&128);
    p.advance(repress); pass &= !(p.mIRQST&128);
    record("select",0,phase,mode,p,pass);
  }
  fprintf(stderr,"%u mismatches across %u scheduled transition cases\n",failures,cases);
  return failures?1:0;
}
