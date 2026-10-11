use emu198x_shell::{
    AudioPacket, AudioSink, HostIo, MachineCore, MachineError, MachineTime, NullFrameSink,
    NullTraceSink,
};
use machine_atari_7800::{Atari7800, Atari7800Region};
use runtime_atari_7800::{Atari7800Runtime, Model};

#[derive(Default)]
struct Sink {
    samples: Vec<f32>,
    packets: usize,
    rate: Option<u32>,
}
impl AudioSink for Sink {
    fn push_audio(&mut self, packet: AudioPacket<'_>) -> Result<(), MachineError> {
        assert_eq!(packet.channels, 1);
        assert!(!packet.samples.is_empty());
        assert!(packet.samples.iter().all(|sample| sample.is_finite()));
        if let Some(rate) = self.rate {
            assert_eq!(packet.sample_rate, rate);
        }
        self.rate = Some(packet.sample_rate);
        self.samples.extend_from_slice(packet.samples);
        self.packets += 1;
        Ok(())
    }
}

fn cartridge(version: u8, selector: u8, base: u16, tia: bool, pokey: bool) -> Vec<u8> {
    let mut program = vec![0x78]; // SEI, then real CPU writes to both chips.
    for (address, value) in [
        (base + 15, 3),
        (base + 8, 0),
        (base, 7),
        (base + 1, if pokey { 0xaf } else { 0xa0 }),
        (base + 9, 0),
        (0x15, 4),
        (0x17, 15),
        (0x19, if tia { 8 } else { 0 }),
        (0x1800, 0x5a),
    ] {
        program.extend_from_slice(&[0xa9, value, 0x8d, address as u8, (address >> 8) as u8]);
    }
    let loop_address = 0x8000 + program.len() as u16;
    program.extend_from_slice(&[0x4c, loop_address as u8, (loop_address >> 8) as u8]);
    let mut rom = vec![0xea; 32768];
    rom[..program.len()].copy_from_slice(&program);
    for vector in [0x7ffa, 0x7ffc, 0x7ffe] {
        rom[vector..vector + 2].copy_from_slice(&[0x00, 0x80]);
    }
    let mut image = vec![0; 128];
    image[0] = version;
    image[1..10].copy_from_slice(b"ATARI7800");
    image[49..53].copy_from_slice(&(rom.len() as u32).to_be_bytes());
    if version == 4 {
        image[67] = selector;
    } else {
        let flags: u16 = match selector {
            1 => 0x0400,
            2 => 0x0040,
            4 => 0x8000,
            5 => 0x0001,
            _ => panic!("unsupported test selector"),
        };
        image[53..55].copy_from_slice(&flags.to_be_bytes());
    }
    image.extend_from_slice(&rom);
    image
}

#[test]
fn cartridge_pokey_reaches_the_host_audio_sink() {
    let mut cases = 0;
    let mut host_failures = 0;
    let mut queued_cases = 0;
    for model in Model::ALL {
        for version in [3, 4] {
            for (selector, base) in [(1, 0x0440), (2, 0x0450), (4, 0x0800), (5, 0x4000)] {
                let mut captured = Vec::new();
                for mode in 0..4 {
                    let tia = mode & 1 != 0;
                    let pokey = mode & 2 != 0;
                    let image = cartridge(version, selector, base, tia, pokey);
                    let region = match model {
                        Model::A7800Ntsc => Atari7800Region::Ntsc,
                        Model::A7800Pal => Atari7800Region::Pal,
                    };
                    // Independent chip-output control: the host is allowed to
                    // consume its own queue completely once the fault is fixed.
                    let mut direct = Atari7800::new(image.clone(), region).expect("direct machine");
                    for _ in 0..4 {
                        direct.run_frame();
                    }
                    let chip_samples = direct.take_pokey_audio_samples();
                    assert!(!chip_samples.is_empty(), "chip generated samples");
                    assert_eq!(chip_samples.iter().any(|value| *value != 0.0), pokey);
                    let mut runtime =
                        Atari7800Runtime::new(model, image).expect("synthetic POKEY cart");
                    let mut sink = Sink::default();
                    runtime
                        .run_until(
                            MachineTime::new(model.frame_ticks() * 4),
                            &mut HostIo {
                                input_events: &[],
                                frame_sink: &mut NullFrameSink,
                                audio_sink: &mut sink,
                                trace_sink: &mut NullTraceSink,
                            },
                        )
                        .expect("four frames");
                    assert_eq!(sink.packets, 4, "complete host output");
                    let machine = runtime.machine_mut().expect("machine");
                    assert_eq!(
                        machine.peek(0x1800),
                        0x5a,
                        "guest completed register writes"
                    );
                    let queued = machine.take_pokey_audio_samples();
                    queued_cases += usize::from(!queued.is_empty());
                    let audible = sink.samples.iter().any(|value| *value != 0.0);
                    eprintln!(
                        "model={model:?} header={version} base={base:04x} mode={mode} host_samples={} rate={:?} host_audible={audible} queued_pokey={} chip_audible={pokey}",
                        sink.samples.len(),
                        sink.rate,
                        queued.len()
                    );
                    captured.push(sink.samples);
                    cases += 1;
                }
                assert!(
                    captured[0].iter().all(|value| *value == 0.0),
                    "silent control"
                );
                assert!(
                    captured[1].iter().any(|value| *value != 0.0),
                    "TIA positive control"
                );
                host_failures += usize::from(captured[2].iter().all(|value| *value == 0.0));
                host_failures += usize::from(captured[3] == captured[1]);
            }
        }
    }
    eprintln!("cases={cases} host_failures={host_failures} undrained_chip_cases={queued_cases}");
    assert_eq!(cases, 64, "complete header/region/location/audio inventory");
    assert_eq!(
        host_failures, 0,
        "cartridge POKEY must contribute to host audio"
    );
    assert_eq!(
        queued_cases, 0,
        "host delivery must consume the POKEY queue"
    );
}
