use motorola_6845::{Crtc6845,Crtc6845Variant};
fn write(c:&mut Crtc6845,r:u8,v:u8) {c.write_address(r);c.write_data(v);}
fn configured(v:Crtc6845Variant,r6:u8)->Crtc6845 {
 let mut c=Crtc6845::new();c.set_variant(v);
 for (r,value) in [(0,15),(1,8),(4,127),(6,r6),(9,0)] {write(&mut c,r,value);} c
}
fn main() {
 let mut failures=0;let mut cases=0;
 println!("variant,kind,register,value,expected,observed,passed");
 for variant in [Crtc6845Variant::Mc6845,Crtc6845Variant::Hd6845s] {
  for reg in [12,14,15,16,17] {
   if reg==12 && variant==Crtc6845Variant::Mc6845 {continue;}
   for value in 0..=255u8 {
    let mut c=Crtc6845::new();c.set_variant(variant);c.write_address(reg);
    let initial=c.read_data();c.write_data(value);let observed=c.read_data();
    let expected=match reg {12|14=>value&0x3f,15=>value,_=>initial};
    cases+=1;failures+=usize::from(observed!=expected);
    println!("{variant:?},readback,{reg},{value},{expected},{observed},{}",observed==expected);
   }
  }
  for low in 0..128u8 {
   let mut a=configured(variant,low);let mut b=configured(variant,low|0x80);
   let mut expected=0;let mut observed=0;let mut differences=0;
   for _ in 0..16*128*2 {a.tick();b.tick();expected+=usize::from(a.display_enable);observed+=usize::from(b.display_enable);differences+=usize::from(a.display_enable!=b.display_enable);}
   cases+=1;failures+=usize::from(differences!=0);
   println!("{variant:?},display_alias,6,{},{expected},{observed},{}",low|0x80,differences==0);
  }
 }
 eprintln!("{failures} mismatches across {cases} register cases");
 assert_eq!(failures,0,"6845 ports must respect implemented bits and read-only registers");
}
