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
