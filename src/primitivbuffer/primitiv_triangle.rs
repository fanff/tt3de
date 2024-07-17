use crate::raster::raster_triangle_tomato::Vertex;

use super::primitivbuffer::{PointInfo, PrimitivReferences};

#[derive(Clone, Copy)]
pub struct PTriangle {
    pub primitive_reference: PrimitivReferences,
    pub pa: PointInfo<f32>,
    pub pb: PointInfo<f32>,
    pub pc: PointInfo<f32>,
    pub uv: usize,
}

impl PTriangle {
    pub fn new(
        primitive_reference: PrimitivReferences,
        pa: PointInfo<f32>,
        pb: PointInfo<f32>,
        pc: PointInfo<f32>,
        uv: usize,
    ) -> Self {
        Self {
            primitive_reference,
            pa,
            pb,
            pc,
            uv,
        }
    }

    pub fn default() -> Self {
        Self {
            primitive_reference: PrimitivReferences::new(0, 0, 1, 0),
            pa: PointInfo::new(0.0, 0.0, 0.0),
            pb: PointInfo::new(5.0, 0.0, 1.0),
            pc: PointInfo::new(5.0, 1.0, 2.0),
            uv: 0,
        }
    }
    pub fn zero() -> Self {
        Self {
            primitive_reference: PrimitivReferences::new(0, 0, 0, 0),
            pa: PointInfo::new(0.0, 0.0, 0.0),
            pb: PointInfo::new(0.0, 0.0, 0.0),
            pc: PointInfo::new(0.0, 0.0, 0.0),
            uv: 0,
        }
    }
}

#[derive(Clone, Copy)]
pub struct PTriangle3D {
    pub primitive_reference: PrimitivReferences,
    pub pa: Vertex,
    pub pb: Vertex,
    pub pc: Vertex,
    pub uv_idx: usize,
}

impl PTriangle3D {
    pub fn new(
        primitive_reference: PrimitivReferences,
        pa: Vertex,
        pb: Vertex,
        pc: Vertex,
        uv_idx: usize,
    ) -> Self {
        Self {
            primitive_reference,
            pa,
            pb,
            pc,
            uv_idx,
        }
    }
}
