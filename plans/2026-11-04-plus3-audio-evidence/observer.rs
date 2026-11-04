use super::*;
use serde::Serialize;
use std::path::PathBuf;

#[derive(Serialize)]
struct FieldWrites {
    field: u32,
    time: u64,
    pc: u16,
    registers: Vec<u8>,
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
    assert_eq!(entry.variant, "plus3");
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
        build_plus3_runtime(&roms[0], &roms[1], &roms[2], &roms[3]),
        u64::from(TIMING_PLUS2A.halfcycles_per_frame),
        SpectrumSessionQueryProvider,
    );
    let media = entry.media.as_ref().expect("media");
    let kind = load_media_spec(&mut session, media, &media_root).expect("mount media");
    assert!(matches!(kind, MediaKind::Disk));
    eprintln!("AY_BOOT_WATCH_START {}", session.time().get());
    session.machine_mut().machine_mut().start_ay_write_watch();
    autoload_plus3_loader(&mut session, DEFAULT_128K_BOOT_FRAMES).expect("ordinary disk loader");
    eprintln!("AUDIT_DISK_START {}", session.time().get());
    let (boot_hash, _) =
        run_script_then_capture_boot_frame(&mut session, entry).expect("ordinary waypoint");
    assert_eq!(boot_hash, entry.boot.frame_hash, "unchanged visual anchor");
    session
        .run_frames(entry.audio.from_frame)
        .expect("ordinary gap");
    session.clear_audio_capture();
    let physical_ram: Vec<u8> = (0..8)
        .flat_map(|bank| {
            session
                .machine()
                .machine()
                .memory
                .ram_bank(bank)
                .iter()
                .copied()
        })
        .collect();
    assert_eq!(physical_ram.len(), 131072);
    std::fs::write(output.join("before.ram"), physical_ram).expect("physical RAM");
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
            time: session.time().get(),
            pc: session.machine().machine().z80.regs.pc,
            registers: session.machine().machine().ay.registers().to_vec(),
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
    let physical_ram: Vec<u8> = (0..8)
        .flat_map(|bank| {
            session
                .machine()
                .machine()
                .memory
                .ram_bank(bank)
                .iter()
                .copied()
        })
        .collect();
    assert_eq!(physical_ram.len(), 131072);
    std::fs::write(output.join("after.ram"), physical_ram).expect("physical RAM");
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
    let mut continuation = Vec::new();
    for field in 100..500 {
        eprintln!("AY_FIELD {field}");
        session.run_frames(1).expect("native continuation field");
        let records = session
            .machine()
            .machine()
            .ay_write_watch_records()
            .expect("armed watch");
        assert!(records.len() < common_sinclair_zx_spectrum::DEFAULT_AY_WATCH_CAP);
        continuation.push(FieldWrites {
            field,
            time: session.time().get(),
            pc: session.machine().machine().z80.regs.pc,
            registers: session.machine().machine().ay.registers().to_vec(),
            writes: records.to_vec(),
        });
        session
            .machine_mut()
            .machine_mut()
            .clear_ay_write_watch_records();
    }
    std::fs::write(
        output.join("continuation.toml"),
        toml::to_string(
            &continuation
                .iter()
                .map(|f| (format!("field_{}", f.field), f))
                .collect::<std::collections::BTreeMap<_, _>>(),
        )
        .expect("continuation TOML"),
    )
    .expect("continuation file");
}

#[derive(serde::Deserialize)]
struct Edge {
    field: u32,
    hc: u32,
    register: u8,
    value: u8,
}
#[derive(serde::Deserialize)]
struct Edges {
    edge: Vec<Edge>,
}

