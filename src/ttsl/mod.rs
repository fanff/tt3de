use nalgebra_glm::{Vec2, Vec3, Vec4};
mod opcodes;
use opcodes::*;
pub mod ttslpy;

#[derive(Clone, Debug)]
pub struct Instr {
    pub opcode: u8,
    pub dst: u8,
    pub a: u8,
    pub b: u8,
    pub c: u8,
    pub d: u8,
}

impl Instr {
    pub fn from_bytes(bytes: &[u8]) -> Self {
        Instr {
            opcode: bytes[0],
            dst: bytes[1],
            a: bytes[2],
            b: bytes[3],
            c: bytes[4],
            d: bytes[5],
        }
    }
}

pub struct Registers {
    pub bool_: [bool; 256],
    pub i32_: [i32; 256],
    pub f32_: [f32; 256],
    pub v2: [Vec2; 256],
    pub v3: [Vec3; 256],
    pub v4: [Vec4; 256],
}

impl Registers {
    pub fn new() -> Self {
        Registers {
            bool_: [false; 256],
            i32_: [0; 256],
            f32_: [0.0; 256],
            v2: [Vec2::zeros(); 256],
            v3: [Vec3::zeros(); 256],
            v4: [Vec4::zeros(); 256],
        }
    }
}

struct TTPU {
    pub regs: Registers,
}

impl TTPU {
    pub fn new() -> Self {
        TTPU {
            regs: Registers::new(),
        }
    }

    fn run(&mut self, bytecode: &[Instr; 256]) -> (Vec3, Vec3, i32) {
        let mut ip: usize = 0;
        loop {
            let instr = unsafe { bytecode.get_unchecked(ip) };

            if let Some(r) = exec_opcode(
                instr.opcode,
                instr.dst,
                instr.a,
                instr.b,
                instr.c,
                instr.d,
                &mut self.regs,
                &mut ip,
            ) {
                return r;
            }
            ip += 1;
        }
    }
}

#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn test_ttsl_add_f32() {
        let mut ttsl = TTPU::new();
        ttsl.regs.f32_[0] = 1.5;
        ttsl.regs.f32_[1] = 2.5;
        ttsl.regs.v3[0] = Vec3::new(1.0, 2.0, 3.0);
        ttsl.regs.v3[1] = Vec3::new(3.0, 4.0, 5.0);

        let bytecode = [
            Instr::from_bytes(&[ADD_V3, 2, 0, 1, 0, 0]), //
            Instr::from_bytes(&[OP_RET, 0, 3, 2, 0, 0]), // return v3[2]
        ];

        // expand the bytecode to 256 instructions, filling the rest with NOPs,
        // but Instr has no "copy" trait, so we need to do it
        // with a loop ono a vec
        let mut uninit_rest: Vec<Instr> = Vec::with_capacity(256 - bytecode.len());
        for i in 0..(256 - bytecode.len()) {
            uninit_rest.push(Instr {
                opcode: OP_RET,
                dst: 0,
                a: 0,
                b: 0,
                c: 0,
                d: 0,
            });
        }
        let mut full_bytecode: Vec<Instr> = Vec::with_capacity(256);
        full_bytecode.extend_from_slice(&bytecode);
        full_bytecode.extend_from_slice(&uninit_rest);
        let bytecode_array: [Instr; 256] = full_bytecode.try_into().unwrap();
        ttsl.regs.f32_[0] = 1.5;
        ttsl.regs.f32_[1] = 2.5;

        let result = ttsl.run(&bytecode_array);
        assert_eq!(result, (Vec3::zeros(), Vec3::new(4.0, 6.0, 8.0), 0));
        dbg!(result);
    }
}
