use motorola_6845::{Crtc6845,Crtc6845Variant};
fn main() {
 let mut failures=0;
 println!("variant,signal,width,expected_clocks,complete_pulses,observed_clocks,passed");
 for variant in [Crtc6845Variant::Mc6845,Crtc6845Variant::Hd6845s] {
  for signal in ["h","v"] { for width in 0..16u8 {
   let mut c=Crtc6845::new();c.set_variant(variant);
   for (r,v) in [(0,63),(1,20),(2,30),(3,if signal=="h" {0x40|width} else {(width<<4)|4}),(4,60),(5,3),(6,20),(7,25),(8,0),(9,0)] {
    c.write_address(r);c.write_data(v);
   }
   let expected=if signal=="h" {usize::from(width)} else {64*if variant==Crtc6845Variant::Mc6845 || width==0 {16} else {usize::from(width)}};
   let mut runs=Vec::new();let mut length=0;
   for _ in 0..128*64 {
    c.tick(); let high=if signal=="h" {c.hsync} else {c.vsync};
    if high {length+=1;} else if length!=0 {runs.push(length);length=0;}
   }
   let passed=if expected==0 {runs.is_empty()&&length==0} else {runs.len()>=2 && runs.iter().all(|&n|n==expected)};
   failures+=usize::from(!passed);
   println!("{variant:?},{signal},{width},{expected},{},{},{passed}",runs.len(),runs.iter().map(usize::to_string).collect::<Vec<_>>().join(":"));
  }}
 }
 eprintln!("{failures} mismatches across 64 pin-level sync cases");
 assert_eq!(failures,0,"CRTC sync outputs must remain high for the programmed interval");
}
