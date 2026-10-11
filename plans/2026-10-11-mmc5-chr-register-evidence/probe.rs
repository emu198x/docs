use format_nintendo_nes_ines::{Mapper, Mmc5};
fn main() {
    let chr: Vec<u8> = (0..1024 * 1024).map(|offset| ((offset / 1024) % 251) as u8).collect();
    println!("mode,bank,mismatched_reads,first_actual,first_expected");
    for mode in 0..4 {
        for bank in 0..16u8 {
            let mut mapper = Mmc5::new(vec![0; 32768], chr.clone());
            mapper.cpu_write(0x5101, mode);
            for reg in 0x5120..=0x5127 { mapper.cpu_write(reg, bank); }
            let unit = 8192usize >> mode;
            let mut mismatches = 0;
            for addr in 0..0x2000u16 {
                let offset = usize::from(bank) * unit + usize::from(addr) % unit;
                if mapper.chr_read(addr) != chr[offset] { mismatches += 1; }
            }
            println!("{mode},{bank},{mismatches},{},{}", mapper.chr_read(0), chr[usize::from(bank)*unit]);
        }
    }
}
