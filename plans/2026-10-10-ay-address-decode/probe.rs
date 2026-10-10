use emu198x_gi_ay_3_8910::Ay3_8910;
fn main() {
    let mut invalid=0;
    let mut mutations=0;
    let mut latch_changes=0;
    let mut non_ff_reads=0;
    let mut valid=0;
    for prior in 0..16 {
        for address in 0..=255 {
            let mut ay=Ay3_8910::new(1_000_000,44_100,1024);
            for reg in 0..16 { ay.select_register(reg); ay.write_data(0); }
            ay.select_register(prior);
            let before=*ay.registers();
            ay.select_register(address);
            let selected=ay.selected_register();
            ay.write_data(0x55);
            let read=ay.read_data();
            if address<16 {
                assert_eq!(selected,address,"valid address must latch");
                assert_ne!(*ay.registers(),before,"valid write must reach a register");
                valid+=1;
            } else {
                invalid+=1;
                let changed=*ay.registers()!=before;
                let latch_changed=selected!=prior;
                mutations+=usize::from(changed);
                latch_changes+=usize::from(latch_changed);
                non_ff_reads+=usize::from(read!=0xff);
                if prior==7 && address>=0xf0 {
                    println!("prior={prior:02x} address={address:02x} selected={selected:02x} mutated={changed} read={read:02x}");
                }
            }
        }
    }
    assert_eq!(valid,256);
    assert_eq!(invalid,3840);
    println!("valid_controls={valid} invalid_addresses={invalid} rejected_write_mutations={mutations} changed_register_latches={latch_changes} reads_other_than_ff={non_ff_reads}");
    std::process::exit(i32::from(mutations!=0 || latch_changes!=0));
}
