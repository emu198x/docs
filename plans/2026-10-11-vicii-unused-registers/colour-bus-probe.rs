    #[test]
    fn colour_ram_bus_matches_native_idle_fetches() {
        let program = include_bytes!(env!("VICII_COLOUR_BUS_PRG"));
        assert_eq!(&program[..2], &[0, 8]);
        let mut total_wrong = 0;
        for model in [C64Model::PalBreadbin, C64Model::NtscBreadbin,
                      C64Model::PalC64c, C64Model::NtscC64c] {
            let mut machine = stub_machine_with_reset_vector(model, 0x0800);
            for (offset, byte) in program[2..].iter().enumerate() {
                machine.memory.ram_write(0x0800 + offset as u16, *byte);
            }
            for _ in 0..20_000 {
                machine.tick();
                if machine.memory.ram_read(0x6220) == 0xA5 { break; }
            }
            assert_eq!(machine.memory.ram_read(0x6220), 0xA5, "guest did not finish");
            let mut values = std::collections::BTreeMap::new();
            let mut wrong = 0;
            for offset in 0..544 {
                let actual = machine.memory.ram_read(0x6000 + offset);
                *values.entry(actual).or_insert(0) += 1;
                wrong += usize::from(actual != 0x9A);
            }
            println!("{model:?}: {wrong}/544 wrong, values {values:?}");
            total_wrong += wrong;
        }
        assert_eq!(total_wrong, 0, "colour RAM differs from native VICE");
    }
