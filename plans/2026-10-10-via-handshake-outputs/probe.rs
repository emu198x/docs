use mos_via_6522::Via6522;

fn main() {
    let mut mismatches = 0;
    let mut observations = 0;
    for (port, handshake, pulse, register) in [("A", 0x08, 0x0a, 1), ("B", 0x80, 0xa0, 0)] {
        for mode in [handshake, pulse] {
            for access in ["read", "write", "override_read"] {
                let mut via = Via6522::new();
                via.write(0x0c, mode);
                match access {
                    "read" => { let _ = via.read(register); }
                    "write" => via.write(register, 0x55),
                    _ if port == "A" => { let _ = via.read_port_a_with_value(0x55); }
                    _ => { let _ = via.read_port_b_with_value(0x55); }
                }
                let actual = if port == "A" { via.ca2_out } else { via.cb2_out };
                let expected = port == "B" && access != "write";
                println!("port={port} pcr={mode:02x} access={access} output_high={actual} expected_high={expected}");
                mismatches += usize::from(actual != expected);
                observations += 1;
                if mode == handshake {
                    if port == "A" { via.set_ca1_level(false); } else { via.set_cb1_level(false); }
                    let actual = if port == "A" { via.ca2_out } else { via.cb2_out };
                    println!("port={port} pcr={mode:02x} access={access} after_active_edge_high={actual} expected_high=true");
                    mismatches += usize::from(!actual);
                    observations += 1;
                }
            }
        }
    }
    println!("{mismatches} mismatches in {observations} observations");
    std::process::exit(i32::from(mismatches != 0));
}
