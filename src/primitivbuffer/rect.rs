use crate::raster;
use raster::vertex::Vertex;

use super::primitivbuffer::PrimitivReferences;

#[derive(Clone, Copy)]
pub struct PRect {
    pub primitive_reference: PrimitivReferences,
    pub top_left: Vertex,
    pub bottom_right: Vertex,
}

impl PRect {
    pub fn new(primitive_reference: PrimitivReferences, pa: Vertex, pb: Vertex) -> Self {
        Self {
            primitive_reference,
            top_left: pa,
            bottom_right: pb,
        }
    }
}
