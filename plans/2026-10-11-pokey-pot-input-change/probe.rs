use atari_pokey::Pokey;

#[test]
fn changing_paddle_rate_preserves_partial_charge() {
    let mut cases = [0; 4];
    let mut failures = [0; 4];
    for frequency in [1_789_772, 1_773_447] {
        for selected in 0..8_u8 {
            for (old, new) in [(64_u8, 200_u8), (200, 64)] {
                for fraction in 0..4_usize {
                    let mut chip = Pokey::new(frequency);
                    chip.write(0x0f, 3);
                    chip.set_pot(selected, old);
                    chip.write(0x0b, 0);
                    let elapsed = u32::from(old) * fraction as u32 / 4;
                    for _ in 0..elapsed * 114 {
                        chip.tick();
                    }
                    if fraction != 0 {
                        chip.set_pot(selected, new);
                    }
                    for _ in 0..27000 {
                        chip.tick();
                    }
                    let expected = if fraction == 0 {
                        i32::from(old)
                    } else {
                        elapsed as i32 + i32::from(new) * (4 - fraction as i32) / 4
                    };
                    let actual = chip.read(selected);
                    cases[fraction] += 1;
                    // This invariant permits two counts of clock-phase and
                    // input quantisation uncertainty. It checks retained charge,
                    // not calibrated analogue response or exact write timing.
                    if (i32::from(actual) - expected).abs() > 2 {
                        failures[fraction] += 1;
                        eprintln!(
                            "frequency={frequency} pot={selected} old={old} new={new} fraction={fraction}/4 actual={actual} expected_near={expected}"
                        );
                    }
                }
            }
        }
    }
    eprintln!("cases={cases:?} failures={failures:?}");
    assert_eq!(cases, [32; 4], "complete input-change inventory");
    assert_eq!(
        failures, [0; 4],
        "input changes must preserve partial pot charge"
    );
}
