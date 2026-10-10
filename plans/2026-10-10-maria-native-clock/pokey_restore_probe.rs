use atari_pokey::Pokey;

#[test]
fn restored_pokey_keeps_the_next_sample_phase() {
    let mut chip = Pokey::new(1_789_772);
    chip.write(1, 0x1f);
    for _ in 0..128 {
        chip.tick();
    }
    chip.take_buffer();
    let saved = postcard::to_allocvec(&chip).expect("snapshot");
    let mut restored: Pokey = postcard::from_bytes(&saved).expect("restore");
    for cycle in 0..64 {
        chip.tick();
        restored.tick();
        assert_eq!(chip.take_buffer(), restored.take_buffer(), "cycle {cycle}");
    }
}
