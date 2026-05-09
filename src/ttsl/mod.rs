use nalgebra_glm::{Vec2, Vec3, Vec4};
pub mod opcodes;
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

#[derive(Clone)]
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

pub fn decode_instrs_256(bytes: &[u8]) -> [Instr; 256] {
    let mut instrs: Vec<Instr> = Vec::new();
    let mut i = 0;
    while i + 6 <= bytes.len() && instrs.len() < 256 {
        instrs.push(Instr::from_bytes(&bytes[i..i + 6]));
        i += 6;
    }

    while instrs.len() < 256 {
        instrs.push(Instr {
            opcode: OP_RET,
            dst: 0,
            a: 0,
            b: 0,
            c: 0,
            d: 0,
        });
    }
    instrs.try_into().unwrap()
}

pub fn run_ttsl(instrs: &[Instr; 256], regs: &mut Registers) -> (Vec3, Vec3, i32) {
    let mut ip: usize = 0;
    loop {
        let instr = unsafe { instrs.get_unchecked(ip) };

        if let Some(r) = exec_opcode(
            instr.opcode,
            instr.dst,
            instr.a,
            instr.b,
            instr.c,
            instr.d,
            regs,
            &mut ip,
        ) {
            return r;
        }
        ip += 1;
    }
}

#[cfg(test)]
struct TTPU {
    pub regs: Registers,
}

#[cfg(test)]
impl TTPU {
    pub fn new() -> Self {
        TTPU {
            regs: Registers::new(),
        }
    }

    fn run(&mut self, bytecode: &[Instr; 256]) -> (Vec3, Vec3, i32) {
        run_ttsl(bytecode, &mut self.regs)
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

        let bytecode_array = decode_instrs_256(&[
            ADD_V3, 2, 0, 1, 0, 0, //
            OP_RET, 0, 3, 2, 0, 0,
        ]);
        ttsl.regs.f32_[0] = 1.5;
        ttsl.regs.f32_[1] = 2.5;

        let result = ttsl.run(&bytecode_array);
        assert_eq!(result, (Vec3::zeros(), Vec3::new(4.0, 6.0, 8.0), 0));
        dbg!(result);
    }

    #[test]
    fn test_run_ttsl_matches_ttpu_path() {
        let mut ttpu = TTPU::new();
        ttpu.regs.v3[3] = Vec3::new(0.25, 0.5, 1.0);
        ttpu.regs.i32_[7] = 42;

        let instrs = decode_instrs_256(&[
            OP_RET, 0, 3, 3, 7, 0, //
            OP_RET, 0, 0, 0, 0, 0,
        ]);

        let expected = ttpu.run(&instrs);
        let actual = run_ttsl(&instrs, &mut ttpu.regs);

        assert_eq!(actual, expected);
    }

    #[test]
    fn test_decode_instrs_256_pads_with_ret() {
        let instrs = decode_instrs_256(&[OP_RET, 0, 4, 5, 6, 0]);
        assert_eq!(instrs[0].opcode, OP_RET);
        assert_eq!(instrs[0].a, 4);
        assert_eq!(instrs[0].b, 5);
        assert_eq!(instrs[0].c, 6);
        assert_eq!(instrs[255].opcode, OP_RET);
    }
}
