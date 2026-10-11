use atari_pokey::Pokey;

fn samples(chip: &mut Pokey, channel: usize) -> Vec<f32> {
    for _ in 0..240 {
        chip.tick();
    }
    let mut buffers = chip.take_channel_buffers();
    let result = std::mem::take(&mut buffers[channel]);
    assert!(result.len() >= 6, "missing public channel samples");
    result
}

fn all_equal(values: &[f32], expected: f32) -> bool {
    values
        .iter()
        .all(|value| (value - expected).abs() < 0.00001)
}

#[test]
fn stimer_presets_audio_and_retains_it_beneath_volume_only() {
    let mut cases = 0;
    let mut failures = 0;
    let mut controls = 0;
    for frequency in [1_789_772, 1_773_447] {
        for channel in 0..4 {
            for previous in [false, true] {
                for volume_only in [false, true] {
                    for reset in [false, true] {
                        let mut chip = Pokey::new(frequency);
                        chip.write(0x0f, 3);
                        chip.write((channel * 2) as u8, 255);
                        chip.write((channel * 2 + 1) as u8, 0xaf);
                        chip.write(0x09, 0);
                        let inverted = channel < 2;
                        let prior_level = f32::from(u8::from(previous ^ inverted));
                        // Find the requested state through public output, without
                        // using the implementation's reset/power-up phase.
                        let mut stable = 0;
                        for _ in 0..(256 * 28 * 3) {
                            chip.tick();
                            let buffers = chip.take_channel_buffers();
                            for value in &buffers[channel] {
                                stable = if (*value - prior_level).abs() < 0.00001 {
                                    stable + 1
                                } else {
                                    0
                                };
                            }
                            if stable >= 2 {
                                break;
                            }
                        }
                        assert!(stable >= 2, "failed to establish prior waveform state");
                        chip.write(
                            (channel * 2 + 1) as u8,
                            if volume_only { 0xbf } else { 0xaf },
                        );
                        let before = samples(&mut chip, channel);
                        assert!(all_equal(
                            &before[2..],
                            if volume_only { 1.0 } else { prior_level }
                        ));
                        if reset {
                            chip.write(0x09, 0);
                        }
                        let after = samples(&mut chip, channel);
                        let final_state = if reset { true } else { previous };
                        let final_level = f32::from(u8::from(final_state ^ inverted));
                        let visible_ok =
                            all_equal(&after[2..], if volume_only { 1.0 } else { final_level });
                        // Removing the volume override must reveal the reset state.
                        chip.write((channel * 2 + 1) as u8, 0xaf);
                        let exposed = samples(&mut chip, channel);
                        let hidden_ok = all_equal(&exposed[2..], final_level);
                        let matches = visible_ok && hidden_ok;
                        println!(
                            "RESET_OUTPUT clock={frequency} channel={channel} previous={previous} volume={volume_only} reset={reset} visible={:?} exposed={:?} expected={final_level} matches={matches}",
                            &after[2..],
                            &exposed[2..]
                        );
                        if !reset {
                            assert!(matches, "no-reset output control failed");
                            controls += 1;
                        }
                        failures += usize::from(!matches);
                        cases += 1;
                    }
                }
            }
        }
    }
    assert_eq!((cases, controls), (64, 32));
    println!("RESET_OUTPUT_SUMMARY cases={cases} controls={controls} failures={failures}");
    assert_eq!(
        failures, 0,
        "STIMER must preset the retained audio flip-flops"
    );
}
