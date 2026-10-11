use format_nintendo_nes_ines::parse_ines;
use machine_nintendo_nes::Nes;
use std::panic::{AssertUnwindSafe, catch_unwind};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args().nth(1).ok_or("supply ROM path")?;
    let cart = parse_ines(&std::fs::read(path)?)?;
    let mut nes = Nes::new(cart.mapper);
    match catch_unwind(AssertUnwindSafe(|| {
        for _ in 0..6 {
            nes.run_frame();
            if nes.peek(0x04f1) == 0xa5 {
                break;
            }
        }
    })) {
        Ok(()) => {
            if nes.peek(0x04f1) != 0xa5 {
                return Err("guest did not finish".into());
            }
            println!(
                "{},{},{},{}",
                nes.peek(0x0400),
                nes.peek(0x0401),
                nes.peek(0x0402),
                nes.peek(0x0403)
            );
        }
        Err(_) => println!("panic"),
    }
    Ok(())
}
