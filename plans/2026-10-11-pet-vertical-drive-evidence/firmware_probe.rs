use machine_commodore_pet::{Pet, PetKey};
fn screen(pet: &Pet) -> String {
 (0x8000..0x83e8).map(|a|match pet.peek(a)&127 {1..=26=>char::from(b'@'+(pet.peek(a)&127)),32..=63=>char::from(pet.peek(a)&127),_=>' '}).collect::<String>().split_whitespace().collect::<Vec<_>>().join(" ")
}
fn report(pet: &Pet, label: &str) {
 println!("{label}: frame={} clock={} pc={:04x} screen={:?}",pet.frame_count(),pet.master_clock(),pet.cpu().regs.pc,screen(pet));
 for row in 0..10 {let bytes:Vec<_>=(0..40).map(|x|pet.peek(0x8000+row*40+x)).collect();if bytes.iter().any(|b|*b!=32){println!("row {row}: {bytes:?}");}}
}
fn tap(pet:&mut Pet,key:PetKey){pet.press_key(key);for _ in 0..5{pet.run_frame();}pet.release_key(key);for _ in 0..5{pet.run_frame();}}
fn main(){
 let home=std::env::var("HOME").expect("home");let p=std::path::PathBuf::from(home).join(".emu198x/roms/commodore-pet");
 let read=|name|std::fs::read(p.join(name)).expect("fixture");let mut pet=Pet::new(read("kernal.rom"),read("basic.rom"),read("editor.rom"),read("char.rom"),40);
 for _ in 0..120{pet.run_frame();} report(&pet,"boot120");
 for key in [PetKey::A,PetKey::B,PetKey::CursorRight,PetKey::C]{tap(&mut pet,key);report(&pet,"key");}
 for _ in 0..100{pet.run_frame();}report(&pet,"extra100");
}
