use std::borrow::BorrowMut;

use nalgebra::{ArrayStorage, U1};
use nalgebra_glm::{vec4, Mat4, TVec4, Vec3, Vec4};

#[derive(Debug)]
pub struct VertexBuffer {
    /// seems like this should be done that way ?128 row, 1 column ?
    v3content: ArrayStorage<Vec3, 1, 128>,
    v4content: ArrayStorage<Vec4, 1, 128>,
}

impl VertexBuffer {
    // set the given vertex at the given location
    fn set_vertex(&mut self, v3: &Vec3, idx: usize) {
        self.v3content.as_mut_slice()[idx] = *v3;
    }

    // attempt at multiplying every vec3 of the v3content  by the matrix.
    // result should be stored in the content at the same index
    // optimally we would like this operation to easily be unfolded and SIMD if possible.
    // note: arraystorage does NOT support indexing.
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

#[pyclass]
pub struct VertexBufferPy {
    buffer: VertexBuffer,
}

#[pymethods]
impl VertexBufferPy {
    #[new]
    fn new() -> VertexBufferPy {
        let v3 = Vec3::zeros();
        let v4 = Vec4::zeros();

        // Create the ArrayStorage for a 3x2 matrix with f64 elements
        //let storage = ArrayStorage::<f64, 3, 2>(flat_data);

        let v3content = ArrayStorage([[v3]; 128]);
        let v4content = ArrayStorage([[v4]; 128]);
        let vb = VertexBuffer {
            v3content,
            v4content,
        };
        VertexBufferPy { buffer: vb }
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
    view_matrix: Mat4,
    project_matrix: Mat4,

    environment_light: Vec3,
}

#[pyclass]
pub struct TransformPackPy {
    data: TransformPack,
}

#[pymethods]
impl TransformPackPy {
    #[new]
    fn new() -> TransformPackPy {
        let v3 = Vec3::zeros();
        let mmmm = Mat4::identity();

        let vb = TransformPack {
            model_matrix: mmmm,
            view_matrix: mmmm,
            project_matrix: mmmm,
            environment_light: v3,
        };
        TransformPackPy { data: vb }
    }
    fn set_model_matrix_glm(&mut self, py: Python, value: Py<PyAny>) {
        self.data.model_matrix = convert_pymat4(py, value)
    }
    fn set_view_matrix_glm(&mut self, py: Python, value: Py<PyAny>) {
        self.data.view_matrix = convert_pymat4(py, value)
    }

    fn set_project_matrix_glm(&mut self, py: Python, value: Py<PyAny>) {
        self.data.project_matrix = convert_pymat4(py, value)
    }

    fn set_model_matrix(&mut self, values: [f32; 16]) {
        let m = Mat4::from_column_slice(&values);
        self.data.model_matrix = m
    }

    fn get_model_matrix_tuple(&mut self, py: Python) -> Py<PyTuple> {
        let t = PyTuple::new_bound(py, self.data.model_matrix.as_slice());
        t.into()
    }
}

fn convert_pymat4(py: Python, values: Py<PyAny>) -> Mat4 {
    let r = values.call_method0(py, "to_tuple").unwrap();
    let outer_tuple: &PyTuple = r.extract(py).unwrap();

    // Create an iterator over the nested tuples
    let nested_tuples_iter = outer_tuple.iter().map(|item| {
        // Extract each inner tuple
        let inner_tuple: (f32, f32, f32, f32) = item.extract().unwrap();
        inner_tuple
    });

    // Flatten the nested tuples into an iterator of floats
    let flat_iter = nested_tuples_iter.flat_map(|(a, b, c, d)| vec![a, b, c, d]);

    Mat4::from_iterator(flat_iter)
}
