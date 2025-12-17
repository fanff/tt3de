use crate::raster;
use raster::vertex::Vertex;

use super::primitivbuffer::{PointInfo, PrimitivReferences};

#[derive(Clone, Copy)]
pub struct PTriangle3D {
    pub primitive_reference: PrimitivReferences,
    pub pa: Vertex,
    pub pb: Vertex,
    pub pc: Vertex,
}

impl PTriangle3D {
    pub fn new(
        primitive_reference: PrimitivReferences,
        pa: Vertex,
        pb: Vertex,
        pc: Vertex,
    ) -> Self {
        Self {
            primitive_reference,
            pa,
            pb,
            pc,
        }
    }
    pub fn zero() -> Self {
        Self {
            primitive_reference: PrimitivReferences::new(0, 0, 0, 0),
            pa: Vertex::zero(),
            pb: Vertex::zero(),
            pc: Vertex::zero(),
        }
    }
}
