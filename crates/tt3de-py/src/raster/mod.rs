use crate::{
    drawbuffer::DrawingBufferPy, primitivbuffer::PrimitiveBufferPy, vertexbuffer::VertexBufferPy,
};
use pyo3::{pyfunction, PyRefMut, Python};
use tt3de_core::raster::{raster_all, PassTag};

#[pyfunction]
#[pyo3(signature = (pb, vbuffpy, db, pass_filter=None))]
pub fn raster_all_py(
    _py: Python,
    pb: &PrimitiveBufferPy,
    vbuffpy: &VertexBufferPy,
    mut db: PyRefMut<'_, DrawingBufferPy>,
    pass_filter: Option<&str>,
) {
    let primitivbuffer = &pb.content;

    let pass = match pass_filter {
        Some("opaque") => Some(PassTag::Opaque),
        Some("transparent") => Some(PassTag::Transparent),
        _ => None,
    };
    match pass {
        Some(PassTag::Transparent) => {
            raster_all(
                primitivbuffer,
                &vbuffpy.buffer3d,
                &mut db.transparent_db,
                Some(PassTag::Transparent),
            );
        }
        _ => {
            raster_all(
                primitivbuffer,
                &vbuffpy.buffer3d,
                &mut db.opaque_db,
                Some(PassTag::Opaque),
            );
        }
    }
}
