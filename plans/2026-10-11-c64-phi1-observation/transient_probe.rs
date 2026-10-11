#[test]
fn custom_glue_bank_swap_fetches_transient_bank_character() {
    let inputs = std::path::PathBuf::from(
        std::env::var("C64_BANK_TRANSIENT_INPUT").expect("native captures"),
    );
    let roms = c64_rom_dir();
    let kernal = std::fs::read(roms.join("kernal.rom")).expect("KERNAL");
    let basic = std::fs::read(roms.join("basic.rom")).expect("BASIC");
    let characters = std::fs::read(roms.join("chargen.rom")).expect("character ROM");
    let mut failed = 0;
    for (model, name, custom) in [
        (C64Model::PalBreadbin, "pal", false),
        (C64Model::PalC64c, "c64c", true),
        (C64Model::NtscBreadbin, "ntsc", false),
        (C64Model::NtscC64c, "c64cntsc", true),
    ] {
        let mut frames = Vec::new();
        for marker in [0, 255] {
            let program =
                std::fs::read(inputs.join(format!("{name}-1-2-marker{marker:02x}-glue1.prg")))
                    .expect("guest");
            let mut machine = C64::new(C64Config {
                model,
                kernal_rom: &kernal,
                basic_rom: &basic,
                character_rom: &characters,
            })
            .expect("real ROM machine");
            for _ in 0..3_100_000 {
                machine.tick();
                if machine.frame_count() == 150 {
                    break;
                }
            }
            assert_eq!(machine.frame_count(), 150, "boot frame limit");
            assert_eq!(machine.load_prg(&program).expect("guest loaded"), 0x0800);
            for (i, value) in b"SYS2048\r".iter().enumerate() {
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
            assert_eq!(done, Some(0xA5), "CPU guest completion");
            assert_eq!(machine.memory.ram_read(0x6000), 0xA5);
            assert!(machine.frame_count() > 152, "guest must span full frames");
            let pixels = machine.framebuffer().to_vec();
            assert!(pixels.len() > 60_000);
            assert!(pixels.iter().any(|p| *p != pixels[0]), "blank capture");
            frames.push(pixels);
        }
        assert_eq!(frames[0].len(), frames[1].len());
        let changed = frames[0]
            .iter()
            .zip(&frames[1])
            .filter(|(a, b)| a != b)
            .count();
        println!(
            "BANK_TRANSIENT|{name}|{}|{changed}|{}",
            frames[0].len(),
            u8::from(custom)
        );
        failed += usize::from((changed != 0) != custom);
    }
    assert_eq!(
        failed, 0,
        "custom-glue bank swap must expose transient bank-3 character data"
    );
}
