use atari_pokey::Pokey;

#[test]
fn pot_scan_public_registers() {
    let mut failures = [0; 4];
    let mut counts = [0; 4];
    for clock in [1_789_772, 1_773_447] {
        for selected in 0..8_u8 {
            for case in 0..4 {
                let mut chip = Pokey::new(clock);
                for pot in 0..8 {
                    chip.set_pot(pot, 228);
                }
                let (mode, ticks) = match case {
                    0 => (7, 300),
                    1 => (3, 1000),
                    2 => (0, 1140),
                    _ => (3, 27000),
                };
                chip.write(0x0f, mode);
                chip.write(0x0b, 0);
                for _ in 0..ticks {
                    chip.tick();
                }
                let actual = (chip.read(selected), chip.read(8));
                // Fresh, discharged high-resistance input. Slow-mode phase is
                // deliberately not fixed: either adjacent stable count is valid.
                let valid = match case {
                    0 => actual == (229, 0),
                    1 => matches!(actual, (8 | 9, 255)),
                    2 => actual == (0, 255),
                    _ => actual == (228, 0),
                };
                counts[case] += 1;
                if !valid {
                    failures[case] += 1;
                    eprintln!("clock={clock} pot={selected} case={case} actual={actual:?}");
                }
            }
        }
    }
    eprintln!("counts={counts:?} failures={failures:?}");
    assert_eq!(counts, [16; 4], "complete public scan inventory");
    assert_eq!(
        failures, [0; 4],
        "pot scans must expose live counts and honour their clock source"
    );
}
