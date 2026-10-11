use motorola_6809::Mc6809;
use std::io::{self, BufRead, Write};
fn main() {
    let mut output = io::BufWriter::new(io::stdout().lock());
    let mut cases = 0;
    for line in io::stdin().lock().lines() {
        let line = line.expect("input row");
        let v: Vec<u16> = line
            .split_whitespace()
            .map(|s| u16::from_str_radix(s, 16).expect("hex input"))
            .collect();
        assert_eq!(v.len(), 13);
        let mut memory = [0u8; 65536];
        for (a, b) in memory.iter_mut().enumerate() {
            *b = ((a * 73) ^ (a >> 8) ^ 0xa5) as u8;
        }
        let mut cpu = Mc6809::new();
        cpu.regs.pc = v[12];
        cpu.addr = v[12];
        cpu.sync = true;
        cpu.regs.a = u8::try_from(v[4]).expect("A");
        cpu.regs.b = u8::try_from(v[5]).expect("B");
        cpu.regs.cc = u8::try_from(v[6]).expect("CC");
        cpu.regs.dp = u8::try_from(v[7]).expect("DP");
        cpu.regs.x = v[8];
        cpu.regs.y = v[9];
        cpu.regs.u = v[10];
        cpu.regs.s = v[11];
        for i in 0..4 {
            memory[usize::from(v[12].wrapping_add(i))] =
                u8::try_from(v[usize::from(i)]).expect("program byte");
        }
        let mut trace = Vec::new();
        loop {
            assert!(cpu.total_cycles < 32, "no boundary: {line}");
            let address = cpu.addr;
            let data = if cpu.rw {
                memory[usize::from(address)]
            } else {
                cpu.data
            };
            trace.push(format!(
                "{}{:04x}:{:02x}",
                if cpu.rw { 'r' } else { 'w' },
                address,
                data
            ));
            if cpu.rw {
                cpu.data_in = data;
            } else {
                memory[usize::from(address)] = data;
            }
            cpu.tick();
            if cpu.halt || cpu.sync {
                break;
            }
        }
        for value in v {
            write!(output, "{value:04x} ").expect("write key");
        }
        writeln!(
            output,
            "| {} {:02x} {:02x} {:02x} {:02x} {:04x} {:04x} {:04x} {:04x} {:04x} | {} | {}",
            cpu.total_cycles,
            cpu.regs.a,
            cpu.regs.b,
            cpu.regs.cc,
            cpu.regs.dp,
            cpu.regs.x,
            cpu.regs.y,
            cpu.regs.u,
            cpu.regs.s,
            cpu.regs.pc,
            trace.join(","),
            u8::from(cpu.halt)
        )
        .expect("write result");
        cases += 1;
    }
    assert_eq!(cases, 96800);
    output.flush().expect("flush result");
}
