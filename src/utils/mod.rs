use nalgebra_glm::{Mat4, Vec3};
use pyo3::{types::PyTuple, Py, PyAny, Python};

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

pub fn convert_glm_vec3(py: Python, values: Py<PyAny>) -> Vec3 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let (a, b, c): (f32, f32, f32) = r.extract(py).unwrap();

    Vec3::new(a, b, c)
}
