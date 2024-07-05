use crate::utils::{convert_glm_vec2, convert_pymat4};
use nalgebra::{ArrayStorage, RawStorage};
use nalgebra_glm::{Mat4, Number, TVec2, TVec3, TVec4, Vec2, Vec3, Vec4};

#[derive(Debug)]
pub struct UVBuffer<const UVCOUNT: usize, UVACC: Number> {
    pub uv_array: ArrayStorage<TVec2<UVACC>, UVCOUNT, 3>,
    pub uv_size: usize,
}

impl<const UVCOUNT: usize, UVACC: Number> UVBuffer<UVCOUNT, UVACC> {
    fn new() -> UVBuffer<UVCOUNT, UVACC> {
        let d: TVec2<UVACC> = TVec2::zeros();
        let arraystore = ArrayStorage([[d; UVCOUNT]; 3]);
        let uvb = UVBuffer {
            uv_array: arraystore,
            uv_size: 0,
        };
        uvb
    }
    // set the given vertex at the given location
    pub fn set_uv(&mut self, uv: &TVec2<UVACC>, idx: usize) {
        self.uv_array.as_mut_slice()[idx] = *uv;
    }

    // set the given vertex at the given location
    pub fn add_uv(&mut self, uva: &TVec2<UVACC>, uvb: &TVec2<UVACC>, uvc: &TVec2<UVACC>) -> usize {
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

    pub fn get_uv(&self, idx: usize) -> (TVec2<UVACC>, TVec2<UVACC>, TVec2<UVACC>) {
        (
            self.uv_array.as_slice()[self.uv_array.linear_index(idx, 0)],
            self.uv_array.as_slice()[self.uv_array.linear_index(idx, 1)],
            self.uv_array.as_slice()[self.uv_array.linear_index(idx, 2)],
        )
    }
}

#[derive(Debug)]
pub struct VertexBuffer<const C: usize> {
    pub v3content: ArrayStorage<Vec3, 1, C>,
    pub v4content: ArrayStorage<Vec4, 1, C>,

    pub current_size: usize,
}
impl<const C: usize> VertexBuffer<C> {
    fn new() -> VertexBuffer<C> {
        let v3: TVec3<f32> = TVec3::zeros(); // = Vec3::zeros();
        let v4: TVec4<f32> = TVec4::zeros(); // = Vec4::zeros();

        let v3content = ArrayStorage([[v3]; C]);
        let v4content = ArrayStorage([[v4]; C]);
        let vb = VertexBuffer {
            v3content,
            v4content,
            current_size: 0,
        };
        vb
    }
    fn add_vertex(&mut self, v3: &Vec3) -> usize {
        self.set_vertex(v3, self.current_size);
        self.current_size += 1;
        self.current_size - 1
    }
    pub fn get_at_vec4(&self, idx: usize) -> &Vec4 {
        &self.v4content.as_slice()[idx]
    }

    pub fn get_at(&self, idx: usize) -> &Vec3 {
        &self.v3content.as_slice()[idx]
    }

    // set the given vertex at the given location
    fn set_vertex(&mut self, v3: &Vec3, idx: usize) {
        self.v3content.as_mut_slice()[idx] = *v3;
    }

    // attempt at multiplying every vec3 of the v3content  by the matrix.
    // result should be stored in the content at the same index
    // param start is included; end is NOT included
    fn mul_vertex(&mut self, value: &Mat4, start: usize, end: usize) {
        // Get mutable slices of the data in ArrayStorage
        let v3_slice = self.v3content.as_slice();
        let v4_slice = self.v4content.as_mut_slice();

        for i in start..end {
            let vec3 = &v3_slice[i];

            // Convert the Vec3 to Vec4 with w component set to 1.0
            let stuff = vec3.to_homogeneous();
            // Multiply the Vec4 by the matrix
            let result: TVec4<f32> = value * stuff;

            // Store the result in the content at the same index
            v4_slice[i] = result;
        }
    }

