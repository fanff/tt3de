use std::ops::{AddAssign, Div, Mul, Sub};

use nalgebra_glm::{floor, vec2, vec3, Number, Real, TVec2, TVec3, Vec2};

use crate::{geombuffer::Point, raster::raster_triangle_tomato::Vertex};

use super::{PTriangle, PTriangle3D};

#[derive(Clone, Copy)]
pub struct PointInfo<DEPTHACC: Real> {
    pub row: usize,
    pub col: usize,
    pub p: TVec3<DEPTHACC>,
}

impl PointInfo<f32> {
    pub fn zero() -> Self {
        PointInfo {
            row: 0,
            col: 0,
            p: vec3(0.0, 0.0, 0.0),
        }
    }

    pub fn new(row_f: f32, col_f: f32, depth: f32) -> Self {
        PointInfo {
            row: row_f as usize,
            col: col_f as usize,
            p: vec3(row_f, col_f, depth),
        }
    }
    pub fn new_from_interpolate(
        pa: &PointInfo<f32>,
        pb: &PointInfo<f32>,
        t: f32,
    ) -> PointInfo<f32> {
        let vout = pa.p + (pb.p - pa.p) * t;
        PointInfo::new(vout.x, vout.y, vout.z)
    }
    pub fn f32_row(&self) -> f32 {
        self.p.x
    }
    pub fn f32_col(&self) -> f32 {
        self.p.y
    }

    pub fn as_f32_row_col(&self) -> (f32, f32) {
        (self.p.x, self.p.y)
    }
    pub fn as_vec2_row_col(&self) -> Vec2 {
        self.p.xy()
    }

    pub fn depth(&self) -> f32 {
        self.p.z
    }

    pub fn divide_in_place_by(&mut self, divisor: f32) -> Self {
        self.p /= divisor;
        *self
    }
}
impl Sub for PointInfo<f32> {
    type Output = PointInfo<f32>;
    fn sub(self, rhs: Self) -> Self::Output {
        let v = self.p - rhs.p;
        PointInfo::new(v.y, v.x, v.z)
    }
}

impl Mul<f32> for PointInfo<f32> {
    type Output = PointInfo<f32>;
    fn mul(self, rhs: f32) -> Self::Output {
        let v = self.p * rhs;
        PointInfo::new(v.y, v.x, v.z)
    }
}
impl Div<f32> for PointInfo<f32> {
    type Output = PointInfo<f32>;
    fn div(self, rhs: f32) -> Self::Output {
        let v = self.p / rhs;
        PointInfo::new(v.y, v.x, v.z)
    }
}
impl AddAssign for PointInfo<f32> {
    fn add_assign(&mut self, rhs: Self) {
        self.p += rhs.p;
    }
}

#[cfg(test)]
pub mod test_point_info {
    use crate::primitivbuffer::primitivbuffer::PointInfo;

    #[test]
    pub fn test_as_f32_point() {
        let point: PointInfo<f32> = PointInfo::new(1.0, 2.0, 3.0);
        let (row, col) = point.as_f32_row_col();
        assert_eq!(row, 1.0);
        assert_eq!(col, 2.0);
    }

    #[test]
    pub fn test_as_vec2_point() {
        let point: PointInfo<f32> = PointInfo::new(1.0, 2.0, 3.0);
        let vec2 = point.as_vec2_row_col();
        assert_eq!(vec2.x, 1.0);
        assert_eq!(vec2.y, 2.0);
    }
}

#[derive(Clone, Copy)]
pub struct PrimitivReferences {
    pub node_id: usize,
    pub material_id: usize,
    pub geometry_id: usize,
    pub primitive_id: usize,
}

impl PrimitivReferences {
    pub fn new(
        node_id: usize,
        material_id: usize,
        geometry_id: usize,
        primitive_id: usize,
    ) -> Self {
        Self {
            node_id,
            material_id,
            geometry_id,
            primitive_id,
        }
    }
}

#[derive(Clone, Copy)]
pub enum PrimitiveElements {
    Point {
        fds: PrimitivReferences,
        point: PointInfo<f32>,
        uv: usize,
    },
    Line {
        fds: PrimitivReferences,
        pa: PointInfo<f32>,
        pb: PointInfo<f32>,
        uv: usize,
    },
    Triangle(PTriangle),
    Triangle3D(PTriangle3D),
    Static {
        fds: PrimitivReferences,
        index: usize,
    },
}

