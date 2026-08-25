use pyo3::{prelude::*, types::PyDict};
use tt3de_core::geombuffer::*;

#[pyclass]
pub struct GeometryBufferPy {
    pub buffer: GeometryBuffer,
}

#[pymethods]
impl GeometryBufferPy {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: usize) -> Self {
        GeometryBufferPy {
            buffer: GeometryBuffer::new(max_size),
        }
    }
    #[pyo3(signature = (p_start, point_count, uv_start, node_id, material_id, transparent=false))]
    fn add_line2d(
        &mut self,
        p_start: usize,
        point_count: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer.add_line2d(
            p_start,
            point_count,
            uv_start,
            node_id,
            material_id,
            transparent,
        )
    }
    #[pyo3(signature = (top_left, uv_start, node_id, material_id, transparent=false))]
    fn add_rect2d(
        &mut self,
        top_left: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer
            .add_rect2d(top_left, uv_start, node_id, material_id, transparent)
    }
    fn get_element(&self, py: Python, idx: usize) -> Py<PyDict> {
        geometry_into_dict(py, &self.buffer.content[idx])
    }

    fn clear(&mut self) {
        self.buffer.current_size = 0;
    }

    fn geometry_count(&self) -> usize {
        self.buffer.current_size
    }
    #[pyo3(signature = (p_idx, uv_idx, node_id, material_id, transparent=false))]
    fn add_point_3d(
        &mut self,
        _py: Python,
        p_idx: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer
            .add_point_3d(p_idx, uv_idx, node_id, material_id, transparent)
    }
    #[pyo3(signature = (p_idx, point_count, uv_idx, node_id, material_id, transparent=false))]
    fn add_points_2d(
        &mut self,
        _py: Python,
        p_idx: usize,
        point_count: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer.add_points_2d(
            p_idx,
            point_count,
            uv_idx,
            node_id,
            material_id,
            transparent,
        )
    }
    #[pyo3(signature = (p_start, p_count, uv_start, triangle_start, triangle_count, node_id, material_id, transparent=false))]
    fn add_polygon2d(
        &mut self,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer.add_polygon2d(
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
            node_id,
            material_id,
            transparent,
        )
    }

    #[pyo3(signature = (p_start, p_count, uv_start, triangle_start, triangle_count, node_id, material_id, transparent=false))]
    fn add_polygon_3d(
        &mut self,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer.add_polygon_3d(
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
            node_id,
            material_id,
            transparent,
        )
    }

    /// Add a 3D line to the geometry buffer
    #[pyo3(signature = (p_start, point_count, uv_start, node_id, material_id, transparent=false))]
    fn add_line3d(
        &mut self,
        p_start: usize,
        point_count: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        self.buffer.add_line3d(
            p_start,
            point_count,
            node_id,
            material_id,
            uv_start,
            transparent,
        )
    }

    pub fn update_geometry_material(&mut self, geom_idx: usize, new_material_id: usize) {
        if geom_idx >= self.buffer.current_size {
            return;
        }

        match &mut self.buffer.content[geom_idx] {
            GeomElement::Rect2D(pi) => {
                pi.geom_ref.material_id = new_material_id;
            }
            GeomElement::Points2D(pi) => {
                pi.geom_ref.material_id = new_material_id;
            }
            GeomElement::Point3D(pi) => {
                pi.geom_ref.material_id = new_material_id;
            }
            GeomElement::Line3D(l) => {
                l.geom_ref.material_id = new_material_id;
            }
            GeomElement::Polygon2D(p) => {
                p.geom_ref.material_id = new_material_id;
            }
            GeomElement::Polygon3D(p) => {
                p.geom_ref.material_id = new_material_id;
            }
            GeomElement::Line2D(points) => {
                points.geom_ref.material_id = new_material_id;
            }
        }
    }
}

fn geometry_into_dict(py: Python, pi: &GeomElement) -> Py<PyDict> {
    let dict = PyDict::new(py);

    match pi {
        GeomElement::Rect2D(pi) => {
            dict.set_item("_type", "Rect2D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &pi.geom_ref))
                .unwrap();
            dict.set_item("point_start", pi.point_start).unwrap();
            dict.set_item("point_count", pi.point_count).unwrap();
            dict.set_item("uv_idx", pi.uv_idx).unwrap();
        }
        GeomElement::Points2D(pi) => {
            dict.set_item("_type", "Points2D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &pi.geom_ref))
                .unwrap();
            dict.set_item("point_start", pi.point_start).unwrap();
            dict.set_item("point_count", pi.point_count).unwrap();
            dict.set_item("uv_idx", pi.uv_idx).unwrap();
        }
        GeomElement::Point3D(pi) => {
            dict.set_item("_type", "Point3D").unwrap();
            dict.set_item("p_start", pi.point_start).unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &pi.geom_ref))
                .unwrap();
        }
        GeomElement::Line3D(l) => {
            dict.set_item("_type", "Line3D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &l.geom_ref))
                .unwrap();
            dict.set_item("point_start", l.point_start).unwrap();
            dict.set_item("point_count", l.point_count).unwrap();
            dict.set_item("uv_idx", l.uv_idx).unwrap();
        }
        GeomElement::Polygon2D(p) => {
            dict.set_item("_type", "Polygon2D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &p.geom_ref))
                .unwrap();
            dict.set_item("p_start", p.p_start).unwrap();
            dict.set_item("triangle_count", p.triangle_count).unwrap();
            dict.set_item("uv_start", p.uv_start).unwrap();
        }

        GeomElement::Polygon3D(p) => {
            dict.set_item("_type", "Polygon3D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &p.geom_ref))
                .unwrap();
            dict.set_item("p_start", p.p_start).unwrap();
            dict.set_item("triangle_count", p.triangle_count).unwrap();
            dict.set_item("uv_start", p.uv_start).unwrap();
        }
        GeomElement::Line2D(points) => {
            dict.set_item("_type", "Line2D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &points.geom_ref))
                .unwrap();
            dict.set_item("point_start", points.point_start).unwrap();
            dict.set_item("point_count", points.point_count).unwrap();
            dict.set_item("uv_idx", points.uv_idx).unwrap();
        }
    }
    dict.into()
}
fn geometry_ref_into_dict(py: Python, pi: &GeomReferences) -> Py<PyDict> {
    let dict = PyDict::new(py);

    dict.set_item("node_id", pi.node_id).unwrap();
    dict.set_item("material_id", pi.material_id).unwrap();
    dict.set_item("transparent", pi.transparent).unwrap();

    dict.into()
}
