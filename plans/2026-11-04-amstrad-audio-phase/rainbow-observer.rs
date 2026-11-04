use super::*;
use serde::Serialize;
use std::path::PathBuf;

#[derive(Serialize)]
struct PhaseAudit {
    boot_hash: String,
    times: Vec<u64>,
}

#[test]
#[ignore = "PRIVATE PROBE: original firmware/media, explicit output"]
fn observe_rainbow_native_fields() {
    let output = PathBuf::from(std::env::var_os("EMU198X_PHASE_AUDIT_OUT").expect("output"));
    std::fs::create_dir_all(&output).expect("directory");
    let manifest = load_manifest(std::path::Path::new("manifest/spectrum.toml")).expect("manifest");
    let entry = manifest
        .entry
        .iter()
        .find(|entry| entry.id == "rainbow-islands-plus3")
        .expect("case");
    let firmware_root =
        PathBuf::from(std::env::var_os("HOME").expect("HOME")).join(".emu198x/roms");
    let media_root = PathBuf::from("/Volumes/Data/Library/ROMs/TOSEC");
    let files = lookup_firmware(&manifest, "plus3").expect("firmware map");
    assert_eq!(files.len(), 4);
    let roms: Vec<_> = files
        .iter()
        .map(|file| read_firmware_bytes(&firmware_root, file).expect("ROM"))
        .collect();
    let mut session = HeadlessSession::new_with_query_provider(
        build_plus3_runtime(&roms[0], &roms[1], &roms[2], &roms[3]),
        u64::from(TIMING_PLUS2A.halfcycles_per_frame),
        SpectrumSessionQueryProvider,
    );
    let media = entry.media.as_ref().expect("disk");
    let _ = load_media_spec(&mut session, media, &media_root).expect("original disk");
    autoload_plus3_loader(&mut session, DEFAULT_128K_BOOT_FRAMES).expect("ordinary disk loader");
    let (boot_hash, png) =
        run_script_then_capture_boot_frame(&mut session, entry).expect("ordinary waypoint");
    assert_eq!(
        boot_hash, "xxh64:c5a96435f59811ff",
        "observer must preserve normal capture"
    );
    std::fs::write(output.join("normal.png"), png).expect("ordinary image");
    let mut times = Vec::new();
    for field in 0..64 {
        if field > 0 {
            session.run_frames(1).expect("native frame");
        }
        let frame = &session.machine().machine().framebuffer;
        assert_eq!(frame.len(), 352 * 296);
        assert!(frame.iter().all(|value| *value < 16));
        times.push(session.time().get());
        std::fs::write(output.join(format!("{field:03}.indices")), frame).expect("indexed frame");
    }
    assert!(times.windows(2).all(|pair| pair[1] - pair[0] == 354_540));
    let audit = PhaseAudit { boot_hash, times };
    std::fs::write(
        output.join("audit.toml"),
        toml::to_string(&audit).expect("audit"),
    )
    .expect("audit output");
}
