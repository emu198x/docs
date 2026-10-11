// Original guest generator copied from the regression.

fn write(program: &mut Vec<u8>, address: u16, value: u8) {
    program.extend_from_slice(&[0xA9, value, 0x8D, address as u8, (address >> 8) as u8]);
}

fn select_mode(program: &mut Vec<u8>, mode: u8) {
    for bit in 0..5 {
        write(program, 0x8000, ((0x0C | mode) >> bit) & 1);
    }
}

fn address(program: &mut Vec<u8>, address: u16) {
    program.extend_from_slice(&[0x2C, 0x02, 0x20]); // BIT PPUSTATUS resets toggle
    write(program, 0x2006, (address >> 8) as u8);
    write(program, 0x2006, address as u8);
}

fn guest_prg(modes: &[u8]) -> Vec<u8> {
    let mut program = vec![0x78, 0xD8, 0xA2, 0xFF, 0x9A]; // SEI/CLD/LDX/TXS
    write(&mut program, 0x2000, 0);
    write(&mut program, 0x2001, 0);
    write(&mut program, 0x4015, 0);
    write(&mut program, 0x00FE, 0);
    write(&mut program, 0x00FF, 0);
    program.extend_from_slice(&[0x2C, 0x02, 0x20]);
    program.extend_from_slice(&[0x2C, 0x02, 0x20, 0x10, 0xFB]);
    program.extend_from_slice(&[0x2C, 0x02, 0x20, 0x10, 0xFB]); // two fresh vblanks
    select_mode(&mut program, 2); // vertical: first 2 KiB reaches both CIRAM pages
    address(&mut program, 0x2000);
    for block in 0..8u8 {
        program.extend_from_slice(&[
            0xA2,
            0,    // LDX #0
            0x8A, // TXA
            0x49,
            block * 17, // EOR #seed: distinguish every 256-byte block
            0x8D,
            7,
            0x20, // STA PPUDATA
            0xE8, // INX
            0xD0,
            0xF7, // BNE TXA
        ]);
    }
    for (phase, mode) in modes.iter().enumerate() {
        select_mode(&mut program, *mode);
        address(&mut program, 0x2000);
        program.extend_from_slice(&[0xAD, 7, 0x20]); // discard old buffered byte
        for block in 0..8u8 {
            program.extend_from_slice(&[
                0xA2,
                0, // LDX #0
                0xAD,
                7,
                0x20, // LDA PPUDATA
                0x9D,
                0,
                0x60 + block, // STA $6000+block*256,X
                0xE8,         // INX
                0xD0,
                0xF7, // BNE LDA
            ]);
        }
        let marker = u8::try_from(phase + 1).expect("short mode sequence");
        write(&mut program, 0x00FF, marker);
        // Wait for the host to inspect this phase before changing the mapper.
        program.extend_from_slice(&[0xA5, 0xFE, 0xC9, marker, 0xD0, 0xFA]);
    }
    let stop = 0xC000 + u16::try_from(program.len()).expect("short guest");
    program.extend_from_slice(&[0x4C, stop as u8, (stop >> 8) as u8]);
    let mut prg = vec![0; 32768];
    prg[16384..16384 + program.len()].copy_from_slice(&program);
    prg[32764..32766].copy_from_slice(&[0, 0xC0]);
    prg
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let output = std::path::PathBuf::from(std::env::args().nth(1).ok_or("output folder")?);
    std::fs::create_dir_all(&output)?;
    for mode in 0..4u8 {
        let mut rom = b"NES\x1a".to_vec();
        rom.extend_from_slice(&[2, 0, 0x10, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        rom.extend_from_slice(&guest_prg(&[mode]));
        std::fs::write(output.join(format!("mode{mode}.nes")), rom)?;
    }
    Ok(())
}
