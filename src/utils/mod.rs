use nalgebra_glm::{Mat4, Vec2, Vec3, Vec4};
use pyo3::{
    types::{PyAnyMethods, PyList, PyTuple, PyTupleMethods},
    Bound, Py, PyAny, Python,
};

use super::texturebuffer::RGBA;

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

pub fn convert_glm_vec3(py: Python, values: Py<PyAny>) -> Vec3 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let (a, b, c): (f32, f32, f32) = r.extract(py).unwrap();

    Vec3::new(a, b, c)
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
