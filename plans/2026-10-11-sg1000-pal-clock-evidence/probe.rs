use common_z80_machine::Z80Machine;
use machine_sega_sg_1000::{Sg1000, Sg1000Region};
use runtime_sega_sg_1000::{Model, profile_for};
fn main() {
    // Original cartridge: program channel 0, then count executed loops in RAM.
    let guest = [0xf3, 0x3e, 0x80, 0xd3, 0x7f, 0x3e, 0x10, 0xd3, 0x7f,
        0x3e, 0x90, 0xd3, 0x7f, 0x3a, 0x00, 0xc0, 0x3c, 0x32, 0x00, 0xc0,
        0xc3, 0x0d, 0x00];
    println!("region,second,runtime_hz,cpu_ticks,samples,expected_samples,guest_marker,nonzero_samples");
    let mut failures = 0;
    for (model, region) in [(Model::Sg1000Ntsc, Sg1000Region::Ntsc), (Model::Sg1000Pal, Sg1000Region::Pal)] {
        let clock = profile_for(model).clock.rate;
        assert_eq!(clock.denominator_hz, 1);
        let mut rom = vec![0; 32768];
        rom[..guest.len()].copy_from_slice(&guest);
        let mut machine = Sg1000::new(rom, region);
        for second in 1..=3 {
            machine.advance_tstates(clock.numerator_hz);
            let audio = machine.take_audio_buffer();
            let nonzero = audio.iter().filter(|v| v.abs() > 1e-6).count();
            assert!(nonzero > 1000, "tone guest must execute");
            let expected = 48_000;
            if audio.len().abs_diff(expected) > 1 { failures += 1; }
            println!("{region:?},{second},{},{},{},{expected},{},{nonzero}", clock.numerator_hz, machine.cpu_tstates(), audio.len(), machine.peek(0xc000));
        }
    }
    eprintln!("sample_rate_mismatches={failures}/6");
    assert_eq!(failures, 0, "audio duration must match runtime time");
}
