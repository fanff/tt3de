use nalgebra::{ArrayStorage, RawStorage};
use nalgebra_glm::{Mat3, Mat4, Number, TVec2, TVec4, Vec2, Vec3, Vec4};

pub struct TransformPack {
    pub model_transforms: Box<[Mat4]>,
    pub view_matrix_2d: Mat4,
    pub view_matrix_3d: Mat4,
    pub projection_matrix_3d: Mat4,
    pub environment_light: Vec3,

    pub max_node_count: usize,
    pub current_count: usize,
}

impl TransformPack {
    pub fn new(max_node: usize) -> Self {
        let v3 = Vec3::zeros();
        let node_tr = vec![Mat4::identity(); max_node].into_boxed_slice();

        TransformPack {
            model_transforms: node_tr,
            view_matrix_2d: Mat4::identity(),
            view_matrix_3d: Mat4::identity(),
            projection_matrix_3d: Mat4::identity(),
            environment_light: v3,
            max_node_count: max_node,
            current_count: 0,
        }
    }

    pub fn clear(&mut self) {
        self.current_count = 0
    }

    pub fn add_node_transform(&mut self, m4: Mat4) -> usize {
        if self.current_count >= self.max_node_count {
            return self.current_count;
        }
        self.model_transforms[self.current_count] = m4;
        self.current_count += 1;
        self.current_count - 1
    }

    pub fn set_node_transform(&mut self, node_id: usize, m4: Mat4) {
        self.model_transforms[node_id] = m4;
    }

    pub fn get_node_transform(&self, node_id: usize) -> &Mat4 {
        &self.model_transforms[node_id]
    }
}
