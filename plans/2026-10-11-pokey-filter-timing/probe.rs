use atari_pokey::Pokey;

#[test]
fn synchronized_filter_timers_cannot_cancel_the_entire_output() {
    let mut cases = 0;
    let mut silent = 0;
    for clock in [1_789_772, 1_773_447] {
        for base in [0, 1] {
            for (channel, filter) in [(0, 4), (1, 2)] {
                for period in [0, 3, 15, 63] {
                    // Unfiltered, active filter, volume-only with filter.
                    for mode in 0..3 {
                        let mut chip = Pokey::new(clock);
                        chip.write(0x0f, 3);
                        chip.write(0x08, base | if mode == 0 { 0 } else { filter });
                        chip.write(channel * 2, period);
                        chip.write((channel + 2) * 2, period);
                        chip.write(channel * 2 + 1, if mode == 2 { 0xbf } else { 0xaf });
                        chip.write((channel + 2) * 2 + 1, 0xa0);
                        chip.write(0x09, 0);
                        for _ in 0..32768 {
                            chip.tick();
                        }
                        chip.take_buffer();
                        chip.take_channel_buffers();
                        for _ in 0..65536 {
                            chip.tick();
                        }
                        let taps = chip.take_channel_buffers();
                        let output = &taps[usize::from(channel)];
                        assert!(output.len() > 1700, "no host samples");
                        assert!(
                            output
                                .iter()
                                .all(|x| x.is_finite() && (0.0..=1.0).contains(x))
                        );
                        let min = output.iter().copied().fold(f32::INFINITY, f32::min);
                        let max = output.iter().copied().fold(f32::NEG_INFINITY, f32::max);
                        if mode == 0 {
                            assert!(max > min, "unfiltered timer did not produce a waveform");
                        } else if mode == 2 {
                            assert!(output.iter().all(|&x| x == 1.0), "volume-only override");
                        } else if max == 0.0 {
                            silent += 1;
                        }
                        println!(
                            "clock={clock} base={base} channel={channel} period={period} mode={mode} samples={} min={min} max={max}",
                            output.len()
                        );
                        cases += 1;
                    }
                }
            }
        }
    }
    assert_eq!(cases, 96);
    assert_eq!(
        silent, 0,
        "half-cycle filter offset cannot erase the entire waveform"
    );
}
