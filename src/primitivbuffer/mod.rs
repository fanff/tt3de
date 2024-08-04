pub mod primitivbuffer;
use nalgebra_glm::{vec2, vec3, vec4};
use primitivbuffer::{PointInfo, PrimitivReferences, PrimitiveBuffer, PrimitiveElements};
use pyo3::{prelude::*, pyclass, pymethods, types::PyDict, Py, Python};

pub mod primitiv_triangle;
use primitiv_triangle::*;

pub mod rect;
use rect::*;

use crate::{
    raster::vertex::Vertex,
    utils::{vec2_as_pylist, vec3_as_pylist, vec4_as_pylist},
};

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
        PrimitiveBufferPy { content }
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
    ) -> usize {
        let va = Vertex::new(
            vec4(p_a_col, p_a_row, p_a_depth, 1.0),
            vec3(1.0, 0.0, 0.0),
            vec2(0.0, 0.0),
        );
        let vb = Vertex::new(
            vec4(p_b_col, p_b_row, p_b_depth, 1.0),
            vec3(0.0, 1.0, 0.0),
            vec2(1.0, 0.0),
        );
        let vc = Vertex::new(
            vec4(p_c_col, p_c_row, p_c_depth, 1.0),
            vec3(0.0, 0.0, 1.0),
            vec2(1.0, 1.0),
        );

        self.content
            .add_triangle3d(node_id, geometry_id, material_id, va, vb, vc)
    }

    #[pyo3(signature = ( node_id, geometry_id, material_id, top, left, top_left_depth, bottom, right, bottom_right_depth, 
        top_left_uv= (0.0, 0.0), bottom_right_uv= (1.0, 1.0) ))]
    fn add_rect(
        &mut self,
        node_id: usize,
        geometry_id: usize,
        material_id: usize,
        top: f32,
        left: f32,
        top_left_depth: f32,
        bottom: f32,
        right: f32,
        bottom_right_depth: f32,
        top_left_uv: (f32, f32),
        bottom_right_uv: (f32, f32),
    ) -> usize {
        let top_left = Vertex::new(
            vec4(left, top, top_left_depth, 1.0),
            vec3(1.0, 0.0, 0.0),
            vec2(top_left_uv.0, top_left_uv.1),
        );
        let bottom_right = Vertex::new(
            vec4(right, bottom, bottom_right_depth, 1.0),
            vec3(0.0, 1.0, 0.0),
            vec2(bottom_right_uv.0, bottom_right_uv.1),
        );
        self.content
            .add_rect(node_id, geometry_id, material_id, top_left, bottom_right)
    }
    fn add_static(&mut self) {
        todo!()
    }

    fn hello(&mut self) {
        todo!()
    }

    fn get_primitive(&self, py: Python, idx: usize) -> Py<PyDict> {
        to_dict(py, &self.content.content[idx])
    }
}

fn to_dict(py: Python, primitive: &PrimitiveElements) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);

    match primitive {
        &PrimitiveElements::Triangle(t) => {
            into_dict(py, &t.primitive_reference, &dict);
            dict.set_item("_type", "triangle").unwrap();
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("pa", point_info_into_dict(py, &t.pa))
                .unwrap();
            dict.set_item("pb", point_info_into_dict(py, &t.pb))
                .unwrap();
            dict.set_item("pc", point_info_into_dict(py, &t.pc))
                .unwrap();

            dict.set_item("uv_idx", t.uv).unwrap();
        }
        &PrimitiveElements::Point { fds, uv, point } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("row", point.row).unwrap();
            dict.set_item("col", point.col).unwrap();
            dict.set_item("depth", point.depth()).unwrap();
            dict.set_item("uv_idx", uv).unwrap();
        }
        &PrimitiveElements::Line { fds, pa, pb, uv } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("pa", point_info_into_dict(py, &pa)).unwrap();
            dict.set_item("pb", point_info_into_dict(py, &pb)).unwrap();
            dict.set_item("uv_idx", uv).unwrap();
        }
        &PrimitiveElements::Static { fds, index } => {
            into_dict(py, &fds, &dict);
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("index", index).unwrap();
            dict.set_item("_type", "static").unwrap();
        }

        &PrimitiveElements::Triangle3D(t) => {
            into_dict(py, &t.primitive_reference, &dict);
            dict.set_item("_type", "triangle").unwrap();
            // Assuming DepthBufferCell has some fields `field1` and `field2`
            dict.set_item("pa", vertex_into_dict(py, &t.pa)).unwrap();
            dict.set_item("pb", vertex_into_dict(py, &t.pb)).unwrap();
            dict.set_item("pc", vertex_into_dict(py, &t.pc)).unwrap();
        }
        &PrimitiveElements::Rect(rect) => {
            into_dict(py, &rect.primitive_reference, &dict);
            dict.set_item("pa", vertex_into_dict(py, &rect.top_left))
                .unwrap();
            dict.set_item("pb", vertex_into_dict(py, &rect.bottom_right))
                .unwrap();
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

fn vertex_into_dict(py: Python, pi: &Vertex) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);
    dict.set_item("pos", vec4_as_pylist(py, pi.pos)).unwrap();
    dict.set_item("normal", vec3_as_pylist(py, pi.normal))
        .unwrap();
    dict.set_item("uv", vec2_as_pylist(py, pi.uv)).unwrap();

    dict.into()
}
