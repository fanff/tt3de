use std::mem::MaybeUninit;

use nalgebra_glm::{Mat3, Mat4, Number, TVec2, TVec4, Vec2, Vec3, Vec4};

pub trait AllowedVec {
    fn zeros() -> Self;
}
impl AllowedVec for Vec3 {
    fn zeros() -> Self {
        Vec3::zeros()
    }
}
impl AllowedVec for Vec4 {
    fn zeros() -> Self {
        Vec4::zeros()
    }
}

#[derive(Clone, Copy, Debug)]
pub struct VertexPair<T: AllowedVec> {
    pub v: T,
    pub mvp: T,
}

pub struct VertexBuffer<T: AllowedVec> {
    data: Vec<MaybeUninit<VertexPair<T>>>, // contiguous storage
    len: usize,                            // number of initialized pairs
}

impl<T: AllowedVec> VertexBuffer<T> {
    /// Preallocate `cap` slots without initializing them.
    pub fn with_capacity(cap: usize) -> Self {
        let mut data = Vec::with_capacity(cap);
        // Fill with uninitialized slots
        data.resize_with(cap, || MaybeUninit::uninit());
        Self { data, len: 0 }
    }
    /// Current initialized length.
    #[inline]
    pub fn len(&self) -> usize {
        self.len
    }

    #[inline]
    pub fn capacity(&self) -> usize {
        self.data.len()
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    #[inline]
    pub fn is_full(&self) -> bool {
        self.len == self.capacity()
    }
    /// Convenient getters.
    #[inline]
    pub fn get(&self, idx: usize) -> &VertexPair<T> {
        if idx < self.len {
            unsafe { self.data.get_unchecked(idx).assume_init_ref() }
        } else {
            panic!("Index out of bounds");
        }
    }

    /// Convenient getters.
    #[inline]
    pub fn get_vertex(&self, idx: usize) -> &T {
        unsafe { &self.data.get_unchecked(idx).assume_init_ref().v }
    }

    #[inline]
    pub fn get_calculated(&self, idx: usize) -> &T {
        unsafe { &self.data.get_unchecked(idx).assume_init_ref().mvp }
    }

    #[inline]
    pub fn get_mut(&mut self, idx: usize) -> &mut VertexPair<T> {
        unsafe { self.data.get_unchecked_mut(idx).assume_init_mut() }
    }
}
impl VertexBuffer<Vec3> {
    #[inline]
    pub fn set_vertex(&mut self, vert: &Vec3, idx: usize) {
        let vp = unsafe { self.data.get_unchecked_mut(idx).assume_init_mut() };
        vp.v = *vert;
    }
    /// Add a vertex, returning its index.
    pub fn add_vertex(&mut self, vert: &Vec3) -> usize {
        assert!(self.len < self.capacity(), "VertexBuffer capacity exceeded");
        self.data[self.len].write(VertexPair {
            v: *vert,
            mvp: Vec3::zeros(),
        });
        self.len += 1;
        self.len - 1
    }
    pub fn apply_mvp(
        &mut self,
        model_matrix: &Mat3,
        view_matrix: &Mat3,
        projection_matrix: &Mat3,
        start: usize,
        end: usize,
    ) {
        let m4 = projection_matrix * view_matrix * model_matrix;
        for i in start..end {
            let vp = unsafe { self.data[i].assume_init_mut() };
            vp.mvp = m4 * vp.v;
        }
    }
}
impl VertexBuffer<Vec4> {
    #[inline]
    pub fn set_vertex(&mut self, vert: &Vec4, idx: usize) {
        let vp = unsafe { self.data.get_unchecked_mut(idx).assume_init_mut() };
        vp.v = *vert;
    }
    /// Add a vertex, returning its index.
    pub fn add_vertex(&mut self, vert: &Vec4) -> usize {
        assert!(self.len < self.capacity(), "VertexBuffer capacity exceeded");
        self.data[self.len].write(VertexPair {
            v: *vert,
            mvp: Vec4::zeros(),
        });
        self.len += 1;
        self.len - 1
    }
    pub fn apply_mv(&mut self, model_matrix: &Mat4, view_matrix: &Mat4, start: usize, end: usize) {
        let m4 = view_matrix * model_matrix;
        for i in start..end {
            let vp = unsafe { self.data[i].assume_init_mut() };
            vp.mvp = m4 * vp.v;
        }
    }
    pub fn apply_mvp(
        &mut self,
        model_matrix: &Mat4,
        view_matrix: &Mat4,
        projection_matrix: &Mat4,
        start: usize,
        end: usize,
    ) {
        let m4 = projection_matrix * view_matrix * model_matrix;
        for i in start..end {
            let vp = unsafe { self.data[i].assume_init_mut() };
            vp.mvp = m4 * vp.v;
        }
    }
}
