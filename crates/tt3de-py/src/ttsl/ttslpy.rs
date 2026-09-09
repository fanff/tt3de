use std::collections::HashMap;

use pyo3::{prelude::*, types::PyDict};

use crate::utils::{from_pydict_int_v2, from_pydict_int_v3, from_pydict_int_v4};
use tt3de_core::ttsl::Registers;

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
