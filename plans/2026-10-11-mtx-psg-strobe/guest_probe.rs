#[cfg(test)]
mod psg_strobe_probe {
    use super::*;

    #[test]
    fn out6_latches_and_in3_delivers_the_sound_byte() {
        let mut mismatches = 0;
        for model in [MtxModel::Mtx500, MtxModel::Mtx512] {
            let mut guest = vec![0xF3]; // DI
            for (write, value) in [
                (true, 0x85), // Unstrobed channel 0 write must be discarded.
                (true, 0xA7), // Replace latch with channel 1 low nibble.
                (false, 0), // Send $A7.
                (false, 0), // The latch persists across reads.
                (true, 0x12), // Channel 1 high bits, still only latched.
                (false, 0), // Send $12: channel 1 becomes $127.
                (true, 0x93), // Channel 0 attenuation, still only latched.
                (false, 0), // Send $93.
            ] {
                if write { guest.extend([0x3E, value, 0xD3, 0x06]); }
                else { guest.extend([0xDB, 0x03]); }
                guest.extend([0; 16]); // Leave the PSG READY interval clear.
            }
            guest.push(0x76);
            let mut rom = vec![0; 0x4000];
            rom[..guest.len()].copy_from_slice(&guest);
            let mut machine = Mtx::new(rom, model).expect("guest");
            machine.start_io_trace();
            let expected = [(0,0,15), (0,0,15), (0,7,15), (0,7,15),
                            (0,7,15), (0,0x127,15), (0,0x127,15), (0,0x127,3)];
            let mut n = 0;
            for _ in 0..1000 {
                machine.advance_tstates(1);
                let trace = machine.io_trace.as_ref().expect("trace enabled");
                if trace.len() > n {
                    assert_eq!(trace.len(), n+1);
                    let event = &trace[n];
                    let mut state = Vec::new(); machine.psg.save_state(&mut state);
                    let actual = (u16::from_le_bytes([state[0],state[1]]),
                                  u16::from_le_bytes([state[2],state[3]]),state[15]);
                    println!("STROBE,{model:?},{n},{},{},{:02x},{},{},{},{}",machine.master_clock(),event.write,event.value,
                             actual.0,actual.1,actual.2,actual==expected[n]);
                    if actual!=expected[n] { mismatches+=1; }
                    n+=1;
                    if n==expected.len() { break; }
                }
            }
            assert_eq!(n,expected.len(),"guest must execute all I/O");
        }
        assert_eq!(mismatches,0,"PSG changed before the sound strobe or retained an overwritten byte");
    }
}
