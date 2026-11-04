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