#[test]
#[ignore = "PRIVATE: observed AY states and bounded timed writes"]
fn replay_saved_ay() {
    let root = PathBuf::from(std::env::var_os("EMU198X_AUDIO_AUDIT_ROOT").expect("root"));
    let label = std::env::var("EMU198X_AUDIO_REPLAY_LABEL").expect("producer label");
    for source in ["original", "current"] {
        for id in [
            "chase-hq-plus3",
            "starglider-2-plus3",
            "lotus-esprit-plus3",
            "robocop-plus3",
            "where-time-stood-still-plus3",
        ] {
            let directory = root.join("observations").join(source).join(id);
            let mut machine = SpectrumPlus3::new();
            machine.ay = toml::from_str(
                &std::fs::read_to_string(directory.join("before-ay.toml")).expect("AY state"),
            )
            .expect("deserialize AY");
            let edges: Edges = toml::from_str(
                &std::fs::read_to_string(directory.join("edges.toml")).expect("edges"),
            )
            .expect("edge schedule");
            assert!(!edges.edge.is_empty());
            assert!(
                edges
                    .edge
                    .windows(2)
                    .all(|w| (w[0].field, w[0].hc) <= (w[1].field, w[1].hc))
            );
            assert!(edges.edge.iter().all(|e| e.field < 100 && e.hc < 354540));
            let mut next = 0;
            let mut samples = Vec::new();
            for field in 0..100 {
                // Offline replay of observed timestamps, not an alternative machine run loop.
                // SpectrumDriver handles CPU/bus before AY at master-clock phase 2 modulo 10.
                for hc in 0..354540 {
                    while next < edges.edge.len()
                        && (edges.edge[next].field, edges.edge[next].hc) == (field, hc)
                    {
                        let edge = &edges.edge[next];
                        machine.ay.select_register(edge.register);
                        machine.ay.write_data(edge.value);
                        next += 1;
                    }
                    if hc % 10 == 2 {
                        machine.ay.tick();
                    }
                }
                let mut frame = [0.0f32; 882];
                machine.ay.end_frame(&mut frame);
                samples.extend(frame.into_iter().flat_map(|v| v.to_le_bytes()));
            }
            assert_eq!(next, edges.edge.len());
            assert_eq!(samples.len(), 88200 * 4);
            std::fs::write(directory.join(format!("replay-{label}.f32")), samples)
                .expect("replayed samples");
            eprintln!("AY_REPLAY {label} {source} {id} {}", next);
        }
    }
}

#[derive(serde::Deserialize)]
struct BeeperEdge {
    field: u32,
    hc: u32,
    value: u8,
}
#[derive(serde::Deserialize)]
struct BeeperEdges {
    start_field: u32,
    edge: Vec<BeeperEdge>,
}

#[test]
#[ignore = "PRIVATE: complete observed speaker transitions from reset"]
fn replay_saved_beeper() {
    let root = PathBuf::from(std::env::var_os("EMU198X_AUDIO_AUDIT_ROOT").expect("root"));
    let label = std::env::var("EMU198X_AUDIO_REPLAY_LABEL").expect("producer label");
    for source in ["original", "current"] {
        for id in ["chase-hq-plus3", "where-time-stood-still-plus3"] {
            let directory = root.join("fe-control/observations").join(source).join(id);
            let edges: BeeperEdges = toml::from_str(
                &std::fs::read_to_string(directory.join("beeper.toml")).expect("beeper edges"),
            )
            .expect("speaker schedule");
            assert!(!edges.edge.is_empty());
            assert!((6190..=6191).contains(&edges.start_field));
            assert!(
                edges
                    .edge
                    .windows(2)
                    .all(|w| (w[0].field, w[0].hc) <= (w[1].field, w[1].hc))
            );
            let mut machine = SpectrumPlus3::new();
            let mut next = 0;
            let mut samples = Vec::new();
            for field in 0..edges.start_field + 100 {
                while next < edges.edge.len() && edges.edge[next].field == field {
                    let edge = &edges.edge[next];
                    assert!(edge.hc < 354540 && edge.value <= 1);
                    machine
                        .audio
                        .set_level(edge.hc / 5, if edge.value == 1 { 0.8 } else { 0.0 });
                    next += 1;
                }
                let mut frame = [0.0f32; 882];
                machine.audio.end_frame(&mut frame);
                if field >= edges.start_field {
                    samples.extend(frame.into_iter().flat_map(|v| v.to_le_bytes()));
                }
            }
            assert_eq!(next, edges.edge.len());
            assert_eq!(samples.len(), 88200 * 4);
            std::fs::write(
                directory.join(format!("beeper-replay-{label}.f32")),
                samples,
            )
            .expect("speaker samples");
            eprintln!("BEEPER_REPLAY {label} {source} {id} {next}");
        }
    }
}
