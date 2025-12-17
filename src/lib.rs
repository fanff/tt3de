pub mod drawbuffer;
pub mod geombuffer;
pub mod material;
pub mod primitiv_building;
pub mod primitivbuffer;
pub mod raster;
pub mod texturebuffer;
pub mod ttsl;

pub mod utils;
pub mod vertexbuffer;
use pyo3::prelude::*;

/// Python module definition
/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[cfg(feature = "python-binding")]
#[pymodule]
fn tt3de(m: &Bound<'_, PyModule>) -> PyResult<()> {
    use crate::{
        material::combo_material::ComboMaterialPy,
        material::materials_py::*,
        vertexbuffer::{transform_pack_py::TransformPackPy, vertex_buffer_py::VertexBufferPy},
    };
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
    m.add_function(wrap_pyfunction!(drawbuffer::get_glyph_set, m)?)?;

    // adding run function for ttsl
    m.add_function(wrap_pyfunction!(ttsl::ttslpy::ttsl_run, m)?)?;

    let submodule = PyModule::new(m.py(), "materials")?;
    submodule.add_class::<ComboMaterialPy>()?;
    submodule.add_class::<MaterialPy>()?;
    submodule.add_class::<BaseTexturePy>()?;
    submodule.add_class::<StaticColorPy>()?;
    submodule.add_class::<StaticGlyphPy>()?;
    m.add_submodule(&submodule)?;

    // see https://github.com/PyO3/pyo3/issues/759
    Python::attach(|py| {
        let sys_modules = py.import("sys").unwrap().getattr("modules").unwrap();
        sys_modules
            .set_item("tt3de.tt3de.materials", submodule)
            .unwrap();
    });

    toglyphmethod(m).unwrap();

    Ok(())
}

fn toglyphmethod(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let submodule = PyModule::new(m.py(), "toglyphmethod")?;
    submodule.add_class::<texturebuffer::toglyph_methods_py::ToGlyphMethodPy>()?;
    submodule.add_class::<texturebuffer::toglyph_methods_py::ToGlyphMethodPyMap4Luminance>()?;
    submodule.add_class::<texturebuffer::toglyph_methods_py::ToGlyphMethodPyStatic>()?;
    m.add_submodule(&submodule)?;

    // see https://github.com/PyO3/pyo3/issues/759
    Python::attach(|py| {
        let sys_modules = py.import("sys").unwrap().getattr("modules").unwrap();
        sys_modules
            .set_item("tt3de.tt3de.toglyphmethod", submodule)
            .unwrap();
    });
    Ok(())
}
