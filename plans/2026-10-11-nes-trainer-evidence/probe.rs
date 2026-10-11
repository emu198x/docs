use format_nintendo_nes_ines::parse_ines;
fn main() {
    let mut controls = 0;
    let mut faults = 0;
    for mapper in [0u8, 1, 3, 4, 5, 34, 68] {
        for nes2 in [false, true] {
            for battery in [false, true] {
                for trainer in [false, true] {
                    let mut rom = vec![0; 16];
                    rom[..4].copy_from_slice(b"NES\x1a");
                    rom[4] = 2;
                    rom[5] = 1;
                    rom[6] = (mapper << 4) | u8::from(battery) * 2 | u8::from(trainer) * 4;
                    rom[7] = (mapper & 0xf0) | if nes2 { 8 } else { 0 };
                    // NES 2.0: specify 8 KiB work RAM or battery RAM explicitly.
                    rom[10] = if nes2 {
                        if battery { 0x70 } else { 7 }
                    } else {
                        0
                    };
                    if trainer {
                        rom.extend((0..512).map(|i| (i as u8).wrapping_mul(37).wrapping_add(11)));
                    }
                    rom.extend(vec![0; 32768 + 8192]);
                    let cart = parse_ines(&rom).expect("valid synthetic cartridge");
                    let ram = cart.mapper.save_ram();
                    assert!(ram.len() >= 0x1200);
                    let mismatches = (0..512)
                        .filter(|i| {
                            ram[0x1000 + i]
                                != if trainer {
                                    (*i as u8).wrapping_mul(37).wrapping_add(11)
                                } else {
                                    0
                                }
                        })
                        .count();
                    if trainer {
                        faults += usize::from(mismatches > 0);
                    } else {
                        assert_eq!(mismatches, 0);
                        controls += 1;
                    }
                    println!("{mapper},{nes2},{battery},{trainer},{mismatches}");
                }
            }
        }
    }
    eprintln!("controls={controls}, trainer_faults={faults}");
    assert_eq!((controls, faults), (28, 28));
}
