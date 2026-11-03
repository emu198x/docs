//! Private-input resolver continuation; retained with the issue evidence.
use emu198x_shell::{build_variant,FirmwareOverrides};
use runtime_oric_atmos::{Model,OricRuntime};
use std::path::PathBuf;
fn boot(mut runtime:OricRuntime)->String {
    for _ in 0..300 {runtime.machine_mut().expect("live").run_frame();}
    let sys=runtime.machine().expect("live");
    (0..28).map(|row|(0..40).map(|col|{let c=sys.peek(0xbb80+row*40+col)&0x7f;if (32..127).contains(&c){char::from(c)}else{' '}}).collect::<String>()).collect::<Vec<_>>().join("\n")
}
#[test]
fn model_specific_resolver_boots_and_generic_only_rejects_oric1() {
    let root=PathBuf::from("/private/tmp/198x-oric-firmware-assets");
    let generic=FirmwareOverrides{dir:Some(root.join("generic-only")),..FirmwareOverrides::none()};
    let error=build_variant::<OricRuntime>(Model::Oric1,&generic).err().expect("generic Atmos directory must reject for Oric-1");
    assert!(error.to_string().contains("oric1-rom"));
    assert!(boot(build_variant::<OricRuntime>(Model::Atmos,&generic).expect("Atmos fallback")).contains("V1.1"));
    let named=FirmwareOverrides{dir:Some(root),..FirmwareOverrides::none()};
    for (model,banner) in [(Model::Oric1,"ORIC EXTENDED BASIC V1.0"),(Model::Atmos,"ORIC EXTENDED BASIC V1.1")] {
        let text=boot(build_variant::<OricRuntime>(model,&named).expect("author filenames resolve"));
        assert!(text.contains(banner)&&text.contains("Ready"),"{text}");
        println!("{}: shared resolver selected {banner} and reached Ready",model.variant_id());
    }
    println!("generic-only Atmos directory rejects Oric-1 with its own missing-firmware ID");
}
