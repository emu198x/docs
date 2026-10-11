use sharp_lr35902::Sm83;
fn main() {
    let mut rom = [0u8; 65536];
    rom[0x100..0x109].copy_from_slice(&[0x11, 0x00, 0xfe, 0x13, 0x1b, 0x00, 0xc3, 0x05, 0x01]);
    let mut cpu = Sm83::new();
    cpu.reset_post_bootrom();
    println!("cycle,pc,opcode,m_cycle,de,addr,mreq,rd,wr");
    let mut inc = 0;
    let mut dec = 0;
    for cycle in 0..12 {
        let de=u16::from_be_bytes([cpu.d,cpu.e]);
        println!("{cycle},{:04x},{:02x},{},{de:04x},{:04x},{},{},{}",cpu.pc,cpu.opcode,cpu.m_cycle,cpu.addr,cpu.mreq,cpu.rd,cpu.wr);
        if cpu.m_cycle==2 && cpu.opcode==0x13 {
            inc+=1;
            assert_eq!(de,0xfe01);
            assert_ne!(cpu.addr,0xfe00,"baseline unexpectedly exposes old DE");
            assert!(!cpu.mreq && !cpu.rd && !cpu.wr);
        }
        if cpu.m_cycle==2 && cpu.opcode==0x1b {
            dec+=1;
            assert_eq!(de,0xfe00);
            assert_ne!(cpu.addr,0xfe01,"baseline unexpectedly exposes old DE");
        }
        if cpu.mreq && cpu.rd { cpu.data_in=rom[usize::from(cpu.addr)]; }
        cpu.tick();
    }
    assert_eq!((inc,dec),(1,1),"both internal-cycle cases must actually execute");
}
