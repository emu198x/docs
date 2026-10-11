use machine_commodore_pet::Pet;
fn main() {
    println!("columns,edge,clock,via_high,pia_flag");
    for columns in [40,80] {
        for edge in [0u8,2] {
            let program=[0x78,0xA9,4|edge,0x8D,0x13,0xE8,
                0xAD,0x40,0xE8,0x8D,0x00,0x02,
                0xAD,0x13,0xE8,0x8D,0x01,0x02,
                0xAD,0x12,0xE8,0x4C,0x06,0xF0];
            let mut rom=vec![0xEA;4096];rom[..program.len()].copy_from_slice(&program);
            rom[0xFFC..0xFFE].copy_from_slice(&0xF000u16.to_le_bytes());
            let mut pet=Pet::new(rom,vec![0;8192],vec![0;2048],vec![0;4096],columns);
            let mut via_clock=0;
            while pet.master_clock()<80000 {
                pet.step_instruction();
                if pet.cpu().regs.pc==0xF009 {via_clock=pet.master_clock();}
                if pet.cpu().regs.pc==0xF012 {
                    println!("{columns},{edge},{via_clock},{},{}",u8::from(pet.peek(0x200)&32!=0),u8::from(pet.peek(0x201)&128!=0));
                }
            }
        }
    }
}
