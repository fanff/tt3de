use std::iter::from_fn;

use nalgebra::{ArrayStorage, U1};
use nalgebra_glm::{Mat4, Number, TVec2, TVec4, Vec2, Vec3, Vec4};

#[derive(Clone, Copy)]
pub struct UVArray<const DIM: usize, const UVCOUNT: usize, UVACC: Number> {
    uv_array: ArrayStorage<TVec2<UVACC>, DIM, UVCOUNT>,
}

impl<const DIM: usize, const UVCOUNT: usize, UVACC: Number> UVArray<DIM, UVCOUNT, UVACC> {
    pub fn new() -> Self {
        let d = TVec2::new(UVACC::zero(), UVACC::zero());
        let uv_array = ArrayStorage([[d; DIM]; UVCOUNT]);
        UVArray { uv_array }
    }
}

#[derive(Clone, Copy)]
pub struct PointInfo<DEPTHACC: Number> {
    pub row: usize,
    pub col: usize,
    pub depth: DEPTHACC,
}

#[derive(Clone, Copy)]
pub struct PrimitivReferences {
    pub node_id: usize,
    pub material_id: usize,
    pub geometry_id: usize,
    pub primitive_id: usize,
}

#[derive(Clone, Copy)]
pub enum PrimitiveElements<const UVCOUNT: usize, UVACC: Number, DEPTHACC: Number> {
    Point {
        fds: PrimitivReferences,
        row: usize,
        col: usize,
        depth: DEPTHACC,
        uv: UVArray<2, UVCOUNT, UVACC>,
    },
    Line {
        fds: PrimitivReferences,
        pa: usize,
        pb: usize,
        uv: UVArray<2, UVCOUNT, UVACC>,
    },
    Triangle {
        fds: PrimitivReferences,
        pa: PointInfo<DEPTHACC>,
        pb: PointInfo<DEPTHACC>,
        pc: PointInfo<DEPTHACC>,
        uv: UVArray<3, UVCOUNT, UVACC>,
    },
    Static {
        fds: PrimitivReferences,
        index: usize,
    },
}

pub struct PrimitiveBuffer<const UVCOUNT: usize, DEPTHACC: Number> {
    pub max_size: usize,
    pub current_size: usize,
    pub content: Box<[PrimitiveElements<UVCOUNT, f32, DEPTHACC>]>,
}

impl<const UVCOUNT: usize, DEPTHACC: Number> PrimitiveBuffer<UVCOUNT, DEPTHACC> {
    pub fn new(max_size: usize) -> Self {
        let p = UVArray::new();
        let init_array: Vec<PrimitiveElements<UVCOUNT, f32, DEPTHACC>> = vec![
            PrimitiveElements::Triangle {
                fds: PrimitivReferences {
                    node_id: 0,
                    material_id: 0,
                    geometry_id: 0,
                    primitive_id: 0,
                },
                uv: p,
                pa: PointInfo {
                    row: 0,
                    col: 0,
                    depth: DEPTHACC::zero()
                },
                pb: PointInfo {
                    row: 0,
                    col: 0,
                    depth: DEPTHACC::zero()
                },
                pc: PointInfo {
                    row: 0,
                    col: 0,
                    depth: DEPTHACC::zero()
                },
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
        depth: DEPTHACC,
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

        let uv: UVArray<2, UVCOUNT, f32> = UVArray::new();
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
    pub fn add_line(&mut self) {
        todo!()
    }
    pub fn add_triangle(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        p_a_row: usize,
        p_a_col: usize,
        p_a_depth: DEPTHACC,
        p_b_row: usize,
        p_b_col: usize,
        p_b_depth: DEPTHACC,
        p_c_row: usize,
        p_c_col: usize,
        p_c_depth: DEPTHACC,
        uv: UVArray<3, UVCOUNT, f32>,
    ) -> usize {
        if self.current_size == self.max_size {
            return self.current_size;
        }

        let pa = PointInfo {
            row: p_a_row,
            col: p_a_col,
            depth: p_a_depth,
        };

        let pr = PrimitivReferences {
            geometry_id: geometry_id,
            material_id: material_id,
            node_id: node_id,
            primitive_id: self.current_size,
        };
        let apoint = PrimitiveElements::Triangle {
            fds: pr,
            pa: pa,
            uv: uv,
            pb: PointInfo {
                row: p_b_row,
                col: p_b_col,
                depth: p_b_depth,
            },
            pc: PointInfo {
                row: p_c_row,
                col: p_c_col,
                depth: p_c_depth,
            },
        };
        self.content[self.current_size] = apoint;

        self.current_size += 1;

        self.current_size - 1
    }
    pub fn add_static(&mut self) {
        todo!()
    }
}
