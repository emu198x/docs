use machine_oric_atmos::{OricAtmos, OricModel};
use std::{env, fs};

#[derive(Default)]
struct Trace {
    motor_seen: bool,
    motor_stopped: bool,
    motor_clocks: u64,
    pb7_edges: usize,
    cb2_edges: usize,
    timer_output_clocks: u64,
    last: Option<(bool, bool, bool)>,
}
impl Trace {
    fn step(&mut self, sys: &mut OricAtmos) {
        let clocks = sys.step_instruction();
        let via = sys.via();
        let motor = via.orb() & via.peek(2) & 0x40 != 0;
        let pb7 = via.cb2_out; // Deliberately sample the incorrect ticket pin.
        let cb2 = via.cb2_out;
        if motor {
            self.motor_seen = true;
            self.motor_clocks += clocks;
            if via.peek(0x0b) & 0x80 != 0 {
                self.timer_output_clocks += clocks;
            }
            if let Some((true, prev_pb7, prev_cb2)) = self.last {
                self.pb7_edges += usize::from(pb7 != prev_pb7);
                self.cb2_edges += usize::from(cb2 != prev_cb2);
            }
        } else if self.motor_seen {
            self.motor_stopped = true;
        }
        self.last = Some((motor, pb7, cb2));
    }
    fn clocks(&mut self, sys: &mut OricAtmos, count: u64) {
        let end = sys.cpu_cycles() + count;
        while sys.cpu_cycles() < end {
            self.step(sys);
        }
    }
}
fn main() {
    let rom_path = env::args().nth(1).expect("ROM path");
    let rom = fs::read(rom_path).expect("read actual ROM");
    assert_eq!(rom.len(), 16384);
    let mut sys = OricAtmos::new(rom, OricModel::Atmos);
    for _ in 0..200 { sys.run_frame(); }
    let mut trace = Trace::default();
    // Type CSAVE"X" using the real keyboard matrix. No ROM trap or register injection.
    for (col,row,shift) in [(2,7,false),(6,6,false),(6,5,false),(0,3,false),(6,3,false),(2,6,true),(0,6,false),(2,6,true),(7,5,false)] {
        if shift { sys.press_key(4,4); }
        sys.press_key(col,row);
        trace.clocks(&mut sys, 4*19968);
        sys.release_key(col,row);
        if shift { sys.release_key(4,4); }
        trace.clocks(&mut sys, 4*19968);
    }
    trace.clocks(&mut sys, 8_000_000);
    println!("motor_seen={} motor_stopped={} motor_clocks={} timer_output_clocks={} pb7_edges={} cb2_edges={}", trace.motor_seen, trace.motor_stopped, trace.motor_clocks, trace.timer_output_clocks, trace.pb7_edges, trace.cb2_edges);
    for row in 0..28u16 {
        let line: String = (0..40u16).map(|col| char::from(sys.peek(0xbb80+row*40+col)&0x7f)).map(|ch| if ch.is_ascii_graphic() || ch==' ' { ch } else { ' ' }).collect();
        if !line.trim().is_empty() { println!("screen[{row}]={line}"); }
    }
    assert!(trace.motor_seen && trace.motor_stopped, "ROM must complete a recording");
    assert!(trace.pb7_edges > 1000, "recording must contain a substantial PB7 waveform");
    assert!(trace.timer_output_clocks > trace.motor_clocks / 2, "timer 1 must drive recording output");
    assert_eq!(trace.cb2_edges, 0, "CB2 is not the tape output");
}
