use atari_pokey::Pokey;

#[test]
fn restarted_scan_retains_input_charge() {
    let mut cases = [0; 3];
    let mut failures = [0; 3];
    for frequency in [1_789_772, 1_773_447] {
        for selected in 0..8_u8 {
            for target in [64_u8, 100, 128, 200] {
                for (group, restart_lines) in [0_u32, 16, 32].into_iter().enumerate() {
                    let mut chip = Pokey::new(frequency);
                    chip.write(0x0f, 3);
                    for pot in 0..8 {
                        chip.set_pot(pot, target);
                    }
                    chip.write(0x0b, 0);
                    for _ in 0..restart_lines * 114 {
                        chip.tick();
                    }
                    if restart_lines != 0 {
                        chip.write(0x0b, 0);
                    }
                    for _ in 0..27000 {
                        chip.tick();
                    }
                    let actual = chip.read(selected);
                    let expected = i32::from(target) - restart_lines as i32;
                    // The source-backed charge-retention invariant does not
                    // depend on pinning the unqualified SKCTL write phase.
                    // Two counts cover phase and input-rate quantisation.
                    let valid = (i32::from(actual) - expected).abs() <= 2 && chip.read(8) == 0;
                    cases[group] += 1;
                    if !valid {
                        failures[group] += 1;
                        eprintln!(
                            "frequency={frequency} pot={selected} target={target} restart={restart_lines} actual={actual} expected_near={expected}"
                        );
                    }
                }
            }
        }
    }
    eprintln!("cases={cases:?} failures={failures:?}");
    assert_eq!(cases, [64; 3], "complete restart/control inventory");
    assert_eq!(
        failures, [0; 3],
        "POTGO must retain the input's accumulated charge"
    );
}
