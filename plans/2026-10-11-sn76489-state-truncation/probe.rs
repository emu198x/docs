use ti_sn76489::{NoiseLfsr, Sn76489};
fn main() {
    let mut source = Sn76489::new(3_579_545, NoiseLfsr::Sega16);
    source.write(0x8A); source.write(0x23); source.write(0xE5); source.write_stereo(0xA5);
    let mut encoded = Vec::new(); source.save_state(&mut encoded);
    println!("encoder bytes={}", encoded.len());
    let mut bad = 0;
    for length in 0..encoded.len() {
        let mut destination = Sn76489::new(3_579_545, NoiseLfsr::Sega16);
        let mut before = Vec::new(); destination.save_state(&mut before);
        assert_ne!(before, encoded);
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| destination.load_state(&encoded[..length])));
        let mut after = Vec::new(); destination.save_state(&mut after);
        if !matches!(result, Ok(Err(_))) || before != after {
            bad += 1;
            println!("length={length}, panic={}, changed={}", result.is_err(), before != after);
        }
    }
    println!("truncated cases={}, bad={bad}", encoded.len());
    assert_eq!(bad, 0);
}
