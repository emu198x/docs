use motorola_6809::Mc6809;
use std::io::{self, Write};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let expected_cycles: u64 = args.get(1).map_or(2, |s| s.parse().expect("cycle count"));
    let expected_second: u16 = args.get(2).map_or(0xffff, |s| {
        u16::from_str_radix(s, 16).expect("second read address")
    });
    let mut output = io::BufWriter::new(io::stdout().lock());
    let mut checked = 0;
    for pc in [0x4000u16, 0xfffe, 0xffff] {
        for opcode in [0x4d, 0x5d] {
            let mut memory = [0; 65536];
            memory[0xffff] = 0x37;
            memory[usize::from(pc)] = opcode;
            memory[usize::from(pc.wrapping_add(1))] = 0x12;
            for value in 0..=u8::MAX {
                for cc in 0..=u8::MAX {
                    let mut cpu = Mc6809::new();
                    cpu.regs.pc = pc;
                    cpu.addr = pc;
                    cpu.sync = true;
                    cpu.regs.a = if opcode == 0x4d { value } else { 0x5a };
                    cpu.regs.b = if opcode == 0x5d { value } else { 0xa5 };
                    cpu.regs.cc = cc;
                    cpu.regs.dp = 0x42;
                    cpu.regs.x = 0x1234;
                    cpu.regs.y = 0x5678;
                    cpu.regs.u = 0x9abc;
                    cpu.regs.s = 0xdef0;
                    let old_a = cpu.regs.a;
                    let old_b = cpu.regs.b;
                    loop {
                        assert!(cpu.total_cycles < 8, "no instruction boundary");
                        assert!(cpu.rw && !cpu.halt, "TST must not write or halt");
                        if cpu.total_cycles == 0 {
                            assert_eq!(cpu.addr, pc);
                            assert!(cpu.sync);
                        } else {
                            assert_eq!(cpu.addr, expected_second, "discarded read address");
                            assert!(!cpu.sync);
                        }
                        cpu.data_in = memory[usize::from(cpu.addr)];
                        cpu.tick();
                        if cpu.sync {
                            break;
                        }
                    }
                    assert_eq!(cpu.total_cycles, expected_cycles, "instruction cycles");
                    assert_eq!(
                        (
                            cpu.regs.a,
                            cpu.regs.b,
                            cpu.regs.dp,
                            cpu.regs.x,
                            cpu.regs.y,
                            cpu.regs.u,
                            cpu.regs.s
                        ),
                        (old_a, old_b, 0x42, 0x1234, 0x5678, 0x9abc, 0xdef0)
                    );
                    assert_eq!(cpu.regs.pc, pc.wrapping_add(1));
                    assert_eq!(cpu.addr, cpu.regs.pc);
                    assert!(cpu.rw && cpu.sync && !cpu.halt);
                    output.write_all(&[cpu.regs.cc]).expect("output flags");
                    checked += 1;
                }
            }
        }
    }
    assert_eq!(checked, 393216);
    output.flush().expect("flush flags");
}
