use atari_pokey::Pokey;

fn clock(chip: &mut Pokey, time: &mut u32, mask: u8) -> bool {
    chip.tick();
    *time += 1;
    if !chip.irq_pending() {
        return false;
    }
    assert_eq!(chip.read(0x0e) & mask, 0);
    chip.write(0x0e, 0);
    chip.write(0x0e, mask);
    true
}

#[test]
fn stimer_preserves_pending_linked_high_irqs() {
    let mut cases = 0;
    let mut failures = 0;
    let mut controls = 0;
    for frequency in [1_789_772, 1_773_447] {
        for pair in 0..2 {
            for low in [0_u8, 1, 15, 255] {
                for high in [0_u8, 1] {
                    for lead in [1, 2, 3] {
                        for action in 0_u32..4 {
                            let mut chip = Pokey::new(frequency);
                            let mask = if pair == 0 { 2 } else { 4 };
                            chip.write(0x0f, 3);
                            chip.write(0x08, if pair == 0 { 0x50 } else { 0x28 });
                            chip.write(pair * 4, low);
                            chip.write(pair * 4 + 2, high);
                            chip.write(0x09, 0);
                            chip.write(0x0e, mask);
                            let period = u32::from(low) + 256 * u32::from(high) + 7;
                            let mut time = 0;
                            let mut warmup = Vec::new();
                            while time < 4 * period && warmup.len() < 2 {
                                if clock(&mut chip, &mut time, mask) {
                                    warmup.push(time);
                                }
                            }
                            assert_eq!(warmup.len(), 2, "missing linked warmup IRQs");
                            assert_eq!(warmup[1] - warmup[0], period);
                            let first = time + period;
                            let write = first - lead;
                            let end = first + 12 + 4 * period;
                            let expected: Vec<u32> = if action == 0 {
                                (first..=end).step_by(period as usize).collect()
                            } else {
                                let reload = write + action.saturating_sub(1) + 4;
                                (first..reload)
                                    .step_by(period as usize)
                                    .chain((reload + period..=end).step_by(period as usize))
                                    .collect()
                            };
                            let mut observed = Vec::new();
                            while time < end {
                                if clock(&mut chip, &mut time, mask) {
                                    observed.push(time);
                                }
                                if action != 0
                                    && (time == write
                                        || (action >= 2 && time == write + action - 1))
                                {
                                    chip.write(0x09, 0);
                                }
                            }
                            let matches = observed == expected;
                            println!(
                                "LINKED_RESET clock={frequency} pair={pair} low={low} high={high} lead={lead} action={action} expected={expected:?} observed={observed:?} matches={matches}"
                            );
                            if action == 0 {
                                assert!(matches, "no-reset linked control disagrees");
                                controls += 1;
                            }
                            failures += usize::from(!matches);
                            cases += 1;
                        }
                    }
                }
            }
        }
    }
    assert_eq!((cases, controls), (384, 96));
    println!("LINKED_RESET_SUMMARY cases={cases} controls={controls} failures={failures}");
    assert_eq!(failures, 0, "STIMER must preserve pending linked high IRQs");
}