impl PrimitiveElements {
    pub fn get_uv_idx(&self) -> usize {
        match self {
            PrimitiveElements::Point {
                fds: _,
                point: _,
                uv,
            } => *uv,
            PrimitiveElements::Line {
                fds: _,
                pa: _,
                pb: _,
                uv,
            } => *uv,

            PrimitiveElements::Static { fds: _, index: _ } => 0,
            PrimitiveElements::Triangle(t) => t.uv,
            PrimitiveElements::Triangle3D(t) => t.uv_idx,
        }
    }
}

pub struct PrimitiveBuffer {
    pub max_size: usize,
    pub current_size: usize,
    pub content: Box<[PrimitiveElements]>,
}

impl PrimitiveBuffer {
    pub fn new(max_size: usize) -> Self {
        let init_array: Vec<PrimitiveElements> =
            vec![PrimitiveElements::Triangle(PTriangle::zero()); max_size];

        let content = init_array.into_boxed_slice();

        let current_size = 0;
        PrimitiveBuffer {
            max_size,
            current_size,
            content,
        }
    }

    pub fn add_triangle3d(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        pa: Vertex,
        pb: Vertex,
        pc: Vertex,
        uv_idx: usize,
    ) -> usize {
        if self.current_size == self.max_size {
            return self.current_size;
        }

        let pr = PrimitivReferences {
            geometry_id: geometry_id,
            material_id: material_id,
            node_id: node_id,
            primitive_id: self.current_size,
        };

        self.content[self.current_size] =
            PrimitiveElements::Triangle3D(PTriangle3D::new(pr, pa, pb, pc, uv_idx));

        self.current_size += 1;

        self.current_size - 1
    }

    pub fn add_point(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        row: f32,
        col: f32,
        depth: f32,
        uv: usize,
    ) -> usize {
        if self.current_size == self.max_size {
            return self.current_size;
        }
        let pr = PrimitivReferences {
            geometry_id: geometry_id,
            material_id: material_id,
            node_id: node_id,
            primitive_id: self.current_size,
        };

        let apoint = PrimitiveElements::Point {
            fds: pr,
            point: PointInfo::new(row, col, depth),
            uv: uv,
        };
        self.content[self.current_size] = apoint;

        self.current_size += 1;

        self.current_size - 1
    }
    pub fn add_line(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        p_a_row: f32,
        p_a_col: f32,
        p_a_depth: f32,
        p_b_row: f32,
        p_b_col: f32,
        p_b_depth: f32,
        uv: usize,
    ) -> usize {
        let pa = PointInfo::new(p_a_row, p_a_col, p_a_depth);

        let elem = PrimitiveElements::Line {
            fds: PrimitivReferences {
                geometry_id: geometry_id,
                material_id: material_id,
                node_id: node_id,
                primitive_id: self.current_size,
            },
            pa: pa,
            uv: uv,
            pb: PointInfo::new(p_b_row, p_b_col, p_b_depth),
        };
        self.content[self.current_size] = elem;

        self.current_size += 1;

        self.current_size - 1
    }
    pub fn add_triangle(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        p_a_row: f32,
        p_a_col: f32,
        p_a_depth: f32,
        p_b_row: f32,
        p_b_col: f32,
        p_b_depth: f32,
        p_c_row: f32,
        p_c_col: f32,
        p_c_depth: f32,
        uv_idx: usize,
    ) -> usize {
        if self.current_size == self.max_size {
            return self.current_size;
        }

        let pr = PrimitivReferences {
            geometry_id: geometry_id,
            material_id: material_id,
            node_id: node_id,
            primitive_id: self.current_size,
        };

        self.content[self.current_size] = PrimitiveElements::Triangle(PTriangle::new(
            pr,
            PointInfo::new(p_a_row, p_a_col, p_a_depth),
            PointInfo::new(p_b_row, p_b_col, p_b_depth),
            PointInfo::new(p_c_row, p_c_col, p_c_depth),
            uv_idx,
        ));

        self.current_size += 1;

        self.current_size - 1
    }
    pub fn add_static(&mut self) {
        todo!()
    }

    pub fn clear(&mut self) {
        self.current_size = 0;
    }
}
