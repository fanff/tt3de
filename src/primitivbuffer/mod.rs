pub mod primitivbuffer;
use crate::utils::convert_pymat4;
use nalgebra_glm::Number;
use primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveBuffer, PrimitiveElements, UVArray};
use pyo3::{
    intern,
    prelude::*,
    pyclass, pymethods,
    types::{PyDict, PyList, PyTuple},
    Py, Python,
};

const UV_LAYER_COUNT: usize = 6;

#[pyclass]
pub struct PrimitiveBufferPy {
    pub content: PrimitiveBuffer<UV_LAYER_COUNT, f32>,
    pub uv_layer_count: usize,
}

#[pymethods]
impl PrimitiveBufferPy {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: usize) -> Self {
        // Step 3: Box the Vec<GeomElement>
        let content = PrimitiveBuffer::new(max_size);
        PrimitiveBufferPy {
            content: content,
            uv_layer_count: UV_LAYER_COUNT,
        }
    }

    fn primitive_count(&self) -> usize {
        self.content.current_size
    }

    const fn layer_count(&self) -> usize {
        UV_LAYER_COUNT
    }

    fn add_point(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        row: usize,
        col: usize,
        depth: f32,
    ) -> usize {
        self.content
            .add_point(node_id, geometry_id, material_id, row, col, depth)
    }
    fn add_line(&mut self) {
        todo!()
    }
    fn add_triangle(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        p_a_row: usize,
        p_a_col: usize,
        p_a_depth: f32,
        p_b_row: usize,
        p_b_col: usize,
        p_b_depth: f32,
        p_c_row: usize,
        p_c_col: usize,
        p_c_depth: f32,
    ) -> usize {
        self.content.add_triangle(
            node_id,
            geometry_id,
            material_id,
            p_a_row,
            p_a_col,
            p_a_depth,
            p_b_row,
            p_b_col,
            p_b_depth,
            p_c_row,
            p_c_col,
            p_c_depth,
            UVArray::new(),
        )
    }
    fn add_static(&mut self) {
        todo!()
    }

    fn get_primitive(&self, py: Python, idx: usize) -> Py<PyDict> {
        to_dict(py, &self.content.content[idx])
    }
}

fn to_dict(py: Python, primitive: &PrimitiveElements<6, f32, f32>) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);

    match primitive {
        &PrimitiveElements::Triangle {
            fds,
            uv,
            pa,
            pb,
            pc,
        } => {
            into_dict(py, &fds, &dict);

            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("pa", point_info_into_dict(py, &pa)).unwrap();
            dict.set_item("pb", point_info_into_dict(py, &pb)).unwrap();
            dict.set_item("pb", point_info_into_dict(py, &pc)).unwrap();
        }
        &PrimitiveElements::Point {
            fds,
            uv,
            row,
            col,
            depth,
        } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("row", row).unwrap();
            dict.set_item("col", col).unwrap();
            dict.set_item("depth", depth).unwrap();
        }
        &PrimitiveElements::Line { fds, pa, pb, uv } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("p_start", pa).unwrap();
            dict.set_item("p_end", pb).unwrap();
        }
        &PrimitiveElements::Static { fds, index } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("index", index).unwrap();
        }
    }

    dict.into()
}

fn into_dict(py: Python, primitive_ref: &PrimitivReferences, dict: &Bound<PyDict>) {
    dict.set_item("node_id", primitive_ref.node_id).unwrap();
    dict.set_item("geometry_id", primitive_ref.geometry_id)
        .unwrap();
    dict.set_item("material_id", primitive_ref.material_id)
        .unwrap();
    dict.set_item("primitive_id", primitive_ref.primitive_id)
        .unwrap();
}

fn point_info_into_dict(py: Python, pi: &PointInfo<f32>) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);
    dict.set_item("row", pi.row).unwrap();
    dict.set_item("col", pi.col).unwrap();
    dict.set_item("depth", pi.depth).unwrap();
    dict.into()
}
