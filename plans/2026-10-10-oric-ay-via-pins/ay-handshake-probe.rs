use machine_oric_atmos::{OricAtmos, OricModel};
fn main() {
    let mut mismatches = 0;
    for ca2 in [0x08, 0x0a, 0x0e] {
        for cb2 in [0x80, 0xa0, 0xe0] {
            let mut rom = vec![0xea; 16384];
            rom[0x3ffc..0x3ffe].copy_from_slice(&0xc000u16.to_le_bytes());
            let mut sys=OricAtmos::new(rom,OricModel::Atmos);
            sys.start_ay_write_watch();
            sys.poke(0x0303,0xff);
            sys.poke(0x030c,0xcc);
            sys.poke(0x0301,7);
            sys.poke(0x030c,ca2|cb2);
            let pins=(sys.via().ca2_drive,sys.via().ca2_out,sys.via().cb2_drive,sys.via().cb2_out);
            assert_eq!(pins,(true,true,true,true));
            let premature=sys.ay_write_watch_records().expect("watch").len();
            sys.poke(0x030c,0xcc);
            sys.poke(0x0301,0x38);
            sys.poke(0x030c,0xec);
            let writes=sys.ay_write_watch_records().expect("watch");
            let row:Vec<_>=writes.iter().map(|r|(r.register,r.value)).collect();
            let ok=premature==0 && row==[(7,0x38)];
            println!("PCR={:02x} pins={pins:?} premature={premature} writes={row:?} {}",ca2|cb2,if ok {"PASS"} else {"FAIL"});
            mismatches+=usize::from(!ok);
        }
    }
    println!("{mismatches}/9 mismatches");
    std::process::exit(i32::from(mismatches!=0));
}
