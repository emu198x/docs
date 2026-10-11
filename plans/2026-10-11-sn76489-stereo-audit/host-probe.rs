use emu198x_shell::{AudioPacket, AudioSink, HostIo, MachineCore, MachineError, MachineTime, NullFrameSink, NullTraceSink};
use runtime_sega_game_gear::{Model, with_cartridge};
#[derive(Default)]
struct Capture { channels: Vec<u8>, samples: Vec<f32> }
impl AudioSink for Capture {
    fn push_audio(&mut self, p: AudioPacket<'_>) -> Result<(), MachineError> {
        assert_eq!(p.sample_rate, 48_000);
        assert!(!p.samples.is_empty());
        self.channels.push(p.channels);
        self.samples.extend_from_slice(p.samples);
        Ok(())
    }
}
fn run(mask: u8) -> Capture {
    let program = [
        0x3E, mask, 0xD3, 0x06, // LD A,mask; OUT (06),A
        0x3E, 0x87, 0xD3, 0x7F, // tone 0 period low
        0x3E, 0x00, 0xD3, 0x7F, // period high
        0x3E, 0x90, 0xD3, 0x7F, // tone 0 full volume
        0x76, // HALT; PSG keeps running
    ];
    let mut rom = vec![0; 32768];
    rom[..program.len()].copy_from_slice(&program);
    let mut runtime = with_cartridge(Model::GameGear, rom);
    let mut capture = Capture::default();
    runtime.run_until(MachineTime::new(150_000), &mut HostIo {
        input_events: &[], frame_sink: &mut NullFrameSink,
        audio_sink: &mut capture, trace_sink: &mut NullTraceSink,
    }).expect("synthetic guest runs");
    let cpu = runtime.machine().expect("loaded machine").cpu();
    assert!(cpu.halt, "guest must execute all writes and reach HALT");
    assert_eq!(cpu.regs.pc, 17, "guest reaches the byte after HALT");
    assert!(!capture.channels.is_empty());
    assert!(capture.samples.iter().all(|v| v.is_finite()));
    capture
}
fn main() {
    let enabled = run(0xFF);
    assert!(enabled.samples.iter().any(|v| *v != 0.0));
    let muted = run(0x00);
    let left = run(0x10);
    println!("Game Gear packet channels: {:?}", enabled.channels);
    println!("all-enabled samples: {}, nonzero: {}", enabled.samples.len(), enabled.samples.iter().filter(|v| **v != 0.0).count());
    println!("muted output identical to enabled: {}", muted.samples == enabled.samples);
    println!("left-only output identical to enabled: {}", left.samples == enabled.samples);
    assert!(enabled.channels.iter().all(|c| *c == 2), "Game Gear reaches host as mono");
    assert!(muted.samples.iter().all(|v| *v == 0.0));
    assert!(left.samples.chunks_exact(2).all(|s| s[1] == 0.0));
}
