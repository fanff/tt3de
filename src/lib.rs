pub mod drawbuffer;
pub mod geombuffer;
pub mod material;
pub mod primitiv_building;
pub mod primitivbuffer;
pub mod raster;
pub mod texturebuffer;
pub mod utils;
pub mod vertexbuffer;

use pyo3::prelude::*;

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[cfg(feature = "python-binding")]
#[pymodule]
fn tt3de(m: &Bound<'_, PyModule>) -> PyResult<()> {
    use crate::{
        material::combo_material::ComboMaterialPy,
        vertexbuffer::{transform_pack_py::TransformPackPy, vertex_buffer_py::VertexBufferPy},
    };
    use pyo3::{prelude::*, wrap_pymodule};
    m.add_class::<texturebuffer::TextureBufferPy>()?;
    m.add_class::<material::MaterialBufferPy>()?;
    m.add_class::<geombuffer::GeometryBufferPy>()?;
    m.add_class::<drawbuffer::DrawingBufferPy>()?;
    m.add_class::<VertexBufferPy>()?;
    m.add_class::<TransformPackPy>()?;

    m.add_class::<primitivbuffer::PrimitiveBufferPy>()?;
    m.add_function(wrap_pyfunction!(primitiv_building::build_primitives_py, m)?)?;
    m.add_function(wrap_pyfunction!(raster::raster_all_py, m)?)?;
    m.add_function(wrap_pyfunction!(primitiv_building::apply_material_py, m)?)?;
    m.add_function(wrap_pyfunction!(
        primitiv_building::apply_material_py_parallel,
        m
    )?)?;

    m.add_function(wrap_pyfunction!(drawbuffer::find_glyph_indices_py, m)?)?;

    let submodule = PyModule::new(m.py(), "materials")?;
    submodule.add_class::<ComboMaterialPy>()?;
    submodule.add_class::<material::TexturedBackPy>()?;
    submodule.add_class::<material::TexturedFrontPy>()?;
    submodule.add_class::<material::StaticColorFrontPy>()?;
    submodule.add_class::<material::StaticColorBackPy>()?;
    submodule.add_class::<material::StaticGlyphPy>()?;
    m.add_submodule(&submodule)?;

    Ok(())
}
