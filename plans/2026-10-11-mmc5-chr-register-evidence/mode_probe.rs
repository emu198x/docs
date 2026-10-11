use format_nintendo_nes_ines::{Mapper, Mmc5};
fn main() {
    let chr: Vec<u8> = (0..1024 * 1024).map(|offset| ((offset / 1024) % 251) as u8).collect();
    println!("write_mode,read_mode,bank,actual,expected_known_bits");
    for read_mode in 0..4 {
        for bank in [0x18, 0x38, 0x78, 0xf8] {
            let mut mapper = Mmc5::new(vec![0; 32768], chr.clone());
            mapper.cpu_write(0x5101, 3);
            for reg in 0x5120..=0x5127 { mapper.cpu_write(reg, bank); }
            mapper.cpu_write(0x5101, read_mode);
            // All bank values align to 8 KiB: the same physical base remains
            // selected when merely widening the PPU offset passthrough.
            println!("3,{read_mode},{bank},{},{}", mapper.chr_read(0), bank);
        }
    }
}
