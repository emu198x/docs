//! Temporary private-asset probe; source retained with the board evidence.
use emu198x_shell::{HostIo,MachineCore,NullAudioSink,NullFrameSink,NullTraceSink,MachineTime};
use runtime_atari_5200::{Atari5200Runtime,Model};
fn run(m:&mut Atari5200Runtime,target:u64) {
 m.run_until(MachineTime::new(target),&mut HostIo { input_events:&[],frame_sink:&mut NullFrameSink,audio_sink:&mut NullAudioSink,trace_sink:&mut NullTraceSink }).expect("native frame run");
}
#[test]
fn real_firmware_boot_and_restore_on_each_owner() {
 let cart=std::fs::read(std::env::var("EMU198X_ATARI_5200_CART").expect("explicit verified cart")).expect("cart");
 let bios=std::fs::read(std::env::var("EMU198X_ATARI_5200_BIOS").expect("explicit verified BIOS")).expect("BIOS");
 for model in Model::ALL {
  let mut m=Atari5200Runtime::new(model,cart.clone(),bios.clone()).expect("fixed board");
  run(&mut m,320*262*228);
  let hardware=m.machine().expect("live board");
  assert_eq!(hardware.board_id(),model.model_id());
  let colours:std::collections::HashSet<_>=hardware.framebuffer().iter().copied().collect();
  let non_bg=hardware.framebuffer().iter().filter(|&&pixel|pixel&0x00ffffff!=0).count();
  assert!(colours.len()>=4 && non_bg>=1000,"{model:?}: BIOS/game did not render");
  let before=m.snapshot().expect("live save");let mut restored=Atari5200Runtime::blank(model);restored.restore(&before).expect("live restore");
  run(&mut m,321*262*228);run(&mut restored,321*262*228);
  assert!(m.snapshot().expect("original")==restored.snapshot().expect("restored"),"{model:?}: full real-firmware continuation differs");
  println!("{}: {} colours, {} non-background pixels; complete next-frame restore matches",model.model_id(),colours.len(),non_bg);
 }
}