    fn apply_mv(&mut self, tr: &TransformPack, start: usize, end: usize) {
        let ttt = tr.model_matrix * tr.view_matrix;
        self.mul_vertex(&ttt, start, end);
    }
}

use pyo3::{prelude::*, types::PyTuple};
const MAX_VERTEX_CONTENT: usize = 128;
const MAX_UV_CONTENT: usize = MAX_VERTEX_CONTENT * 4;

#[pyclass]
pub struct VertexBufferPy {
    pub buffer: VertexBuffer<MAX_VERTEX_CONTENT>,
    pub uv_array: UVBuffer<MAX_UV_CONTENT, f32>,
}

#[pymethods]
impl VertexBufferPy {
    #[new]
    fn new() -> VertexBufferPy {
        let v3 = Vec3::zeros();
        let v4 = Vec4::zeros();

        let v3content = ArrayStorage([[v3]; MAX_VERTEX_CONTENT]);
        let v4content = ArrayStorage([[v4]; MAX_VERTEX_CONTENT]);
        let vb = VertexBuffer {
            v3content,
            v4content,
            current_size: 0,
        };
        let uvb = UVBuffer::new();

        VertexBufferPy {
            buffer: vb,
            uv_array: uvb,
        }
    }

    fn add_uv(&mut self, py: Python, uva: Py<PyAny>, uvb: Py<PyAny>, uvc: Py<PyAny>) -> usize {
        let va: Vec2 = convert_glm_vec2(py, uva);
        let vb: Vec2 = convert_glm_vec2(py, uvb);
        let vc: Vec2 = convert_glm_vec2(py, uvc);
        self.uv_array.add_uv(&va, &vb, &vc)
    }
    fn get_uv_size(&self, py: Python) -> usize {
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

    fn get_uv_max_content(&self, py: Python) -> usize {
        MAX_UV_CONTENT
    }

    fn get_max_content(&self, py: Python) -> usize {
        MAX_VERTEX_CONTENT
    }
    fn get_vertex_size(&self, py: Python) -> usize {
        self.buffer.current_size
    }
    fn add_vertex(&mut self, x: f32, y: f32, z: f32) -> usize {
        let ve = Vec3::new(x, y, z);
        self.buffer.add_vertex(&ve)
    }
    fn set_v3(&mut self, x: f32, y: f32, z: f32, idx: usize) {
        let ve = Vec3::new(x, y, z);
        self.buffer.set_vertex(&ve, idx)
    }

    fn get_v3_t(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer.v3content.as_slice()[idx];
        let t = PyTuple::new_bound(py, [result.x, result.y, result.z]);
        t.into()
    }

    fn get_v4_t(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let result = self.buffer.v4content.as_slice()[idx];
        let t = PyTuple::new_bound(py, [result.x, result.y, result.z, result.w]);
        t.into()
    }

    fn apply_mv(&mut self, py: Python, t: Py<TransformPackPy>, start: usize, end: usize) {
        // Step 1: Borrow the TransformPackPy object using Bound stuff (magic!)
        let thething: &Bound<TransformPackPy> = t.bind(py);

        // Step 2: Access the `data` attribute safely  (magic!)
        let inner_data: &TransformPack = &thething.borrow().data;

        self.buffer.apply_mv(inner_data, start, end)
    }
}

pub struct TransformPack {
    model_matrix: Mat4,

    model_transforms: Box<[Mat4]>,
    view_matrix: Mat4,
    project_matrix: Mat4,
    environment_light: Vec3,

    max_node_count: usize,
    current_count: usize,
}

impl TransformPack {
    fn new(max_node: usize) -> Self {
        let v3 = Vec3::zeros();
        let mmmm = Mat4::identity();
        let node_tr = vec![mmmm; max_node].into_boxed_slice();
        let vb = TransformPack {
            model_matrix: mmmm,
            model_transforms: node_tr,
            view_matrix: mmmm,
            project_matrix: mmmm,
            environment_light: v3,
            max_node_count: max_node,
            current_count: 0,
        };
        vb
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

    fn set_node_transform(&mut self, idx: usize, m4: Mat4) {
        self.model_transforms[idx] = m4;
    }

    fn get_node_transform(&self, idx: usize) -> &Mat4 {
        &self.model_transforms[idx]
    }
}

#[pyclass]
pub struct TransformPackPy {
    data: TransformPack,
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
        self.data.view_matrix = convert_pymat4(py, value)
    }

    fn set_project_matrix_glm(&mut self, py: Python, value: Py<PyAny>) {
        self.data.project_matrix = convert_pymat4(py, value)
    }
}
