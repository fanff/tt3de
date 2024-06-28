use pyo3::prelude::*;

pub mod drawbuffer;
pub mod geombuffer;
pub mod primitivbuffer;
pub mod raster;
pub mod utils;
pub mod vertexbuffer;

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn rtt3de(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<geombuffer::GeometryBufferPy>()?;
    m.add_class::<drawbuffer::Small16Drawing>()?;
    m.add_class::<drawbuffer::AbigDrawing>()?;
    m.add_class::<vertexbuffer::VertexBufferPy>()?;
    m.add_class::<vertexbuffer::TransformPackPy>()?;

    m.add_class::<primitivbuffer::PrimitiveBufferPy>()?;
    m.add_function(wrap_pyfunction!(raster::raster_all_py, m)?)?;

    Ok(())
}
