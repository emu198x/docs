use ti_sn76489::{NoiseLfsr, Sn76489};
fn main() {
 let zero=std::env::args().nth(1).is_some_and(|s| s=="zero");
 println!("variant,channel,period,interval1,interval2");
 for (name,variant) in [("ti",NoiseLfsr::Tms15),("sega",NoiseLfsr::Sega16)] {
  for ch in 0..3u8 { for period in (if zero {0} else {1})..(if zero {1} else {1024u16}) {
   let mut psg=Sn76489::new(4_000_000,variant);
   psg.write(0x80|(ch<<5)|((period&15) as u8));
   for _ in 0..64 { psg.tick(); }
   psg.write((period>>4) as u8);
   let mut state=Vec::new(); psg.save_state(&mut state);
   let mut previous=state[12+usize::from(ch)]; let mut edges=Vec::new();
   for tick in 80..100000 {
    if tick % 16 != 0 {continue;}
    for _ in 0..16 {psg.tick();}
    state.clear(); psg.save_state(&mut state);
    let output=state[12+usize::from(ch)];
    if output!=previous {previous=output;edges.push(tick);if edges.len()==3 {break;}}
   }
   assert_eq!(edges.len(),3);
   println!("{name},{ch},{period},{},{}",edges[1]-edges[0],edges[2]-edges[1]);
  }}
 }
}
