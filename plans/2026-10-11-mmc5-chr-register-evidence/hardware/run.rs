//! Full-machine execution of the observation ROM; no low-bit hardware oracle.
use format_nintendo_nes_ines::parse_ines;
use machine_nintendo_nes::Nes;
use std::error::Error;
use std::fmt::Write as _;
use std::io::Write as _;
use std::path::PathBuf;

fn require(condition: bool, message: &str) -> Result<(), Box<dyn Error>> {
    if !condition {
        return Err(message.into());
    }
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    require(args.len() == 3, "usage: run ROM OUTPUT_DIRECTORY")?;
    let output = PathBuf::from(&args[2]);
    std::fs::create_dir_all(&output)?;
    let mut nes = Nes::new(parse_ines(&std::fs::read(&args[1])?)?.mapper);
    for _ in 0..60 {
        nes.run_frame();
        if nes.peek(0x04f1) == 0xa5 {
            break;
        }
    }
    require(nes.peek(0x04f0) == 0xa5, "sampling never completed")?;
    require(nes.peek(0x04f1) == 0xa5, "display never completed")?;
    require(nes.peek(0x04f7) == 32, "not all 32 rows executed")?;
    require(nes.peek(0x04f2) == 0, "guest read controls failed")?;
    for (offset, expected) in b"M5C1".iter().enumerate() {
        require(
            nes.peek(0x04f3 + offset as u16) == *expected,
            "wrong signature",
        )?;
    }
    // Finish a complete visible frame after the guest enables rendering.
    nes.run_frame();
    nes.run_frame();
    let nametable = nes.effective_nametable();
    require(
        &nametable[0x43..0x43 + b"MMC5 CHR OBSERVATION".len()] == b"MMC5 CHR OBSERVATION",
        "missing title",
    )?;
    let mut csv = String::from("mode,input,same_mode_page,retained_page,complement,repeat\n");
    let mut static_mismatches = 0;
    for row in 0..32u16 {
        let mode = row / 8;
        let input = row % 8;
        let retained = nes.peek(0x0400 + row);
        let same = nes.peek(0x0420 + row);
        let complement = nes.peek(0x0440 + row);
        let repeat = nes.peek(0x0460 + row);
        require(
            retained ^ complement == 255,
            "host complement control failed",
        )?;
        require(retained == repeat, "host repeated-read control failed")?;
        if mode == 3 {
            require(
                retained == input as u8,
                "1 KiB unchanged-mode control failed",
            )?;
        }
        let expected_same = (input << (3 - mode)) + (7 >> mode);
        static_mismatches += usize::from(u16::from(same) != expected_same);
        writeln!(
            csv,
            "{mode},{input},{same},{retained},{complement},{repeat}"
        )?;
        for (screen, value) in [(0xc5, retained), (0x185, same)] {
            let position = screen + usize::from(mode) * 32 + usize::from(input) * 3;
            require(
                &nametable[position..position + 2] == format!("{value:02X}").as_bytes(),
                "screen does not show the sampled RAM value",
            )?;
        }
    }
    std::fs::write(output.join("observations.csv"), csv)?;
    let ram: Vec<u8> = (0..2048u16).map(|addr| nes.peek(addr)).collect();
    std::fs::write(output.join("ram.bin"), ram)?;
    let mut ppm = std::fs::File::create(output.join("screen.ppm"))?;
    let pixels = nes.framebuffer();
    require(
        pixels.len() == 256 * 240,
        "unexpected framebuffer dimensions",
    )?;
    write!(ppm, "P6\n256 240\n255\n")?;
    for pixel in pixels {
        ppm.write_all(&[(pixel >> 16) as u8, (pixel >> 8) as u8, *pixel as u8])?;
    }
    println!("32 rows completed; complement/repeat/1KiB/display controls passed");
    println!("{static_mismatches}/32 static-page mismatches; low bits are observations only");
    Ok(())
}
