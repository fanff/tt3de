use crate::{
    drawbuffer::DrawingBufferPy,
    geombuffer::GeometryBufferPy,
    lightbuffer::LightBufferPy,
    material::MaterialBufferPy,
    primitivbuffer::PrimitiveBufferPy,
    texturebuffer::TextureBufferPy,
    vertexbuffer::{TransformPackPy, VertexBufferPy},
};
use tt3de_core::lightbuffer::{bind_frame_lights, LightBuffer};
use pyo3::{exceptions::PyValueError, pyfunction, PyRefMut, PyResult};
use tt3de_core::{
    drawbuffer::drawbuffer::{
        apply_material_on, apply_material_on_parallel, apply_material_transparent_on,
    },
    primitiv_building::build_primitives,
};

#[pyfunction]
pub fn build_primitives_py(
    geometry_buffer: &GeometryBufferPy,
    vbpy: &mut VertexBufferPy,
    trbuffer_py: &TransformPackPy,
    dbpy: &DrawingBufferPy,
    primitivbuffer: &mut PrimitiveBufferPy,
) {
    let prim_content = &mut primitivbuffer.content;

    build_primitives(
        &geometry_buffer.buffer,
        &mut vbpy.buffer3d,
        &mut vbpy.buffer2d,
        &vbpy.triangle_buffer3d,
        &trbuffer_py.data,
        &vbpy.uv_array,
        &dbpy.opaque_db,
        prim_content,
    );
}

#[pyfunction]
#[pyo3(signature = (material_buffer, texturebuffer, vertex_buffer, primitivbuffer, draw_buffer_py, pass_filter=None, light_buffer=None))]
pub fn apply_material_py(
    material_buffer: &MaterialBufferPy,
    texturebuffer: &TextureBufferPy,
    vertex_buffer: &VertexBufferPy,
    primitivbuffer: &PrimitiveBufferPy,
    mut draw_buffer_py: PyRefMut<'_, DrawingBufferPy>,
    pass_filter: Option<&str>,
    light_buffer: Option<&LightBufferPy>,
) {
    let empty = LightBuffer::new();
    let lights = light_buffer.map(|b| &b.data).unwrap_or(&empty);
    let _guard = bind_frame_lights(lights);
    let draw_buf: &mut DrawingBufferPy = &mut draw_buffer_py;

    match pass_filter {
        Some("transparent") => {
            let transparent_db = &draw_buf.transparent_db;
            let opaque_db = &mut draw_buf.opaque_db;
            apply_material_transparent_on(
                transparent_db,
                opaque_db,
                &material_buffer.content,
                &texturebuffer.data,
                &vertex_buffer.uv_array,
                &primitivbuffer.content,
            )
        }
        _ => apply_material_on(
            &mut draw_buf.opaque_db,
            &material_buffer.content,
            &texturebuffer.data,
            &vertex_buffer.uv_array,
            &primitivbuffer.content,
        ),
    }
}

#[pyfunction]
#[pyo3(signature = (material_buffer, texturebuffer, vertex_buffer, primitivbuffer, draw_buffer_py, pass_filter=None, light_buffer=None))]
pub fn apply_material_py_parallel(
    material_buffer: &MaterialBufferPy,
    texturebuffer: &TextureBufferPy,
    vertex_buffer: &VertexBufferPy,
    primitivbuffer: &PrimitiveBufferPy,
    mut draw_buffer_py: PyRefMut<'_, DrawingBufferPy>,
    pass_filter: Option<&str>,
    light_buffer: Option<&LightBufferPy>,
) -> PyResult<()> {
    let empty = LightBuffer::new();
    let lights = light_buffer.map(|b| &b.data).unwrap_or(&empty);
    let _guard = bind_frame_lights(lights);
    let draw_buf: &mut DrawingBufferPy = &mut draw_buffer_py;
    let material_pool = &draw_buf.material_pool;
    let pool = material_pool.as_ref().ok_or_else(|| {
        PyValueError::new_err(
            "DrawingBufferPy has no material thread pool (material_parallel_threads=None); \
             use apply_material_py for serial shading",
        )
    })?;
    if matches!(pass_filter, Some("transparent")) {
        let transparent_db = &draw_buf.transparent_db;
        let opaque_db = &mut draw_buf.opaque_db;
        apply_material_transparent_on(
            transparent_db,
            opaque_db,
            &material_buffer.content,
            &texturebuffer.data,
            &vertex_buffer.uv_array,
            &primitivbuffer.content,
        );
    } else {
        apply_material_on_parallel(
            pool.as_ref(),
            &mut draw_buf.opaque_db,
            &material_buffer.content,
            &texturebuffer.data,
            &vertex_buffer.uv_array,
            &primitivbuffer.content,
        );
    }
    Ok(())
}
