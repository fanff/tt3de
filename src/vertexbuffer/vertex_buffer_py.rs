use nalgebra_glm::{Mat4, Vec2, Vec4};
use pyo3::{
    prelude::*,
    types::{PyFunction, PyTuple},
};

use crate::{
    utils::{convert_glm_vec2, convert_glm_vec3},
    vertexbuffer::{
        transform_pack::TransformPack, transform_pack_py::TransformPackPy, uv_buffer::UVBuffer,
        vertex_buffer::VertexBuffer,
    },
};

#[pyclass]
pub struct VertexBufferPy {
    pub buffer3d: VertexBuffer<Vec4>,
    pub uv_array: UVBuffer<f32>,
    pub buffer2d: VertexBuffer<Vec4>,
}
impl VertexBufferPy {
    /// Function to return the internal Buffers as tuple of mutable references
    pub fn get_internal_buffers_mut(
        &mut self,
    ) -> (
        &mut VertexBuffer<Vec4>,
        &mut UVBuffer<f32>,
        &mut VertexBuffer<Vec4>,
    ) {
        (&mut self.buffer3d, &mut self.uv_array, &mut self.buffer2d)
    }
}
#[pymethods]
impl VertexBufferPy {
    #[new]
    fn new(buffer3d_size: usize, uv_array_size: usize, buffer2d_size: usize) -> VertexBufferPy {
        VertexBufferPy {
            buffer3d: VertexBuffer::with_capacity(buffer3d_size),
            uv_array: UVBuffer::new(uv_array_size),
            buffer2d: VertexBuffer::with_capacity(buffer2d_size),
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

        let ta = PyTuple::new(py, [ra.x, ra.y]).unwrap();
        let tb = PyTuple::new(py, [rb.x, rb.y]).unwrap();
        let tc = PyTuple::new(py, [rc.x, rc.y]).unwrap();

        let tt = PyTuple::new(py, [ta, tb, tc]).unwrap();
        tt.into()
    }

    fn get_uv_max_content(&self, _py: Python) -> usize {
        self.uv_array.uv_array.capacity()
    }
    // 2d section
    fn add_2d_vertex(&mut self, x: f32, y: f32, z: f32) -> usize {
        let ve = Vec4::new(x, y, z, 1.0);
        self.buffer2d.add_vertex(&ve)
    }
    fn get_2d_vertex_tuple(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer2d.get_vertex(idx);
        let t = PyTuple::new(py, [result.x, result.y, result.z, result.w]).unwrap();
        t.into()
    }
    fn get_2d_calculated_tuple(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer2d.get_calculated(idx);
        let t = PyTuple::new(py, [result.x, result.y, result.z, result.w]);
        t.unwrap().into()
    }
    fn get_2d_len(&self, _py: Python) -> usize {
        self.buffer2d.len()
    }
    fn get_2d_capacity(&self, _py: Python) -> usize {
        self.buffer2d.capacity()
    }
    fn apply_2d_mv(
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

        self.buffer2d.apply_mv(
            inner_data.get_node_transform(node_id),
            &inner_data.view_matrix_2d,
            start,
            end,
        )
    }

    // 3d section
    fn get_3d_capacity(&self, _py: Python) -> usize {
        self.buffer3d.capacity()
    }
    fn get_3d_len(&self, _py: Python) -> usize {
        self.buffer3d.len()
    }

    fn add_3d_vertex(&mut self, x: f32, y: f32, z: f32) -> usize {
        let ve = Vec4::new(x, y, z, 1.0);
        self.buffer3d.add_vertex(&ve)
    }

    fn get_3d_vertex_tuple(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer3d.get_vertex(idx);
        let t = PyTuple::new(py, [result.x, result.y, result.z, result.w]).unwrap();
        t.into()
    }

    fn get_3d_calculated_tuple(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer3d.get_calculated(idx);
        let t = PyTuple::new(py, [result.x, result.y, result.z, result.w]);
        t.unwrap().into()
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

        self.buffer3d.apply_mv(
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
        self.buffer3d
            .apply_mvp(model_matrix, view_matrix, projection_matrix, start, end)
    }
}
