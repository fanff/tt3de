use nalgebra_glm::{Mat4, Vec2, Vec3};
use pyo3::{
    types::{PyAnyMethods, PyList, PyTuple, PyTupleMethods},
    Bound, Py, PyAny, Python,
};

use super::texturebuffer::RGBA;

pub fn convert_pymat4(py: Python, values: Py<PyAny>) -> Mat4 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let outer_tuple: &PyTuple = r.extract(py).unwrap();

    // Create an iterator over the nested tuples
    let nested_tuples_iter = outer_tuple.iter().map(|item| {
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
    let list = PyList::new_bound(py, s);
    list.into()
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

pub fn convert_tuple_texture_rgba(py: Python, tuple: Py<PyAny>) -> Option<RGBA> {
    let tuple = tuple.as_ref(py).downcast::<PyTuple>().ok()?;
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
