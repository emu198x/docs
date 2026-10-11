use emu198x_zilog_z80::Z80Stepper;
use machine_sega_master_system::{Sms, SmsVariant};
use std::{env, fs};
fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 3);
    let variant = if args[2] == "pal" { SmsVariant::SmsPal } else { SmsVariant::SmsNtsc };
    let mut machine = Sms::new(fs::read(&args[1]).expect("read guest"), variant);
    for _ in 0..59 { machine.run_frame(); machine.take_audio_buffer(); }
    let ticks = if args[2] == "pal" { 313 * 228 } else { 262 * 228 };
    println!("event,tstate,scanline,dot,vc,hc,pc,port,value");
    for _ in 0..ticks {
        let old_irq = machine.vdp().interrupt;
        let old_vc = machine.vdp().read_v_counter();
        machine.start_io_trace();
        machine.step_tick();
        let io = machine.take_io_trace();
        let vdp = machine.vdp();
        if (!old_irq && vdp.interrupt) || (old_vc != vdp.read_v_counter() && (28..=34).contains(&vdp.scanline())) {
            println!("{},{},{},{},{},{},{:04x},,", if !old_irq && vdp.interrupt {"irq"} else {"vc"}, machine.cpu_tstates(), vdp.scanline(), vdp.dot(), vdp.read_v_counter(), vdp.read_h_counter(), machine.cpu().regs.pc);
        }
        for event in io {
            if !event.write || event.port & 255 != 0xbf { continue; }
            println!("{},{},{},{},{},{},{:04x},{:02x},{:02x}", if event.write {"out"} else {"in"}, machine.cpu_tstates(), vdp.scanline(), vdp.dot(), vdp.read_v_counter(), vdp.read_h_counter(), event.pc, event.port, event.value);
        }
    }
}
