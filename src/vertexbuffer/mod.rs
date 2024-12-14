use crate::utils::{convert_glm_vec2, convert_pymat4, mat4_to_slicelist};
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
#[derive(Debug)]
pub struct VertexBuffer {
    pub v4content: Vec<Vec4>,
    pub mvp_calculated: Vec<Vec4>,
    pub current_size: usize,
}

impl Default for VertexBuffer {
    fn default() -> Self {
        Self::new(0)
    }
}

impl VertexBuffer {
    /// Create a new VertexBuffer with a given initial capacity
    pub fn new(initial_capacity: usize) -> Self {
        VertexBuffer {
            v4content: Vec::with_capacity(initial_capacity),
            mvp_calculated: Vec::with_capacity(initial_capacity),
            current_size: 0,
        }
    }

    pub fn add_vertex(&mut self, vert: &Vec4) -> usize {
        if self.current_size >= self.v4content.capacity() {
            self.v4content.reserve(1); // Reserve more space if needed
            self.mvp_calculated.reserve(1);
        }
        
        self.v4content.push(*vert);
        self.mvp_calculated.push(Vec4::zeros());
        self.current_size += 1;
        self.current_size - 1
    }

    pub fn get_at(&self, idx: usize) -> &Vec4 {
        &self.v4content[idx]
    }

    pub fn get_clip_space_vertex(&self, idx: usize) -> &Vec4 {
        &self.mvp_calculated[idx]
    }

    pub fn get_vertex_count(&self) -> usize {
        self.current_size
    }

    fn set_vertex(&mut self, vert: &Vec4, idx: usize) {
        if idx < self.v4content.len() {
            self.v4content[idx] = *vert;
        } else {
            panic!("Index out of bounds");
        }
    }

    pub fn apply_mv(&mut self, model_matrix: &Mat4, view_matrix: &Mat4, start: usize, end: usize) {
        let m4 = model_matrix * view_matrix;
        for i in start..end {
            if i < self.v4content.len() {
                self.mvp_calculated[i] = m4 * self.v4content[i];
            }
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
            self.mvp_calculated[i] = m4 * self.v4content[i];
        }
    }
}


use pyo3::{prelude::*, types::PyTuple};

#[pyclass]
pub struct VertexBufferPy {
    pub buffer: VertexBuffer,
    pub uv_array: UVBuffer<f32>,
}

#[pymethods]
impl VertexBufferPy {
    #[new]
    fn new(size: usize) -> VertexBufferPy {
        VertexBufferPy {
            buffer: VertexBuffer::new(size),
            uv_array: UVBuffer::new(size),
        }
    }

    fn add_uv(&mut self, py: Python, uva: Py<PyAny>, uvb: Py<PyAny>, uvc: Py<PyAny>) -> usize {
        let va: Vec2 = convert_glm_vec2(py, uva);
        let vb: Vec2 = convert_glm_vec2(py, uvb);
        let vc: Vec2 = convert_glm_vec2(py, uvc);
        self.uv_array.add_uv(&va, &vb, &vc)
    }
    fn get_uv_size(&self, _py: Python) -> usize {
        self.uv_array.uv_size
    }

    fn get_uv(&self, py: Python, index: usize) -> Py<PyTuple> {
        let (ra, rb, rc) = self.uv_array.get_uv(index);

        let ta = PyTuple::new_bound(py, [ra.x, ra.y]);
        let tb = PyTuple::new_bound(py, [rb.x, rb.y]);
        let tc = PyTuple::new_bound(py, [rc.x, rc.y]);

        let tt = PyTuple::new_bound(py, [ta, tb, tc]);

        tt.into()
    }

    fn get_uv_max_content(&self, _py: Python) -> usize {
        self.uv_array.uv_array.capacity()
    }

    fn get_max_content(&self, _py: Python) -> usize {
        self.buffer.v4content.capacity()
    }

    fn get_vertex_count(&self, _py: Python) -> usize {
        self.buffer.get_vertex_count()
    }
    fn add_vertex(&mut self, x: f32, y: f32, z: f32) -> usize {
        let ve = Vec4::new(x, y, z, 1.0);
        self.buffer.add_vertex(&ve)
    }
    fn set_vertex(&mut self, idx: usize, x: f32, y: f32, z: f32) {
        let ve = Vec4::new(x, y, z, 1.0);
        self.buffer.set_vertex(&ve, idx)
    }

    fn get_vertex(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer.v4content.as_slice()[idx];
        let t = PyTuple::new_bound(py, [result.x, result.y, result.z, result.w]);
        t.into()
    }

