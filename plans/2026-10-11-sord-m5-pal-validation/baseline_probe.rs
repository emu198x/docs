//! Finite PAL boot and output-cadence investigation for issue #252.
use common_z80_machine::Z80Machine;
use machine_sord_m5::{M5Region, SordM5};
use std::{fs, path::PathBuf};

#[test]
#[ignore = "FIXTURE: needs European M5 BIOS and BASIC-I/Dig Dug carts"]
fn european_bios_pal_boot_probe() {
    let root = PathBuf::from(std::env::var("HOME").expect("HOME"));
    let bios = fs::read(root.join(".emu198x/roms/sord-m5/sord-m5.rom")).expect("European BIOS");
    assert_eq!(bios.len(),8192);
    let out = PathBuf::from(std::env::var("SORD_PAL_EVIDENCE").expect("evidence directory"));
    for name in ["basic-i", "dig-dug"] {
        let cart=fs::read(root.join(format!(".emu198x/media/sord-m5/{name}.bin"))).expect("cart");
        let mut m=SordM5::new(bios.clone(),cart,M5Region::Pal);
        for _ in 0..600 { assert_eq!(m.run_frame(),71364); m.take_audio_buffer(); }
        let before=m.irq_acks_by_channel();
        let clock=m.cpu_tstates();
        for _ in 0..100 { assert_eq!(m.run_frame(),71364); m.take_audio_buffer(); }
        let acks=m.irq_acks_by_channel();
        println!("PAL cart={name} frames={} ticks={} ch3_delta={} scanline={} regs={:?} pc={:04x}",m.frame_count(),m.cpu_tstates()-clock,acks[3]-before[3],m.vdp().scanline(),m.vdp().registers(),m.cpu().regs.pc);
        assert_eq!(acks[3]-before[3],100,"one serviced VDP interrupt per PAL frame");
        let base=usize::from(m.vdp().registers()[2]&0x0f)*1024;
        let table=&m.vdp().vram()[base..base+960];
        let names:String=table.iter().map(|b|if (32..127).contains(b) {char::from(*b)} else {'.'}).collect();
        println!("NAMES {name}: {names}");
        fs::write(out.join(format!("{name}.vram")),m.vdp().vram()).expect("VRAM");
        let mut ppm=format!("P6\n{} {}\n255\n",m.framebuffer_width(),m.framebuffer_height()).into_bytes();
        for pixel in m.framebuffer() {ppm.extend([(*pixel>>16)as u8,(*pixel>>8)as u8,*pixel as u8]);}
        fs::write(out.join(format!("{name}.ppm")),ppm).expect("framebuffer");
    }
}

#[test]
fn each_runtime_second_produces_48000_audio_samples() {
    let mut mismatches=Vec::new();
    for region in [M5Region::Ntsc,M5Region::Pal] {
        let mut rom=vec![0;8192];rom[..2].copy_from_slice(&[0xf3,0x76]);
        let mut m=SordM5::new(rom,vec![],region);
        m.advance_tstates(3_579_545); // One second according to both runtime profiles.
        let n=m.take_audio_buffer().len();
        println!("AUDIO region={region:?} tstates={} samples={n}",m.cpu_tstates());
        if n!=48_000 {mismatches.push((region,n));}
    }
    assert!(mismatches.is_empty(),"runtime/chip clock mismatch: {mismatches:?}");
}
