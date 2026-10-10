use machine_oric_atmos::{OricAtmos, OricModel};
use std::{env, fs};
fn main() {
    let out=env::args().nth(1).expect("output prefix");
    let rom=fs::read("/Users/stevehill/.emu198x/roms/oric/oric.rom").expect("ROM");
    let mut sys=OricAtmos::new(rom,OricModel::Atmos);
    for _ in 0..200 { sys.run_frame(); }
    sys.take_audio_buffer();
    sys.start_ay_write_watch();
    for (col,row) in [(5,3),(5,1),(0,1),(6,2),(7,5)] {
        sys.press_key(col,row);
        for _ in 0..4 { sys.run_frame(); }
        sys.release_key(col,row);
        for _ in 0..4 { sys.run_frame(); }
    }
    for _ in 0..100 { sys.run_frame(); }
    let audio=sys.take_audio_buffer();
    assert!(audio.iter().any(|s| s.abs()>0.01), "PING must produce audio");
    fs::write(format!("{out}.audio"),audio.iter().flat_map(|s|s.to_le_bytes()).collect::<Vec<_>>()).expect("audio");
    fs::write(format!("{out}.frame"),sys.framebuffer().iter().flat_map(|p|p.to_le_bytes()).collect::<Vec<_>>()).expect("frame");
    let writes:Vec<_>=sys.ay_write_watch_records().expect("watch").iter().map(|w|(w.pc,w.register,w.value)).collect();
    assert!(writes.iter().any(|w|w.1==13),"PING must program the envelope");
    fs::write(format!("{out}.writes"),format!("{writes:?}\n")).expect("writes");
    println!("samples={} AY writes={} cpu_cycles={}",audio.len(),writes.len(),sys.cpu_cycles());
}
