use atari_pokey::Pokey;

fn clock(chip: &mut Pokey, time: &mut u32) -> bool {
    chip.tick();
    *time += 1;
    if !chip.irq_pending() {
        return false;
    }
    assert_eq!(chip.read(0x0e) & 1, 0);
    chip.write(0x0e, 0);
    chip.write(0x0e, 1);
    true
}

#[test]
fn audf_write_retains_the_reload_already_in_flight() {
    let mut cases = 0;
    let mut failures = 0;
    for frequency in [1_789_772, 1_773_447] {
        for old in [0_u8, 1, 15, 255] {
            for new in [0_u8, 1, 15, 255] {
                for lead in [1, 2, 3] {
                    let mut chip = Pokey::new(frequency);
                    chip.write(0x0f, 3);
                    chip.write(0x08, 0x40);
                    chip.write(0, old);
                    chip.write(1, 0xaf);
                    chip.write(0x09, 0);
                    chip.write(0x0e, 1);
                    let old_period = u32::from(old) + 4;
                    let new_period = u32::from(new) + 4;
                    let mut time = 0;
                    let mut warmup = Vec::new();
                    while time < old_period * 4 && warmup.len() < 2 {
                        if clock(&mut chip, &mut time) {
                            warmup.push(time);
                        }
                    }
                    assert_eq!(warmup.len(), 2, "missing warmup IRQ");
                    assert_eq!(warmup[1] - warmup[0], old_period);
                    let first = time + old_period;
                    let write_at = first - lead;
                    while time < write_at {
                        assert!(!clock(&mut chip, &mut time), "unexpected early IRQ");
                    }
                    chip.write(0, new);
                    let second = first + if lead >= 2 { new_period } else { old_period };
                    let expected = [first, second, second + new_period];
                    let mut observed = Vec::new();
                    while time < first + 3 * old_period.max(new_period) && observed.len() < 3 {
                        if clock(&mut chip, &mut time) {
                            observed.push(time);
                        }
                    }
                    assert_eq!(observed.len(), 3, "missing post-write IRQ");
                    let matches = observed == expected;
                    println!(
                        "AUDF clock={frequency} old={old} new={new} lead={lead} expected={expected:?} observed={observed:?} matches={matches}"
                    );
                    failures += usize::from(!matches);
                    cases += 1;
                }
            }
        }
    }
    assert_eq!(cases, 96);
    println!("AUDF_SUMMARY cases={cases} failures={failures}");
    assert_eq!(failures, 0, "AUDF writes must retain the in-flight reload");
}
