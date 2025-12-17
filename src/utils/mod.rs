use std::collections::HashMap;

use nalgebra_glm::{Mat4, Vec2, Vec3, Vec4};
use once_cell::sync::OnceCell;
use pyo3::{
    types::{PyAnyMethods, PyDict, PyDictMethods, PyList, PyTuple, PyTupleMethods},
    Bound, Py, PyAny, PyResult, Python,
};

use super::texturebuffer::RGBA;

// caching the glm.vec2, vec3, vec4 constructors
static GLM_VEC2: OnceCell<Py<PyAny>> = OnceCell::new();
static GLM_VEC3: OnceCell<Py<PyAny>> = OnceCell::new();
static GLM_VEC4: OnceCell<Py<PyAny>> = OnceCell::new();

fn get_glm_vec2(py: Python<'_>) -> PyResult<&Py<PyAny>> {
    GLM_VEC2.get_or_try_init(|| {
        let pyglm = py.import("pyglm")?;
        let glm = pyglm.getattr("glm")?;
        let vec2 = glm.getattr("vec2")?;
        Ok(vec2.into())
    })
}

fn get_glm_vec3(py: Python<'_>) -> PyResult<&Py<PyAny>> {
    GLM_VEC3.get_or_try_init(|| {
        let pyglm = py.import("pyglm")?;
        let glm = pyglm.getattr("glm")?;
        let vec3 = glm.getattr("vec3")?;
        Ok(vec3.into())
    })
}
fn get_glm_vec4(py: Python<'_>) -> PyResult<&Py<PyAny>> {
    GLM_VEC4.get_or_try_init(|| {
        let pyglm = py.import("pyglm")?;
        let glm = pyglm.getattr("glm")?;
        let vec4 = glm.getattr("vec4")?;
        Ok(vec4.into())
    })
}

// convert PyAny glm.mat4 to nalgebra_glm::Mat4

pub fn convert_pymat4(py: Python, glm_mat4: &Py<PyAny>) -> Mat4 {
    let tuple = glm_mat4.call_method0(py, "to_tuple").unwrap();
    let r: &Bound<PyTuple> = tuple.bind(py).cast().unwrap();
    //let outer_tuple: &PyTuple = r.extract().unwrap();

    // Create an iterator over the nested tuples
    let nested_tuples_iter = r.iter().map(|item| {
        // Extract each inner tuple
        let inner_tuple: (f32, f32, f32, f32) = item.extract().unwrap();
        inner_tuple
    });

    // Flatten the nested tuples into an iterator of floats
    let flat_iter = nested_tuples_iter.flat_map(|(a, b, c, d)| vec![a, b, c, d]);

    Mat4::from_iterator(flat_iter)
}

pub fn mat4_to_slicelist(py: Python, mat4: Mat4) -> Py<PyAny> {
    let s = mat4.as_slice();
    let list = PyList::new(py, s).unwrap();
    list.into()
}
pub fn mat4_to_pyglm(py: Python, mat4: Mat4) -> Py<PyAny> {
    let list_of_values = mat4.as_slice();

    // convert the list of values into a IntoPy<Py<PyTuple>>
    let tupl = PyTuple::new(py, list_of_values).unwrap();

    // build and return a "glm.mat4(*list_of_values)" from the slice
    let glm_module = py.import("glm").unwrap();
    let mat4_class = glm_module.getattr("mat4").unwrap();
    let glm_mat4_instance = mat4_class.call1(tupl).unwrap();

    glm_mat4_instance.into()
}

// convert Vec2, Vec3, Vec4 to Pyglm objects
pub fn vec3_to_pyglm(py: Python<'_>, vec3: Vec3) -> Py<PyAny> {
    let ctor = get_glm_vec3(py).unwrap();
    ctor.call1(py, (vec3.x, vec3.y, vec3.z)).unwrap()
}

pub fn vec2_to_pyglm(py: Python<'_>, vec2: Vec2) -> Py<PyAny> {
    let ctor = get_glm_vec2(py).unwrap();
    ctor.call1(py, (vec2.x, vec2.y)).unwrap()
}
pub fn vec4_to_pyglm(py: Python<'_>, vec4: Vec4) -> Py<PyAny> {
    let ctor = get_glm_vec4(py).unwrap();
    ctor.call1(py, (vec4.x, vec4.y, vec4.z, vec4.w)).unwrap()
}

