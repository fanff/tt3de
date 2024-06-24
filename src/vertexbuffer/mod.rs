use nalgebra::ArrayStorage;
use nalgebra_glm::TVec4;

use pyo3::prelude::*;

#[pyclass]
#[derive(Debug)]
struct VertexBuffer {
    /// seems like this should be done that way ?128 row, 1 column ?
    content: ArrayStorage<TVec4<f32>, 128, 1>,
}