    fn get_clip_space_vertex(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer.get_clip_space_vertex(idx);
        let t = PyTuple::new_bound(py, [result.x, result.y, result.z, result.w]);
        t.into()
    }

    fn apply_mv(
        &mut self,
        py: Python,
        t: Py<TransformPackPy>,
        node_id: usize,
        start: usize,
        end: usize,
    ) {
        // Step 1: Borrow the TransformPackPy object using Bound stuff (magic!)
        let thething: &Bound<TransformPackPy> = t.bind(py);

        // Step 2: Access the `data` attribute safely  (magic!)
        let inner_data: &TransformPack = &thething.borrow().data;

        self.buffer.apply_mv(
            inner_data.get_node_transform(node_id),
            &inner_data.view_matrix_2d,
            start,
            end,
        )
    }

    pub fn apply_mvp(
        &mut self,
        py: Python,
        t: Py<TransformPackPy>,
        node_id: usize,
        start: usize,
        end: usize,
    ) {
        let thething: &Bound<TransformPackPy> = t.bind(py);
        let inner_data: &TransformPack = &thething.borrow().data;
        let model_matrix: &Mat4 = inner_data.get_node_transform(node_id);
        let view_matrix: &Mat4 = &inner_data.view_matrix_3d;
        let projection_matrix: &Mat4 = &inner_data.projection_matrix_3d;
        self.buffer
            .apply_mvp(model_matrix, view_matrix, projection_matrix, start, end)
    }
}

pub struct TransformPack {
    pub model_transforms: Box<[Mat4]>,
    pub view_matrix_2d: Mat4,
    pub view_matrix_3d: Mat4,
    pub projection_matrix_3d: Mat4,
    pub environment_light: Vec3,

    max_node_count: usize,
    current_count: usize,
}

impl TransformPack {
    fn new(max_node: usize) -> Self {
        let v3 = Vec3::zeros();
        let mmmm = Mat4::identity();
        let node_tr = vec![mmmm; max_node].into_boxed_slice();

        TransformPack {
            model_transforms: node_tr,
            view_matrix_2d: mmmm,
            view_matrix_3d: mmmm,
            projection_matrix_3d: mmmm,
            environment_light: v3,
            max_node_count: max_node,
            current_count: 0,
        }
    }

    fn clear(&mut self) {
        self.current_count = 0
    }

    fn add_node_transform(&mut self, m4: Mat4) -> usize {
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

#[pyclass]
pub struct TransformPackPy {
    pub data: TransformPack,
}

#[pymethods]
impl TransformPackPy {
    #[new]
    fn new(max_node: usize) -> TransformPackPy {
        TransformPackPy {
            data: TransformPack::new(max_node),
        }
    }
    fn clear(&mut self) {
        self.data.clear()
    }
    fn node_count(&self) -> usize {
        self.data.current_count
    }
    fn add_node_transform(&mut self, py: Python, value: Py<PyAny>) -> usize {
        let m4 = convert_pymat4(py, value);
        self.data.add_node_transform(m4)
    }
    fn set_node_transform(&mut self, py: Python, idx: usize, value: Py<PyAny>) {
        let m4 = convert_pymat4(py, value);
        self.data.set_node_transform(idx, m4);
    }

    fn get_node_transform(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let t = PyTuple::new_bound(py, self.data.get_node_transform(idx).as_slice());
        t.into()
    }

    fn set_view_matrix_glm(&mut self, py: Python, value: Py<PyAny>) {
        self.data.view_matrix_2d = convert_pymat4(py, value)
    }
    fn get_view_matrix(&self, py: Python) -> Py<PyAny> {
        mat4_to_slicelist(py, self.data.view_matrix_2d)
    }

    fn set_view_matrix_3d(&mut self, py: Python, value: Py<PyAny>) {
        self.data.view_matrix_3d = convert_pymat4(py, value)
    }
    fn get_view_matrix_3d(&self, py: Python) -> Py<PyAny> {
        mat4_to_slicelist(py, self.data.view_matrix_2d)
    }

    /// set the projection matrix
    fn set_projection_matrix(&mut self, py: Python, value: Py<PyAny>) {
        self.data.projection_matrix_3d = convert_pymat4(py, value)
    }
    /// get the projection matrix
    fn get_projection_matrix(&self, py: Python) -> Py<PyAny> {
        mat4_to_slicelist(py, self.data.projection_matrix_3d)
    }
}
