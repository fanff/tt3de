use crate::utils::{convert_glm_vec2, convert_pymat4, mat4_to_slicelist};
use nalgebra::{ArrayStorage, RawStorage};
use nalgebra_glm::{Mat4, Number, TVec2, TVec4, Vec2, Vec3, Vec4};

#[derive(Debug)]
pub struct UVBuffer<const UVCOUNT: usize, UVACC: Number> {
    pub uv_array: ArrayStorage<TVec2<UVACC>, UVCOUNT, 3>,
    pub uv_size: usize,
}

impl<const UVCOUNT: usize, UVACC: Number> Default for UVBuffer<UVCOUNT, UVACC> {
    fn default() -> Self {
        Self::new()
    }
}

impl<const UVCOUNT: usize, UVACC: Number> UVBuffer<UVCOUNT, UVACC> {
    pub fn new() -> UVBuffer<UVCOUNT, UVACC> {
        let d: TVec2<UVACC> = TVec2::zeros();
        let arraystore = ArrayStorage([[d; UVCOUNT]; 3]);
        
        UVBuffer {
            uv_array: arraystore,
            uv_size: 0,
        }
    }
    // set the given vertex at the given location
    pub fn set_uv(&mut self, uv: &TVec2<UVACC>, idx: usize) {
        self.uv_array.as_mut_slice()[idx] = *uv;
    }

    // set the given vertex at the given location
    pub fn add_uv(&mut self, uva: &TVec2<UVACC>, uvb: &TVec2<UVACC>, uvc: &TVec2<UVACC>) -> usize {
        /// = [uva, uvb, uvc];
        let x = self.uv_array.linear_index(self.uv_size, 0);
        self.set_uv(uva, x);

        let x = self.uv_array.linear_index(self.uv_size, 1);
        self.set_uv(uvb, x);
        let x = self.uv_array.linear_index(self.uv_size, 2);
        self.set_uv(uvc, x);

        let returned = self.uv_size;
        self.uv_size += 1;

        returned
    }

    pub fn get_uv(&self, idx: usize) -> (&TVec2<UVACC>, &TVec2<UVACC>, &TVec2<UVACC>) {
        (
            &self.uv_array.as_slice()[self.uv_array.linear_index(idx, 0)],
            &self.uv_array.as_slice()[self.uv_array.linear_index(idx, 1)],
            &self.uv_array.as_slice()[self.uv_array.linear_index(idx, 2)],
        )
    }

    pub fn clear(&mut self) {
        self.uv_size = 0;
    }
}

#[derive(Debug, Copy, Clone)]
pub struct VertexBuffer<const C: usize> {
    pub v4content: ArrayStorage<Vec4, 1, C>,

    // v4 into mvp_calculated after the mvp calculation
    pub mvp_calculated: ArrayStorage<Vec4, 1, C>,

    pub current_size: usize,
}
impl<const C: usize> Default for VertexBuffer<C> {
    fn default() -> Self {
        Self::new()
    }
}

impl<const C: usize> VertexBuffer<C> {
    pub fn new() -> Self {
        let v4: TVec4<f32> = TVec4::zeros(); // = Vec4::zeros();

        let v4content = ArrayStorage([[v4]; C]);
        
        VertexBuffer {
            v4content,
            mvp_calculated: ArrayStorage([[v4]; C]),
            current_size: 0,
        }
    }

    fn add_vertex(&mut self, vert: &Vec4) -> usize {
        self.v4content.as_mut_slice()[self.current_size] = *vert;
        self.current_size += 1;
        self.current_size - 1
    }
    pub fn get_at(&self, idx: usize) -> &Vec4 {
        &self.v4content.as_slice()[idx]
    }
    pub fn get_clip_space_vertex(&self, idx: usize) -> &Vec4 {
        &self.mvp_calculated.as_slice()[idx]
    }
    pub fn get_vertex_count(&self) -> usize {
        self.current_size
    }
    // set the given vertex at the given location
    fn set_vertex(&mut self, vert: &Vec4, idx: usize) {
        self.v4content.as_mut_slice()[idx] = *vert;
    }

    pub fn apply_mv(&mut self, model_matrix: &Mat4, view_matrix: &Mat4, start: usize, end: usize) {
        let m4 = model_matrix * view_matrix;
        let v4_slice = self.v4content.as_mut_slice();
        let mv_calc = self.mvp_calculated.as_mut_slice();
        for i in start..end {
            let avec = &v4_slice[i];

            // Store the result in the content at the same index
            mv_calc[i] = m4 * avec;
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
        let v4_slice = self.v4content.as_mut_slice();
        let mv_calc = self.mvp_calculated.as_mut_slice();
        for i in start..end {
            let avec = &v4_slice[i];

            // Store the result in the content at the same index
            mv_calc[i] = m4 * avec;
        }
    }
}

use pyo3::{prelude::*, types::PyTuple};
const MAX_VERTEX_CONTENT: usize = 2048;
const MAX_UV_CONTENT: usize = MAX_VERTEX_CONTENT * 2;

#[pyclass]
pub struct VertexBufferPy {
    pub buffer: VertexBuffer<MAX_VERTEX_CONTENT>,
    pub uv_array: UVBuffer<MAX_UV_CONTENT, f32>,
    pub uv_post_clipping: UVBuffer<MAX_UV_CONTENT, f32>,
}

#[pymethods]
impl VertexBufferPy {
    #[new]
    fn new() -> VertexBufferPy {
        VertexBufferPy {
            buffer: VertexBuffer::new(),
            uv_array: UVBuffer::new(),
            uv_post_clipping: UVBuffer::new(),
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
        MAX_UV_CONTENT
    }

    fn get_max_content(&self, _py: Python) -> usize {
        MAX_VERTEX_CONTENT
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

    fn get_post_clip_uv(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let (ra, rb, rc) = self.uv_post_clipping.get_uv(idx);

        let ta = PyTuple::new_bound(py, [ra.x, ra.y]);
        let tb = PyTuple::new_bound(py, [rb.x, rb.y]);
        let tc = PyTuple::new_bound(py, [rc.x, rc.y]);

        let tt = PyTuple::new_bound(py, [ta, tb, tc]);

        tt.into()
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
