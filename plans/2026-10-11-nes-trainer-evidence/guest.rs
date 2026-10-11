use format_nintendo_nes_ines::parse_ines;
use machine_nintendo_nes::Nes;
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args().nth(1).ok_or("ROM path")?;
    let cart = parse_ines(&std::fs::read(path)?)?;
    let mut nes = Nes::new(cart.mapper);
    for _ in 0..4 {
        nes.run_frame();
        if nes.peek(0x00ff) == 0xa5 {
            break;
        }
    }
    if nes.peek(0x00ff) != 0xa5 {
        return Err("guest did not finish".into());
    }
    for i in 0..512u16 {
        print!("{:02x}", nes.peek(0x0400 + i));
    }
    println!();
    Ok(())
}
