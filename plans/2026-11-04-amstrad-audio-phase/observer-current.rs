use super::*;
use serde::Serialize;
use std::path::PathBuf;

#[derive(Serialize)]
struct FieldWrites {
    field: u32,
    writes: Vec<common_sinclair_zx_spectrum::AyWriteRecord>,
}

#[derive(Serialize)]
struct Audit {
    id: String,
    boot_hash: String,
    audio_hash: String,
    start_time: u64,
    end_time: u64,
    fields: Vec<FieldWrites>,
}

#[test]
#[ignore = "PRIVATE PROBE: original ROM/media and explicit output directory"]
fn observe_amstrad_audio_window() {
    let id = std::env::var("EMU198X_AUDIO_AUDIT_ID").expect("case ID");
    let output = PathBuf::from(std::env::var_os("EMU198X_AUDIO_AUDIT_OUT").expect("output"));
    std::fs::create_dir_all(&output).expect("output directory");
    let manifest = load_manifest(std::path::Path::new("manifest/spectrum.toml")).expect("manifest");
    let entry = manifest
        .entry
        .iter()
        .find(|entry| entry.id == id)
        .expect("known case");
    assert_eq!(entry.variant, "plus2a");
    let firmware_root =
        PathBuf::from(std::env::var_os("HOME").expect("HOME")).join(".emu198x/roms");
    let media_root = PathBuf::from("/Volumes/Data/Library/ROMs/TOSEC");
    let files = lookup_firmware(&manifest, &entry.variant).expect("firmware map");
    assert_eq!(files.len(), 4);
    let roms: Vec<_> = files
        .iter()
        .map(|file| read_firmware_bytes(&firmware_root, file).expect("ROM"))
        .collect();
    let mut session = HeadlessSession::new_with_query_provider(
        build_plus2a_runtime(&roms[0], &roms[1], &roms[2], &roms[3]),
        u64::from(TIMING_PLUS2A.halfcycles_per_frame),
        SpectrumSessionQueryProvider,
    );
    let media = entry.media.as_ref().expect("media");
    let kind = load_media_spec(&mut session, media, &media_root).expect("mount media");
    let boot = session
        .wait_for_boot(DEFAULT_128K_BOOT_FRAMES)
        .expect("firmware menu");
    eprintln!("AUDIT_BOOT {} {}", boot.frames, session.time().get());
    let delay: u32 = std::env::var("EMU198X_AUDIO_AUDIT_DELAY")
        .unwrap_or_else(|_| "0".into())
        .parse()
        .expect("delay");
    assert!(delay <= 1, "bounded causal control");
    session
        .run_frames(delay)
        .expect("ordinary pre-loader delay");
    autoload_128k_tape_loader(&mut session, &media.slot, DEFAULT_128K_BOOT_FRAMES)
        .expect("ordinary loader");
    eprintln!("AUDIT_TAPE_START {}", session.time().get());
    wait_for_tape_stop(&mut session, kind, "tape.playing").expect("tape completes");
    eprintln!("AUDIT_TAPE_STOP {}", session.time().get());
    let (boot_hash, _) =
        run_script_then_capture_boot_frame(&mut session, entry).expect("ordinary waypoint");
    assert_eq!(boot_hash, entry.boot.frame_hash, "unchanged visual anchor");
    session
        .run_frames(entry.audio.from_frame)
        .expect("ordinary gap");
    session.clear_audio_capture();
    std::fs::write(
        output.join("before-ay.toml"),
        toml::to_string(&session.machine().machine().ay).expect("AY state"),
    )
    .expect("before state");
    let start_time = session.time().get();
    session.machine_mut().machine_mut().start_ay_write_watch();
    let count =
        (f64::from(entry.audio.secs) * spectrum_frames_per_sec(&TIMING_PLUS2A)).round() as u32;
    assert!(count > 0 && count <= 150, "bounded audio fields");
    let mut fields = Vec::new();
    for field in 0..count {
        eprintln!("AY_FIELD {field}");
        session.run_frames(1).expect("native field");
        let records = session
            .machine()
            .machine()
            .ay_write_watch_records()
            .expect("armed watch");
        assert!(
            records.len() < common_sinclair_zx_spectrum::DEFAULT_AY_WATCH_CAP,
            "no truncated observation"
        );
        fields.push(FieldWrites {
            field,
            writes: records.to_vec(),
        });
        session
            .machine_mut()
            .machine_mut()
            .clear_ay_write_watch_records();
    }
    let audio = session.audio_wav_bytes().expect("normal WAV");
    let audio_hash = hash_xxh64(&audio);
    let expected =
        std::env::var("EMU198X_AUDIO_AUDIT_EXPECT").expect("independent normal-capture hash");

    let audit = Audit {
        id,
        boot_hash,
        audio_hash: audio_hash.clone(),
        start_time,
        end_time: session.time().get(),
        fields,
    };
    std::fs::write(
        output.join("after-ay.toml"),
        toml::to_string(&session.machine().machine().ay).expect("AY state"),
    )
    .expect("after state");
    std::fs::write(
        output.join("audit.toml"),
        toml::to_string(&audit).expect("audit"),
    )
    .expect("audit file");
    std::fs::write(output.join("audio.wav"), audio).expect("audio evidence");
    assert_eq!(audio_hash, expected, "predicted ordinary capture");
}

#[test]
#[ignore = "PRIVATE PROBE: original ROMs"]
fn observe_amstrad_boot_time() {
    let firmware_root =
        PathBuf::from(std::env::var_os("HOME").expect("HOME")).join(".emu198x/roms");
    let manifest = load_manifest(std::path::Path::new("manifest/spectrum.toml")).expect("manifest");
    let files = lookup_firmware(&manifest, "plus2a").expect("firmware map");
    let roms: Vec<_> = files
        .iter()
        .map(|file| read_firmware_bytes(&firmware_root, file).expect("ROM"))
        .collect();
    let mut session = HeadlessSession::new_with_query_provider(
        build_plus2a_runtime(&roms[0], &roms[1], &roms[2], &roms[3]),
        u64::from(TIMING_PLUS2A.halfcycles_per_frame),
        SpectrumSessionQueryProvider,
    );
    prepare_session_no_media(&mut session).expect("prepare");
    let boot = session
        .wait_for_boot(DEFAULT_128K_BOOT_FRAMES)
        .expect("boot");
    eprintln!("AUDIT_BOOT {} {}", boot.frames, session.time().get());
}
