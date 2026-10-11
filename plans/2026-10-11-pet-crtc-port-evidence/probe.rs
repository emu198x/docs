use machine_commodore_pet::Pet;

fn main() {
    let mut failures = 0;
    println!("columns,value,data_port,address_port,expected,done");
    for columns in [40, 80] {
        for value in 0..=255u8 {
            let program = [
                0x78, 0xD8, // SEI; CLD
                0xA9, 15, 0x8D, 0x80, 0xE8, // Select cursor low
                0xA9, value, 0x8D, 0x81, 0xE8, // Write cursor low
                0xAD, 0x81, 0xE8, 0x8D, 0x00, 0x02, // Actual LDA data port, record RAM
                0xAD, 0x80, 0xE8, 0x8D, 0x01, 0x02, // Record status/address port separately
                0xA9, 0xA5, 0x8D, 0x02, 0x02, // Completion marker
                0x4C, 0x1D, 0xF0, // Spin
            ];
            let mut kernal = vec![0xEA; 4096];
            kernal[..program.len()].copy_from_slice(&program);
            kernal[0xFFC..0xFFE].copy_from_slice(&0xF000u16.to_le_bytes());
            let mut pet = Pet::new(kernal, vec![0; 8192], vec![0; 2048], vec![0; 4096], columns);
            pet.run_frame();
            let done = pet.peek(0x0202) == 0xA5;
            assert!(done, "guest did not complete for {columns}/{value}");
            let actual = pet.peek(0x0200);
            failures += usize::from(actual != value);
            println!("{columns},{value},{actual},{},{value},{done}", pet.peek(0x0201));
        }
    }
    eprintln!("512 guest cases; {failures} data-port failures");
    if failures != 0 { std::process::exit(1); }
}
