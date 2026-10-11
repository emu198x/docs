use motorola_6809::Mc6809;
fn main() {
    println!("opcode value cc pc cycles a b result_cc result_pc memory result_x trace halted");
    for op in [
        0x12, 0x1b, 0x19, 0x1a, 0x1c, 0x1d, 0x3a, 0x3d, 0x40, 0x41, 0x43, 0x44, 0x45, 0x46, 0x47,
        0x48, 0x49, 0x4a, 0x4c, 0x4d, 0x4f, 0x50, 0x51, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5a, 0x5c, 0x5d, 0x5f,
    ] {
        for v in [0, 1, 0x09, 0x10, 0x7f, 0x80, 0xfe, 0xff] {
            for cc in [0, 1, 0xfe, 0xff] {
                for pc in [0x4000u16, 0xfffe, 0xffff] {
                    let mut cpu = Mc6809::new();
                    cpu.regs.pc = pc;
                    cpu.addr = pc;
                    cpu.sync = true;
                    cpu.regs.a = v;
                    cpu.regs.b = v ^ 0xa5;
                    cpu.regs.cc = cc;
                    cpu.regs.dp = 0x50;
                    cpu.regs.x = 0x50a5;
                    let mut memory = [0; 65536];
                    memory[usize::from(pc)] = op;
                    memory[usize::from(pc.wrapping_add(1))] = if op < 0x10 {
                        0xa5
                    } else if op & 0xf0 == 0x60 {
                        0x84
                    } else if op & 0xf0 == 0x70 {
                        0x50
                    } else {
                        0x12
                    };
                    memory[usize::from(pc.wrapping_add(2))] = 0xa5;
                    memory[0x50a5] = v;
                    let mut trace = Vec::new();
                    loop {
                        assert!(cpu.total_cycles < 32);
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
                    println!(
                        "{op:02x} {v:02x} {cc:02x} {pc:04x} {} {:02x} {:02x} {:02x} {:04x} {:02x} {:04x} {} {}",
                        cpu.total_cycles,
                        cpu.regs.a,
                        cpu.regs.b,
                        cpu.regs.cc,
                        cpu.regs.pc,
                        memory[0x50a5],
                        cpu.regs.x,
                        trace.join(","),
                        cpu.halt
                    );
                }
            }
        }
    }
}
