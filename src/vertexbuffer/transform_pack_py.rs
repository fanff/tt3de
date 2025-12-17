use pyo3::{
    prelude::*,
    types::{PyFunction, PyTuple},
};

use crate::{
    utils::{convert_pymat4, mat4_to_pyglm, mat4_to_slicelist},
    vertexbuffer::transform_pack::TransformPack,
};

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
        let m4 = convert_pymat4(py, &value);
        self.data.add_node_transform(m4)
    }
    fn set_node_transform(&mut self, py: Python, idx: usize, value: Py<PyAny>) {
        let m4 = convert_pymat4(py, &value);
        self.data.set_node_transform(idx, m4);
    }

    fn get_node_transform(&self, py: Python, idx: usize) -> Py<PyTuple> {
        let t = PyTuple::new(py, self.data.get_node_transform(idx).as_slice()).unwrap();
        t.into()
    }

    fn set_view_matrix_glm(&mut self, py: Python, value_glm: Py<PyAny>) {
        self.data.view_matrix_2d = convert_pymat4(py, &value_glm)
    }
    fn get_view_matrix(&self, py: Python) -> Py<PyAny> {
        mat4_to_pyglm(py, self.data.view_matrix_2d).into()
    }

    fn set_view_matrix_3d(&mut self, py: Python, value: Py<PyAny>) {
        self.data.view_matrix_3d = convert_pymat4(py, &value)
    }
    fn get_view_matrix_3d(&self, py: Python) -> Py<PyAny> {
        mat4_to_slicelist(py, self.data.view_matrix_2d)
    }

    /// set the projection matrix
    fn set_projection_matrix(&mut self, py: Python, value: Py<PyAny>) {
        self.data.projection_matrix_3d = convert_pymat4(py, &value)
    }
    /// get the projection matrix
    fn get_projection_matrix(&self, py: Python) -> Py<PyAny> {
        mat4_to_slicelist(py, self.data.projection_matrix_3d)
    }
}
