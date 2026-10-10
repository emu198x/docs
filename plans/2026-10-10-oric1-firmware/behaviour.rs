use machine_oric_atmos::{OricAtmos,OricModel};
use std::{fs,path::Path};
fn main() {
    let root=Path::new("/private/tmp/oric-firmware-audit");
    for (model,file) in [(OricModel::Oric1,"basic10.rom"),(OricModel::Atmos,"basic11b.rom")] {
        let selected=if std::env::args().any(|a| a=="--wrong-rom") && file=="basic10.rom" { "basic11b.rom" } else { file };
        let mut sys=OricAtmos::new(fs::read(root.join(selected)).expect("ROM"),model);
        for _ in 0..300 { sys.run_frame(); }
        for c in "PRINTASC(STR$(1))\n".chars() {
            let (col,row,shift)=match c {
                'P'=>(5,3,false),'R'=>(1,2,false),'I'=>(5,1,false),'N'=>(0,1,false),
                'T'=>(1,1,false),'A'=>(6,5,false),'S'=>(6,6,false),'C'=>(2,7,false),
                '('=>(3,1,true),')'=>(7,2,true),'$'=>(2,3,true),'1'=>(0,5,false),
                '\n'=>(7,5,false),_=>panic!("unmapped key")
            };
            if shift { sys.press_key(4,4); }
            sys.press_key(col,row);
            for _ in 0..4 {sys.run_frame();}
            sys.release_key(col,row);
            if shift {sys.release_key(4,4);}
            for _ in 0..4 {sys.run_frame();}
        }
        for _ in 0..50 {sys.run_frame();}
        let screen=(0..28).map(|row| (0..40).map(|col| {
            let c=sys.peek(0xbb80+row*40+col)&0x7f;
            if (32..127).contains(&c) {char::from(c)} else {' '}
        }).collect::<String>()).collect::<Vec<_>>().join("\n");
        println!("{file}\n{screen}");
        assert!(screen.contains("PRINTASC(STR$(1))"),"command must echo completely");
        assert!(!screen.contains("ERROR"),"command must execute");
        let expected=if file=="basic10.rom" { "2" } else { "32" };
        assert!(screen.lines().any(|line|line.trim()==expected),"ROM-specific STR$ result must match");
        assert_eq!(screen.matches("Ready").count(),2,"command must return to Ready");
        fs::write(root.join(format!("{file}.str-screen.txt")),screen).expect("screen");
    }
}
