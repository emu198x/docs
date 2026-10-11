use machine_sega_master_system::{Sms,SmsVariant};
use std::{env,fs,io::Write};
fn main() {
 let args:Vec<String>=env::args().collect();
 assert_eq!(args.len(),5);
 let region=if args[2]=="pal" {SmsVariant::SmsPal} else {SmsVariant::SmsNtsc};
 let mut m=Sms::new(fs::read(&args[1]).expect("ROM"),region);
 let frames:u32=args[4].parse().expect("frames");
 for _ in 0..frames {m.run_frame();m.take_audio_buffer();}
 let w=m.framebuffer_width();let h=m.framebuffer_height();
 let mut f=fs::File::create(format!("{}.ppm",args[3])).expect("PPM");
 write!(f,"P6\n{w} {h}\n255\n").expect("header");
 for &p in m.framebuffer(){f.write_all(&[(p>>16)as u8,(p>>8)as u8,p as u8]).expect("pixel");}
 let ram:Vec<u8>=(0xc000u16..0xe000).map(|a|m.peek(a)).collect();
 fs::write(format!("{}.ram",args[3]),ram).expect("RAM");
 println!("region={region:?} frames={frames} ticks={} pc={:04x} pixels={w}x{h}",m.cpu_tstates(),m.cpu().regs.pc);
}
