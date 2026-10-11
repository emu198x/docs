#[cfg(test)]
mod borrow_probe {
    use super::*;

    #[test]
    fn linked_high_event_follows_low_event_by_three_clocks() {
        let mut failures = 0;
        let mut cases = 0;
        let mut chip = Pokey::new(1_789_772);
        for (lo, fast, link) in [(0_usize, 0x40, 0x10), (2, 0x20, 0x08)] {
            for low in [0_u8, 1, 15, 255] {
                for high in [0_u8, 1] {
                    chip.write(0x08, fast | link);
                    chip.write((lo * 2) as u8, low);
                    chip.write(((lo + 1) * 2) as u8, high);
                    chip.write((lo * 2 + 1) as u8, 0xa0);
                    chip.write(((lo + 1) * 2 + 1) as u8, 0xa0);
                    chip.write(0x09, 0);
                    let period = u32::from(low) + u32::from(high) * 256 + 7;
                    let mut last_low = None;
                    let mut high_times = Vec::new();
                    for time in 1..=period * 2 {
                        let previous_low = chip.channels[lo].output;
                        let previous_high = chip.channels[lo + 1].output;
                        chip.tick_channels(false);
                        if chip.channels[lo].output != previous_low {
                            last_low = Some(time);
                        }
                        if chip.channels[lo + 1].output != previous_high {
                            high_times.push(time);
                        }
                    }
                    assert_eq!(high_times.len(), 2, "the linked timer must execute");
                    assert_eq!(high_times[1] - high_times[0], period);
                    let gap = high_times[1] - last_low.expect("low channel event");
                    println!("channel={lo} low={low} high={high} period={period} gap={gap}");
                    failures += usize::from(gap != 3);
                    cases += 1;
                }
            }
        }
        assert_eq!(cases, 16);
        assert_eq!(
            failures, 0,
            "linked high event must follow the final low event by three clocks"
        );
    }
}
