use nalgebra_glm::{floor, vec2, vec3, Number, Real, TVec2, TVec3, Vec2};

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
    pub fn as_f32_row_col(&self) -> (f32, f32) {
        (self.p.x, self.p.y)
    }
    pub fn as_vec2_row_col(&self) -> Vec2 {
        self.p.xy()
    }

    pub fn depth(&self) -> f32 {
        self.p.z
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

#[derive(Clone, Copy)]
pub enum PrimitiveElements<DEPTHACC: Number> {
    Point {
        fds: PrimitivReferences,
        row: usize,
        col: usize,
        depth: DEPTHACC,
        uv: usize,
    },
    Line {
        fds: PrimitivReferences,
        pa: PointInfo<f32>,
        pb: PointInfo<f32>,
        uv: usize,
    },
    Triangle {
        primitive_reference: PrimitivReferences,
        pa: PointInfo<f32>,
        pb: PointInfo<f32>,
        pc: PointInfo<f32>,
        uv: usize,
        // store the original triangle definition before clipping
        vertex_idx: usize,
        triangle_id: usize,
    },
    Static {
        fds: PrimitivReferences,
        index: usize,
    },
}

impl<DEPTHACC: Number> PrimitiveElements<DEPTHACC> {
    pub fn get_uv_idx(&self) -> usize {
        match self {
            PrimitiveElements::Point {
                fds: _,
                row: _,
                col: _,
                depth: _,
                uv,
            } => *uv,
            PrimitiveElements::Line {
                fds: _,
                pa: _,
                pb: _,
                uv,
            } => *uv,
            PrimitiveElements::Triangle {
                primitive_reference: _,
                pa: _,
                pb: _,
                pc: _,
                uv,
                vertex_idx: _,
                triangle_id: _,
            } => *uv,
            PrimitiveElements::Static { fds: _, index: _ } => 0,
        }
    }
}

pub struct PrimitiveBuffer {
    pub max_size: usize,
    pub current_size: usize,
    pub content: Box<[PrimitiveElements<f32>]>,
}

impl PrimitiveBuffer {
    pub fn new(max_size: usize) -> Self {
        let init_array: Vec<PrimitiveElements<f32>> = vec![
            PrimitiveElements::Triangle {
                primitive_reference: PrimitivReferences {
                    node_id: 0,
                    material_id: 0,
                    geometry_id: 0,
                    primitive_id: 0,
                },
                uv: 0,
                pa: PointInfo::zero(),
                pb: PointInfo::zero(),
                pc: PointInfo::zero(),
                vertex_idx: 0,
                triangle_id: 0
            };
            max_size
        ];

        let content = init_array.into_boxed_slice();

        let current_size = 0;
        PrimitiveBuffer {
            max_size,
            current_size,
            content,
        }
    }

    pub fn add_point(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        row: usize,
        col: usize,
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
            row: row,
            col: col,
            depth: depth,
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
        p_a_row: usize,
        p_a_col: usize,
        p_a_depth: f32,
        p_b_row: usize,
        p_b_col: usize,
        p_b_depth: f32,
        uv: usize,
    ) -> usize {
        let pa = PointInfo::new(p_a_row as f32, p_a_col as f32, p_a_depth);

        let elem = PrimitiveElements::Line {
            fds: PrimitivReferences {
                geometry_id: geometry_id,
                material_id: material_id,
                node_id: node_id,
                primitive_id: self.current_size,
            },
            pa: pa,
            uv: uv,
            pb: PointInfo::new(p_b_row as f32, p_b_col as f32, p_b_depth),
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
        vertex_idx: usize,
        triangle_idx: usize,
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
        self.content[self.current_size] = PrimitiveElements::Triangle {
            primitive_reference: pr,
            pa: PointInfo::new(p_a_row, p_a_col, p_a_depth),
            pb: PointInfo::new(p_b_row, p_b_col, p_b_depth),
            pc: PointInfo::new(p_c_row, p_c_col, p_c_depth),
            uv: uv_idx,
            vertex_idx: vertex_idx,
            triangle_id: triangle_idx,
        };

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
