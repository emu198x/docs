use common_z80_machine::Z80Machine;
use machine_sega_sg_1000::{ControllerState,Sg1000,Sg1000Region};
fn pad(bits:u16)->ControllerState {ControllerState {up:bits&1!=0,down:bits&2!=0,left:bits&4!=0,right:bits&8!=0,button1:bits&16!=0,button2:bits&32!=0}}
fn main(){
 let rom=std::fs::read("/private/tmp/198x-sg1000-input-evidence/input.sg").expect("original guest");
 let mut m=Sg1000::new(rom,Sg1000Region::Ntsc);
 println!("state,even,odd,before,after");
 for state in 0..4096 {
  *m.controller1_mut()=pad(state);*m.controller2_mut()=pad(state>>6);
  let before=m.peek(0xc002);m.advance_tstates(4000);
  println!("{state},{},{},{before},{}",m.peek(0xc000),m.peek(0xc001),m.peek(0xc002));
 }
}
