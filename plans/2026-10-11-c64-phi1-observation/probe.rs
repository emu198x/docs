    #[test]
    fn phi1_guest_reads_match_native_endpoints() {
        let inputs = std::path::PathBuf::from(std::env::var("C64_PHI1_INPUT").expect("native captures"));
        let roms = c64_rom_dir();
        let kernal = std::fs::read(roms.join("kernal.rom")).expect("KERNAL");
        let basic = std::fs::read(roms.join("basic.rom")).expect("BASIC");
        let characters = std::fs::read(roms.join("chargen.rom")).expect("character ROM");
        let mut total_wrong = 0;
        for (model, name, cycles) in [
            (C64Model::PalBreadbin, "pal", 63),
            (C64Model::PalC64c, "c64c", 63),
            (C64Model::NtscBreadbin, "ntsc", 65),
            (C64Model::NtscC64c, "c64cntsc", 65),
        ] {
            for endpoint in ["io1", "colour"] {
                let program = std::fs::read(inputs.join(format!("{name}-{endpoint}.prg"))).expect("guest");
                let native = std::fs::read(inputs.join(format!("{name}-{endpoint}.bin"))).expect("native dump");
                assert_eq!(native.len(), program.len() - 2);
                let measured_at = native.len() - 132;
                assert_eq!((0x0801 + measured_at) & 255, 0);
                let mut machine = C64::new(C64Config {
                    model, kernal_rom: &kernal, basic_rom: &basic, character_rom: &characters,
                }).expect("real ROM machine");
                for _ in 0..3_100_000 {
                    machine.tick();
                    if machine.frame_count() == 150 { break; }
                }
                assert_eq!(machine.frame_count(), 150, "boot frame limit");
                assert_eq!(machine.load_prg(&program).expect("guest loaded"), 0x0801);
                // Queue the same SYS entry used by the native monitor through
                // KERNAL's keyboard buffer. The CPU executes the BASIC command.
                for (i, value) in b"SYS2061\r".iter().enumerate() {
                    machine.cpu_write(0x0277 + i as u16, *value);
                }
                machine.cpu_write(0x00C6, 8);
                let mut done = None;
                for _ in 0..1_000_000 {
                    let cpu = machine.cpu();
                    let (addr, value, rw, total) = (cpu.addr, cpu.data, cpu.rw, cpu.total_cycles);
                    machine.tick();
                    if !rw && addr == 0xD7FF && machine.cpu().total_cycles != total {
                        done = Some(value);
                        break;
                    }
                }
                let status = done.expect("guest never wrote completion sentinel");
                let actual: Vec<_> = (0..cycles).map(|i| machine.memory.ram_read((0x0801 + measured_at + i) as u16)).collect();
                let expected = &native[measured_at..measured_at + cycles];
                let wrong = actual.iter().zip(expected).filter(|(a,b)| a != b).count();
                println!("ROW|{name}|{endpoint}|{status}|{wrong}|{actual:?}");
                total_wrong += wrong;
            }
        }
        assert_eq!(total_wrong, 0, "Phi1 guest differs from native VICE");
    }