// functions to convert Vec2, Vec3, Vec4 to PyList
pub fn vec2_as_pylist(py: Python, vec2: Vec2) -> Py<PyAny> {
    let list = PyList::new(py, vec2.as_slice());
    list.unwrap().into()
}
pub fn vec3_as_pylist(py: Python, vec3: Vec3) -> Py<PyAny> {
    let list = PyList::new(py, vec3.as_slice());
    list.unwrap().into()
}
pub fn vec4_as_pylist(py: Python, vec4: Vec4) -> Py<PyAny> {
    let list = PyList::new(py, vec4.as_slice());
    list.unwrap().into()
}

// functions to convert PyAny to Vec2, Vec3, Vec4
pub fn convert_glm_vec3(py: Python, values: Py<PyAny>) -> Vec3 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let (a, b, c): (f32, f32, f32) = r.extract(py).unwrap();

    Vec3::new(a, b, c)
}

pub fn convert_glm_vec4(py: Python, values: Py<PyAny>) -> Vec4 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let (a, b, c, d): (f32, f32, f32, f32) = r.extract(py).unwrap();

    Vec4::new(a, b, c, d)
}

pub fn convert_glm_vec2(py: Python, values: Py<PyAny>) -> Vec2 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let (a, b): (f32, f32) = r.extract(py).unwrap();

    Vec2::new(a, b)
}

pub fn convert_tuple_texture_rgba(py: Python, tuple: Py<PyTuple>) -> Option<RGBA> {
    let tuple = tuple.bind(py).downcast::<PyTuple>().ok()?;
    match tuple.len() {
        3 => {
            let (a, b, c): (u8, u8, u8) = tuple.extract().unwrap();
            Some(RGBA {
                r: a,
                g: b,
                b: c,
                a: 255,
            })
        }
        4 => {
            let (a, b, c, d): (u8, u8, u8, u8) = tuple.extract().unwrap();
            Some(RGBA {
                r: a,
                g: b,
                b: c,
                a: d,
            })
        }
        _ => None,
    }
}

pub fn convert_tuple_rgba(tuple: &Bound<PyTuple>) -> Option<RGBA> {
    let size = tuple.len();
    match size {
        3 => {
            let (a, b, c): (u8, u8, u8) = tuple.extract().unwrap();
            Some(RGBA {
                r: a,
                g: b,
                b: c,
                a: 255,
            })
        }
        4 => {
            let (a, b, c, d): (u8, u8, u8, u8) = tuple.extract().unwrap();
            Some(RGBA {
                r: a,
                g: b,
                b: c,
                a: d,
            })
        }
        _ => None,
    }
}

pub fn from_pydict_int_v2<'py>(py: Python<'py>, dict: &Bound<'py, PyDict>) -> HashMap<i64, Vec2> {
    let mut map = HashMap::new();

    for (key, value) in dict.iter() {
        let key_i64: i64 = key.extract().unwrap();
        let vec2: Vec2 = convert_glm_vec2(py, value.unbind()); // or `value` depending on your fn sig
        map.insert(key_i64, vec2);
    }

    map
}

pub fn from_pydict_int_v3<'py>(py: Python<'py>, dict: &Bound<'py, PyDict>) -> HashMap<i64, Vec3> {
    let mut map = HashMap::new();

    for (key, value) in dict.iter() {
        let key_i64: i64 = key.extract().unwrap();
        let vec3: Vec3 = convert_glm_vec3(py, value.unbind()); // or `value` depending on your fn sig
        map.insert(key_i64, vec3);
    }

    map
}

pub fn from_pydict_int_v4<'py>(py: Python<'py>, dict: &Bound<'py, PyDict>) -> HashMap<i64, Vec4> {
    let mut map = HashMap::new();

    for (key, value) in dict.iter() {
        let key_i64: i64 = key.extract().unwrap();
        let vec4: Vec4 = convert_glm_vec4(py, value.unbind()); // or `value` depending on your fn sig
        map.insert(key_i64, vec4);
    }

    map
}
