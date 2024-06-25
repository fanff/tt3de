use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

pub mod drawbuffer;
pub mod geombuffer;
pub mod primitivbuffer;
pub mod vertexbuffer;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pyclass]
struct MyClass {
    inner: i32,
}

#[pymethods]
impl MyClass {
    #[new]
    #[pyo3(signature = (num=-1))]
    fn new(num: i32) -> Self {
        MyClass { inner: num }
    }
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn rtt3de(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_class::<MyClass>()?;
    m.add_class::<geombuffer::GeometryBufferPy>()?;
    m.add_class::<drawbuffer::Small8Drawing>()?;
    m.add_class::<drawbuffer::Small16Drawing>()?;
    m.add_class::<drawbuffer::AbigDrawing>()?;
    m.add_class::<vertexbuffer::VertexBufferPy>()?;
    m.add_class::<vertexbuffer::TransformPackPy>()?;
    Ok(())
}
