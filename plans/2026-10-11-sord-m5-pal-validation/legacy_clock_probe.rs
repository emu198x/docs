use common_z80_machine::Z80Machine;
use machine_sord_m5::{M5Region, SordM5};
#[test]
fn legacy_clock_probe() {
    let path = std::env::var("LEGACY_CLOCK_SNAPSHOT").expect("snapshot path");
    if std::env::var_os("GENERATE_LEGACY_CLOCK").is_some() {
        let mut rom = vec![0; 8192];
        rom[..2].copy_from_slice(&[0xf3, 0x76]);
        let machine = SordM5::new(rom, vec![], M5Region::Pal);
        std::fs::write(path, postcard::to_allocvec(&machine).expect("encode")).expect("write");
    } else {
        let bytes = std::fs::read(path).expect("read");
        let mut machine: SordM5 = postcard::from_bytes(&bytes).expect("decode");
        machine.cpu_mut().rehydrate_walker_sequence();
        machine.advance_tstates(3_579_545);
        let n = machine.take_audio_buffer().len();
        println!("LEGACY PAL restored under corrected constructor: {n} samples per runtime second");
        assert_eq!(n, 48_441, "legacy limitation reproduction");
    }
}
