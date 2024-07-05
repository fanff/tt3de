use nalgebra_glm::Number;

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
        pa: PointInfo<DEPTHACC>,
        pb: PointInfo<DEPTHACC>,
        uv: usize,
    },
    Triangle {
        fds: PrimitivReferences,
        pa: PointInfo<DEPTHACC>,
        pb: PointInfo<DEPTHACC>,
        pc: PointInfo<DEPTHACC>,
        uv: usize,
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
                fds: _,
                pa: _,
                pb: _,
                pc: _,
                uv,
            } => *uv,
            PrimitiveElements::Static { fds: _, index: _ } => 0,
        }
    }
}

pub struct PrimitiveBuffer<DEPTHACC: Number> {
    pub max_size: usize,
    pub current_size: usize,
    pub content: Box<[PrimitiveElements<DEPTHACC>]>,
}

impl<DEPTHACC: Number> PrimitiveBuffer<DEPTHACC> {
    pub fn new(max_size: usize) -> Self {
        let init_array: Vec<PrimitiveElements<DEPTHACC>> = vec![
            PrimitiveElements::Triangle {
                fds: PrimitivReferences {
                    node_id: 0,
                    material_id: 0,
                    geometry_id: 0,
                    primitive_id: 0,
                },
                uv: 0,
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
        p_a_depth: DEPTHACC,
        p_b_row: usize,
        p_b_col: usize,
        p_b_depth: DEPTHACC,
        uv: usize,
    ) -> usize {
        let pa = PointInfo {
            row: p_a_row,
            col: p_a_col,
            depth: p_a_depth,
        };

        let elem = PrimitiveElements::Line {
            fds: PrimitivReferences {
                geometry_id: geometry_id,
                material_id: material_id,
                node_id: node_id,
                primitive_id: self.current_size,
            },
            pa: pa,
            uv: uv,
            pb: PointInfo {
                row: p_b_row,
                col: p_b_col,
                depth: p_b_depth,
            },
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
        p_a_row: usize,
        p_a_col: usize,
        p_a_depth: DEPTHACC,
        p_b_row: usize,
        p_b_col: usize,
        p_b_depth: DEPTHACC,
        p_c_row: usize,
        p_c_col: usize,
        p_c_depth: DEPTHACC,
        uv: usize,
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
            uv: uv,
        };
        self.content[self.current_size] = apoint;

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
