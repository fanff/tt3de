pub mod primitivbuffer;
use primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveBuffer, PrimitiveElements};
use pyo3::{prelude::*, pyclass, pymethods, types::PyDict, Py, Python};

#[pyclass]
pub struct PrimitiveBufferPy {
    pub content: PrimitiveBuffer,
}

#[pymethods]
impl PrimitiveBufferPy {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: usize) -> Self {
        // Step 3: Box the Vec<GeomElement>
        let content = PrimitiveBuffer::new(max_size);
        PrimitiveBufferPy { content: content }
    }
    fn clear(&mut self) {
        self.content.clear();
    }
    fn primitive_count(&self) -> usize {
        self.content.current_size
    }

    fn add_point(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        row: f32,
        col: f32,
        depth: f32,
        uv: usize,
    ) -> usize {
        self.content
            .add_point(node_id, geometry_id, material_id, row, col, depth, uv)
    }
    fn add_line(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        p_a_row: f32,
        p_a_col: f32,
        p_a_depth: f32,
        p_b_row: f32,
        p_b_col: f32,
        p_b_depth: f32,
        uv: usize,
    ) -> usize {
        self.content.add_line(
            node_id,
            geometry_id,
            material_id,
            p_a_row,
            p_a_col,
            p_a_depth,
            p_b_row,
            p_b_col,
            p_b_depth,
            uv,
        )
    }

    fn add_triangle(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        p_a_row: f32,
        p_a_col: f32,
        p_a_depth: f32,
        p_b_row: f32,
        p_b_col: f32,
        p_b_depth: f32,
        p_c_row: f32,
        p_c_col: f32,
        p_c_depth: f32,
        uv: usize,
        vertex_idx: usize,
        triangle_idx: usize,
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
            uv,
            vertex_idx,
            triangle_idx,
        )
    }
    fn add_static(&mut self) {
        todo!()
    }

    fn get_primitive(&self, py: Python, idx: usize) -> Py<PyDict> {
        to_dict(py, &self.content.content[idx])
    }
}

fn to_dict(py: Python, primitive: &PrimitiveElements) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);

    match primitive {
        &PrimitiveElements::Triangle {
            primitive_reference: fds,
            uv,
            pa,
            pb,
            pc,
            vertex_idx,
            triangle_id,
        } => {
            into_dict(py, &fds, &dict);

            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("pa", point_info_into_dict(py, &pa)).unwrap();
            dict.set_item("pb", point_info_into_dict(py, &pb)).unwrap();
            dict.set_item("pc", point_info_into_dict(py, &pc)).unwrap();

            dict.set_item("uv_idx", uv).unwrap();

            dict.set_item("vertex_idx", vertex_idx).unwrap();
            dict.set_item("triangle_idx", triangle_id).unwrap();
        }
        &PrimitiveElements::Point { fds, uv, point } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("row", point.row).unwrap();
            dict.set_item("col", point.col).unwrap();
            dict.set_item("depth", point.depth()).unwrap();
        }
        &PrimitiveElements::Line { fds, pa, pb, uv } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("pa", point_info_into_dict(py, &pa)).unwrap();
            dict.set_item("pb", point_info_into_dict(py, &pb)).unwrap();
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
    dict.set_item("depth", pi.p.z).unwrap();
    dict.into()
}
