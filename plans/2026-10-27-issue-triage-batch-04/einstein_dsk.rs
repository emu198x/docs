use machine_tatung_einstein::Einstein;
fn image() -> Vec<u8> {
 let mut d=vec![0;1024]; d[..23].copy_from_slice(b"EXTENDED CPC DSK File\r\n");
 d[0x30]=1; d[0x31]=1; d[0x34]=3;
 d[256..268].copy_from_slice(b"Track-Info\r\n"); d[0x114]=2;d[0x115]=1;
 d[0x11a]=1;d[0x11b]=2;d[0x11f]=2;d[512..].fill(0x5a);d
}
#[test] fn malformed_media_is_rejected_without_panicking() {
 let control=image(); assert!(Einstein::validate_cpc_dsk(&control).is_ok());
 let mut cases=Vec::new(); let mut d=control.clone();d[0x115]=255;cases.push(("descriptor-count",d));
 let mut d=control.clone();d[0x114]=64;cases.push(("sector-size-shift",d));
 let mut d=control;d.truncate(512);cases.push(("missing-sector-payload",d));
 let mut failures=0;
 for (name,d) in cases {match std::panic::catch_unwind(||Einstein::validate_cpc_dsk(&d)) {
  Ok(Err(e))=>println!("{name}: rejected: {e}"),
  Ok(Ok(()))=>{println!("{name}: ACCEPTED");failures+=1},
  Err(_)=>{println!("{name}: PANIC");failures+=1}
 }} assert_eq!(failures,0,"malformed disk cases must return errors");
}
