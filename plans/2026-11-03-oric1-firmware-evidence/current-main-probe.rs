use emu198x_shell::{FirmwareOverrides, build_variant};
use runtime_oric_atmos::{Model, OricRuntime};
use std::{fs,path::PathBuf};
fn boot(mut runtime: OricRuntime) -> String {
    let sys=runtime.machine_mut().expect("machine");
    for _ in 0..300 { sys.run_frame(); }
    (0..28).map(|row| {
        (0..40).map(|col| {
            let c=sys.peek(0xbb80+row*40+col)&0x7f;
            if (32..127).contains(&c) { char::from(c) } else { ' ' }
        }).collect::<String>()
    }).collect::<Vec<_>>().join("\n")
}
#[test]
fn generic_firmware_must_not_misidentify_oric1() {
    let root=PathBuf::from("/private/tmp/198x-oric-firmware-assets");
    for (model,file) in [(Model::Oric1,"basic10.rom"),(Model::Atmos,"basic11b.rom")] {
        let runtime=OricRuntime::new(model,fs::read(root.join(file)).expect("ROM")).expect("runtime");
        let screen=boot(runtime);
        println!("explicit {} {file}\n{screen}",model.variant_id());
        assert!(screen.contains("Ready"),"ROM must reach Ready");
        fs::write(root.join(format!("{}.screen.txt",model.variant_id())),screen).expect("screen");
    }
    let dir=root.join("generic-only");
    fs::create_dir_all(&dir).expect("directory");
    fs::copy(root.join("basic11b.rom"),dir.join("oric.rom")).expect("copy");
    let overrides=FirmwareOverrides { dir:Some(dir),..FirmwareOverrides::none() };
    let mut wrong=0;
    for model in Model::ALL {
        let runtime=build_variant::<OricRuntime>(model,&overrides).expect("resolve");
        let screen=boot(runtime);
        println!("generic-only {}\n{screen}",model.variant_id());
        assert!(screen.contains("Ready"));
        if model==Model::Oric1 && screen.contains("V1.1") { wrong+=1; }
    }
    println!("wrong-model boots={wrong}");
    assert_eq!(wrong,0,"selected Oric-1 must not automatically boot Atmos BASIC 1.1");
}
