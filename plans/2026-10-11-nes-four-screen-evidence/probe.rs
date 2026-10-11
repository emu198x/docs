use format_nintendo_nes_ines::{Mapper, parse_ines};
use ricoh_ppu_2c02::Ppu;
use std::panic::{AssertUnwindSafe, catch_unwind};

fn address(ppu: &mut Ppu, mapper: &mut dyn Mapper, addr: u16) {
    ppu.cpu_read(2, mapper);
    ppu.cpu_write(6, (addr >> 8) as u8, mapper);
    ppu.cpu_write(6, addr as u8, mapper);
}

fn sample(mapper_id: u8, nes2: bool, four_screen: bool, mirror_write: u8) {
    let mut rom = vec![0; 16 + 32768 + 8192];
    rom[..4].copy_from_slice(b"NES\x1a");
    rom[4] = 2;
    rom[5] = 1;
    rom[6] = (mapper_id << 4) | 1 | if four_screen { 8 } else { 0 };
    rom[7] = if nes2 { 8 } else { 0 };
    let cart = parse_ines(&rom).expect("valid synthetic cartridge");
    let header = cart.header.mirroring;
    let mut mapper = cart.mapper;
    mapper.cpu_write(0xA000, mirror_write);
    let mapped = mapper.mirroring();
    let mut ppu = Ppu::new();
    let result = catch_unwind(AssertUnwindSafe(|| {
        for page in 0..4u16 {
            address(&mut ppu, &mut *mapper, 0x2000 + page * 1024);
            ppu.cpu_write(7, (page + 1) as u8 * 17, &mut *mapper);
        }
        let mut bytes = [0; 4];
        for page in 0..4u16 {
            address(&mut ppu, &mut *mapper, 0x2000 + page * 1024);
            ppu.cpu_read(7, &mut *mapper);
            for _ in 0..12 {
                ppu.tick(&mut *mapper);
            }
            bytes[page as usize] = ppu.cpu_read(7, &mut *mapper);
        }
        bytes
    }));
    match result {
        Ok(bytes) => println!(
            "{mapper_id},{nes2},{four_screen},{mirror_write},{header:?},{mapped:?},ok,{bytes:?}"
        ),
        Err(_) => println!(
            "{mapper_id},{nes2},{four_screen},{mirror_write},{header:?},{mapped:?},panic,[]"
        ),
    }
}
fn main() {
    println!("mapper,nes2,four_screen,mirror_write,header_mapping,live_mapping,result,bytes");
    for nes2 in [false, true] {
        for mapper in [0, 4] {
            for four in [false, true] {
                for mirror in [0, 1] {
                    sample(mapper, nes2, four, mirror);
                }
            }
        }
    }
}
