use nalgebra::{ArrayStorage, RawStorage};
use nalgebra_glm::{Mat4, Number, TVec2, TVec4, Vec2, Vec3, Vec4};

#[derive(Debug)]
pub struct UVBuffer<UVACC: Number> {
    pub uv_array: Vec<TVec2<UVACC>>,
    pub uv_size: usize,
}

impl Default for UVBuffer<f32> {
    fn default() -> Self {
        Self::new(0)
    }
}
impl<UVACC: Number> UVBuffer<UVACC> {
    /// Create a new UVBuffer with a given initial capacity
    pub fn new(initial_capacity: usize) -> Self {
        UVBuffer {
            uv_array: Vec::with_capacity(initial_capacity * 3), // Each "UV" is a triplet
            uv_size: 0,
        }
    }

    pub fn set_uv(&mut self, uv: &TVec2<UVACC>, idx: usize) {
        if idx < self.uv_array.len() {
            self.uv_array[idx] = *uv;
        } else {
            panic!("Index out of bounds");
        }
    }

    pub fn add_uv(&mut self, uva: &TVec2<UVACC>, uvb: &TVec2<UVACC>, uvc: &TVec2<UVACC>) -> usize {
        if self.uv_array.len() < (self.uv_size + 1) * 3 {
            self.uv_array.reserve(3); // Reserve additional space for three elements if needed
        }

        self.uv_array.push(*uva);
        self.uv_array.push(*uvb);
        self.uv_array.push(*uvc);

        let returned = self.uv_size;
        self.uv_size += 1;
        returned
    }

    pub fn get_uv(&self, idx: usize) -> (&TVec2<UVACC>, &TVec2<UVACC>, &TVec2<UVACC>) {
        let base_idx = idx * 3;
        (
            &self.uv_array[base_idx],
            &self.uv_array[base_idx + 1],
            &self.uv_array[base_idx + 2],
        )
    }

    pub fn clear(&mut self) {
        self.uv_size = 0;
        self.uv_array.clear(); // Clear the Vec, maintaining its capacity
    }
}
