use sega_vdp::{SegaVdp, VdpRegion, VdpVariant};
fn main() {
    let mut failures = 0;
    let mut controls = 0;
    println!("region,chip,probe,actual,expected");
    for region in [VdpRegion::Ntsc, VdpRegion::Pal] {
        for chip in [VdpVariant::Sms1, VdpVariant::Sms2] {
            let mut vdp = SegaVdp::new(region, chip);
            for (reg, value) in [(0, 0x14), (1, 0x40), (10, 31)] {
                vdp.write_control(value);
                vdp.write_control(0x80 | reg);
            }
            let lines = if region == VdpRegion::Ntsc { 262 } else { 313 };
            for _ in 0..lines * 342 {
                vdp.tick();
            }
            vdp.read_status();
            for _ in 0..lines * 342 {
                let line = vdp.scanline();
                let dot = vdp.dot();
                if line == 30 {
                    // MAME hcount(), expressed in its physical raster position.
                    let hpos = (i32::from(dot) + 63) % 342;
                    let previous = if hpos == 0 { 341 } else { hpos - 1 };
                    let expected = ((previous - 46) >> 1) as u8;
                    vdp.latch_h_counter();
                    assert_eq!(vdp.read_h_counter(), expected, "H-count control");
                    controls += 1;
                }
                if line == 31 && dot == 0 {
                    let actual = vdp.read_v_counter();
                    println!("{region:?},{chip:?},vc_at_active_31,{actual},31");
                    failures += usize::from(actual != 31);
                }
                let old_irq = vdp.interrupt;
                vdp.tick();
                if !old_irq && vdp.interrupt {
                    // MAME physical HINT hpos 26, first active hpos 63.
                    // R10=31 first IRQ precedes active line 31.
                    let timestamp = u32::from(vdp.scanline()) * 342 + u32::from(vdp.dot());
                    let expected = 31 * 342 - (63 - 26);
                    println!("{region:?},{chip:?},irq_dot,{timestamp},{expected}");
                    failures += usize::from(timestamp != expected);
                    break;
                }
            }
        }
    }
    assert_eq!(controls, 4 * 342, "all horizontal positions exercised");
    eprintln!("{controls} horizontal controls passed; {failures} phase failures");
    assert_eq!(failures, 0, "VDP phase disagrees with reference");
}
