use ti_sn76489::{NoiseLfsr, Sn76489};
const CLOCKS: usize = 16384;
fn make(channel: u8, mask: u8) -> Sn76489 {
    let mut psg = Sn76489::new(3_579_545, NoiseLfsr::Sega16);
    if channel < 3 {
        psg.write(0x80 | (channel << 5) | 7);
        psg.write(0);
    } else {
        psg.write(0xE4);
    }
    psg.write(0x90 | (channel << 5));
    psg.write_stereo(mask);
    psg
}
fn render(psg: &mut Sn76489) -> Vec<f32> {
    for _ in 0..CLOCKS { psg.tick(); }
    let samples = psg.take_buffer_stereo();
    assert!(!samples.is_empty() && samples.len().is_multiple_of(2));
    assert!(samples.iter().all(|s| s.is_finite()));
    samples
}
fn main() {
    let mut checked = 0;
    let mut failures = 0;
    let mut side_failures = [0; 2];
    for channel in 0..4 {
        let control = render(&mut make(channel, 0xFF));
        assert!(control.iter().any(|s| *s != 0.0), "channel {channel} silent");
        assert!(control.chunks_exact(2).all(|s| s[0] == s[1]));
        for mask in 0..=u8::MAX {
            let actual = render(&mut make(channel, mask));
            assert_eq!(actual.len(), control.len());
            let mut mismatched = false;
            for (side, shift) in [4, 0].into_iter().enumerate() {
                let enabled = mask & (1 << (channel + shift)) != 0;
                let matches = actual.chunks_exact(2).zip(control.chunks_exact(2))
                    .all(|(a,c)| a[side] == if enabled { c[side] } else { 0.0 });
                if !matches { side_failures[side] += 1; mismatched = true; }
            }
            failures += usize::from(mismatched);
            checked += 1;
        }
    }
    assert_eq!(checked, 1024);
    println!("mask cases={checked}, mismatches={failures}, left={}, right={}", side_failures[0], side_failures[1]);
    // A write after generating audio cannot reroute that audio retroactively.
    let mut pending = make(0, 0x10);
    for _ in 0..CLOCKS { pending.tick(); }
    pending.write_stereo(0x01);
    let before = pending.take_buffer_stereo();
    assert!(!before.is_empty());
    let historical_left = before.chunks_exact(2).all(|s| s[1] == 0.0)
        && before.chunks_exact(2).any(|s| s[0] != 0.0);
    println!("pre-write samples retain left-only routing: {historical_left}");
    assert_eq!(failures, 0, "panning does not select the enabled outputs");
    assert!(historical_left);
}
