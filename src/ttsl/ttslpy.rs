use std::{collections::HashMap, hash::Hash};

use nalgebra_glm::{Vec2, Vec3, Vec4};
use pyo3::{
    prelude::*,
    types::{PyByteArray, PyBytes, PyDict, PyDictMethods, PyList, PyTuple},
};


use crate::{
    ttsl::{opcodes::OP_RET, Instr, Registers, TTPU},
    utils::{from_pydict_int_v2, from_pydict_int_v3, from_pydict_int_v4, vec3_to_pyglm},
};

pub fn convert_and_fill_register(
    regs: &mut Registers,
    regbool: Py<PyDict>,
    regf32: Py<PyDict>,
    regi32: Py<PyDict>,
    regv2: Py<PyDict>,
    regv3: Py<PyDict>,
    regv4: Py<PyDict>,
    py: Python,
) {
    let mapf32: HashMap<i64, f32> = regf32.extract(py).unwrap();
    for (key_, value) in mapf32.iter() {
        regs.f32_[*key_ as usize] = *value;
    }
    let mapi32: HashMap<i64, i32> = regi32.extract(py).unwrap();
    for (key_, value) in mapi32.iter() {
        regs.i32_[*key_ as usize] = *value;
    }
    let mapbool: HashMap<i64, bool> = regbool.extract(py).unwrap();
    for (key_, value) in mapbool.iter() {
        regs.bool_[*key_ as usize] = *value;
    }

    // load registers from regsetup
    let vec2_set = from_pydict_int_v2(py, regv2.bind(py));
    let vec3_set = from_pydict_int_v3(py, regv3.bind(py));
    let vec4_set = from_pydict_int_v4(py, regv4.bind(py));

    for (key_, value) in vec2_set.iter() {
        regs.v2[*key_ as usize] = *value;
    }
    for (key_, value) in vec3_set.iter() {
        regs.v3[*key_ as usize] = *value;
    }
    for (key_, value) in vec4_set.iter() {
        regs.v4[*key_ as usize] = *value;
    }
}

pub fn to_instrs(bytes: &[u8]) -> [Instr; 256] {
    let mut instrs: Vec<Instr> = Vec::new();
    let mut i = 0;
    while i + 6 <= bytes.len() && instrs.len() < 256 {
        let instr_bytes = &bytes[i..i + 6];
        let instr = Instr::from_bytes(instr_bytes);
        instrs.push(instr);
        i += 6;
    }
    // fill the rest with NOPs
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

#[pyfunction]
pub fn ttsl_run(
    py: Python,
    regbool: Py<PyDict>,
    regf32: Py<PyDict>,
    regi32: Py<PyDict>,
    regv2: Py<PyDict>,
    regv3: Py<PyDict>,
    regv4: Py<PyDict>,
    bytecode: Py<PyBytes>, // the bytes drirectly from python.
) -> (Py<PyAny>, Py<PyAny>, i32) {
    // setup TTPU
    let mut ttpu = TTPU::new();
    let regs = &mut ttpu.regs;
    // load regsetup into regs
    convert_and_fill_register(regs, regbool, regf32, regi32, regv2, regv3, regv4, py);

    // load bytes &[u8] from bytecode
    let bytes: &[u8] = bytecode.extract(py).unwrap();
    let instrs = to_instrs(bytes);

    let (v3a, v3b, iret) = ttpu.run(&instrs);
    let a = vec3_to_pyglm(py, v3a);
    let b = vec3_to_pyglm(py, v3b);
    let c = iret;
    return (a, b, c);
}
