use std::collections::HashMap;
use std::sync::{Arc, Mutex, OnceLock};

use pyo3::{exceptions::PyValueError, prelude::*, types::PyDict};

use crate::utils::{from_pydict_int_v2, from_pydict_int_v3, from_pydict_int_v4, vec4_to_pyglm};
use tt3de_core::ttsl::jit::{compile_ttsl_json, CompiledShader};
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

fn compiled_shader(ssa_json: &str) -> PyResult<Arc<CompiledShader>> {
    static CACHE: OnceLock<Mutex<HashMap<String, Arc<CompiledShader>>>> = OnceLock::new();
    let cache = CACHE.get_or_init(|| Mutex::new(HashMap::new()));
    let mut map = cache
        .lock()
        .map_err(|_| PyValueError::new_err("TTSL JIT cache lock poisoned"))?;
    if let Some(compiled) = map.get(ssa_json) {
        return Ok(Arc::clone(compiled));
    }
    let compiled = Arc::new(
        compile_ttsl_json(ssa_json)
            .map_err(|err| PyValueError::new_err(format!("TTSL JIT: {err}")))?,
    );
    map.insert(ssa_json.to_string(), Arc::clone(&compiled));
    Ok(compiled)
}

/// Execute a compiled TTSL shader (Cranelift) against seeded register banks.
#[pyfunction]
pub fn ttsl_run(
    py: Python,
    regbool: Py<PyDict>,
    regf32: Py<PyDict>,
    regi32: Py<PyDict>,
    regv2: Py<PyDict>,
    regv3: Py<PyDict>,
    regv4: Py<PyDict>,
    ssa_json: &str,
) -> PyResult<(Py<PyAny>, Py<PyAny>, i32)> {
    let mut regs = Registers::new();
    convert_and_fill_register(&mut regs, regbool, regf32, regi32, regv2, regv3, regv4, py);

    let compiled = compiled_shader(ssa_json)?;
    let (v4a, v4b, iret) = compiled.run(&mut regs, None);
    Ok((vec4_to_pyglm(py, v4a), vec4_to_pyglm(py, v4b), iret))
}
