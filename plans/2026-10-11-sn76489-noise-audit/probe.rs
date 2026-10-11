use ti_sn76489::{NoiseLfsr,Sn76489};
fn main() {
 println!("variant,mode,white,period,event,tick,interval,lfsr,tone3,rising");
 let mut count=0;
 for (name,variant) in [("ti",NoiseLfsr::Tms15),("sega",NoiseLfsr::Sega16)] {
  for mode in 0..4u8 {for white in 0..2u8 {
   let periods:&[u16]=if mode==3 {&[0,1,2,7,31,1023]} else {&[7]};
   for &period in periods {
    let mut psg=Sn76489::new(4_000_000,variant);
    psg.write(0xC0|(period&15) as u8);
    for _ in 0..64 {psg.tick();} psg.write((period>>4) as u8);
    for _ in 0..64 {psg.tick();} psg.write(0xE0|mode|(white<<2));
    let mut state=Vec::new();psg.save_state(&mut state);
    assert_eq!(u16::from_le_bytes([state[4],state[5]]),period);
    let mut old=u16::from_le_bytes([state[23],state[24]]);
    let mut last=0;let mut events=0;
    for tick in (144..4_000_000).step_by(16) {
     let prev_tone=state[14];
     for _ in 0..16 {psg.tick();}
     state.clear();psg.save_state(&mut state);
     let lfsr=u16::from_le_bytes([state[23],state[24]]);
     if lfsr!=old {
      let rising=u8::from(prev_tone==0 && state[14]!=0);
      if events>0 {
       println!("{name},{mode},{white},{period},{events},{tick},{},{lfsr},{},{rising}",tick-last,state[14]);
       count+=1;
      }
      old=lfsr;last=tick;events+=1;
      if events==65 {break;}
     }
    }
    assert_eq!(events,65);
   }
  }}
 }
 assert_eq!(count,2304);
}
