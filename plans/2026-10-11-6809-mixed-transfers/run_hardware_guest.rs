use motorola_6809::Mc6809;
fn main() {
    let b = std::fs::read(std::env::args().nth(1).expect("binary path")).expect("read binary");
    let length = usize::from(u16::from_be_bytes([b[1], b[2]]));
    let origin = u16::from_be_bytes([b[3], b[4]]);
    assert_eq!(b.len(), length + 10);
    assert_eq!(b[0], 0);
    assert_eq!(&b[length + 5..], &[255, 0, 0, 0x68, 0]);
    let done = origin + u16::try_from(length).expect("length fits") - 2;
    let mut memory = [0; 65536];
    memory[usize::from(origin)..usize::from(origin) + length].copy_from_slice(&b[5..length + 5]);
    assert_eq!(
        &memory[usize::from(done)..usize::from(done) + 2],
        &[0x20, 0xfe]
    );
    let mut cpu = Mc6809::new();
    cpu.regs.pc = origin;
    cpu.addr = origin;
    cpu.sync = true;
    let mut cycles = 0;
    while cpu.addr != done || !cpu.sync {
        assert!(cycles < 100_000, "test did not reach Done loop");
        assert!(!cpu.halt, "CPU halted at {:04x}", cpu.addr);
        if cpu.rw {
            cpu.data_in = memory[usize::from(cpu.addr)];
        } else {
            memory[usize::from(cpu.addr)] = cpu.data;
        }
        cpu.tick();
        cycles += 1;
    }
    eprintln!("Reached hardware guest Done loop after {cycles} CPU cycles");
    for row in memory[0x400..0x540].chunks(32) {
        println!(
            "{}",
            row.iter()
                .map(|value| format!("{value:02x}"))
                .collect::<Vec<_>>()
                .join(" ")
        );
    }
}
