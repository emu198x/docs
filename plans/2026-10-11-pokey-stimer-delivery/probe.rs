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
fn stimer_preserves_pending_irqs_until_the_reset_stages_arrive() {
    let mut cases = 0;
    let mut failures = 0;
    let mut controls = 0;
    for frequency in [1_789_772, 1_773_447] {
        for audf in [0_u8, 1, 15, 255] {
            for lead in [1, 2, 3] {
                for action in 0..4 {
                    let mut chip = Pokey::new(frequency);
                    chip.write(0x0f, 3);
                    chip.write(0x08, 0x40);
                    chip.write(0, audf);
                    chip.write(0x09, 0);
                    chip.write(0x0e, 1);
                    let period = u32::from(audf) + 4;
                    let mut time = 0;
                    let mut warmup = Vec::new();
                    while time < 4 * period && warmup.len() < 2 {
                        if clock(&mut chip, &mut time) {
                            warmup.push(time);
                        }
                    }
                    assert_eq!(warmup.len(), 2, "missing warmup IRQs");
                    assert_eq!(warmup[1] - warmup[0], period);
                    let first = time + period;
                    let write = first - lead;
                    let end = first + 12 + 4 * period;
                    let expected: Vec<u32> = if action == 0 {
                        (first..=end).step_by(period as usize).collect()
                    } else {
                        let reload = write + if action >= 2 { action - 1 } else { 0 } + 4;
                        (first..reload)
                            .step_by(period as usize)
                            .chain((reload + period..=end).step_by(period as usize))
                            .collect()
                    };
                    let mut observed = Vec::new();
                    while time < end {
                        if clock(&mut chip, &mut time) {
                            observed.push(time);
                        }
                        if action != 0
                            && (time == write || (action >= 2 && time == write + action - 1))
                        {
                            chip.write(0x09, 0);
                        }
                    }
                    let matches = observed == expected;
                    println!(
                        "STIMER clock={frequency} audf={audf} lead={lead} action={action} expected={expected:?} observed={observed:?} matches={matches}"
                    );
                    if action == 0 {
                        assert!(matches, "no-reset control disagrees");
                        controls += 1;
                    }
                    failures += usize::from(!matches);
                    cases += 1;
                }
            }
        }
    }
    assert_eq!((cases, controls), (96, 24));
    println!("STIMER_SUMMARY cases={cases} controls={controls} failures={failures}");
    assert_eq!(
        failures, 0,
        "STIMER must preserve pending IRQs until its reset stages arrive"
    );
}
