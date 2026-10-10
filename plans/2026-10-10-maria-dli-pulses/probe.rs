#[cfg(test)]
mod dli_probe {
    use super::*;

    #[test]
    fn consecutive_zone_interrupts_reach_the_cpu() {
        let mut mismatches = 0;
        for region in [Atari7800Region::Ntsc, Atari7800Region::Pal] {
            for height in [1_u8, 2, 3, 16] {
                for mode in [0, 1, 2] {
                    let mut rom = vec![0xea; 0x8000];
                    // Set DPP=$1800, enable DMA, then idle. NMI increments $40.
                    rom[..16].copy_from_slice(&[
                        0x78, 0xa9, 0x18, 0x85, 0x2c, 0xa9, 0x00, 0x85, 0x30, 0xa9, 0x40, 0x85,
                        0x3c, 0x4c, 0x0d, 0x80,
                    ]);
                    rom[0x100..0x103].copy_from_slice(&[0xe6, 0x40, 0x40]);
                    rom[0x7ffa..].copy_from_slice(&[0x00, 0x81, 0x00, 0x80, 0x00, 0x80]);
                    let mut machine = Atari7800::new(rom, region).expect("probe cartridge");
                    for (index, entry) in machine.ram_main[..768].chunks_exact_mut(3).enumerate() {
                        let enabled = mode == 1 || (mode == 2 && index % 2 == 0);
                        entry.copy_from_slice(&[
                            if enabled { 0x80 } else { 0 } | (height - 1),
                            0x1c,
                            0x00,
                        ]);
                    }
                    // Count the chip's actual DLI requests separately from CPU
                    // delivery, without assuming an absolute hardware raster origin.
                    let mut chip = Maria::new(region.maria_region());
                    chip.write(0x0c, 0x18);
                    chip.write(0x10, 0x00);
                    chip.write(0x1c, 0x40);
                    let mut requests = 0;
                    for _ in 0..region.lines_per_frame() {
                        chip.render_line(&mut |address| {
                            if (0x1800..0x2800).contains(&address) {
                                machine.ram_main[usize::from(address - 0x1800)]
                            } else {
                                0
                            }
                        });
                        requests += u32::from(chip.take_dli());
                    }
                    let mut edges = 0;
                    let mut previous = false;
                    let mut first_edge = None;
                    for _ in 0..machine.clocks_per_frame {
                        machine.tick_colour_clock();
                        if machine.cpu.nmi && !previous {
                            edges += 1;
                            first_edge.get_or_insert((
                                machine.master_clock,
                                machine.line_cycle,
                                machine.dma_budget,
                            ));
                        }
                        previous = machine.cpu.nmi;
                    }
                    let handled = u32::from(machine.ram_zp[0]);
                    println!(
                        "region={region:?} height={height} mode={mode} requests={requests} edges={edges} handlers={handled} first_edge={first_edge:?}"
                    );
                    if edges != requests || handled != requests {
                        mismatches += 1;
                    }
                }
            }
        }
        assert_eq!(mismatches, 0, "every chip DLI request must reach the CPU");
    }
}
