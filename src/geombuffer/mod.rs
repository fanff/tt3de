use pyo3::{prelude::*, types::PyDict};

use crate::primitivbuffer::primitivbuffer::PrimitiveBuffer;

#[derive(Debug, Clone, Copy)]
pub struct GeomReferences {
    pub node_id: usize,
    pub material_id: usize,
}

#[derive(Debug)]
pub struct Point {
    pub geom_ref: GeomReferences,
    pub point_start: usize,
    pub uv_idx: usize,
}

#[derive(Debug)]
pub struct Points {
    pub geom_ref: GeomReferences,

    /// start index of the points in the vertex buffer
    pub point_start: usize,
    /// number of points
    pub point_count: usize,
    pub uv_idx: usize,
}

#[derive(Debug)]
pub struct Line {
    /// deprecated
    pub geom_ref: GeomReferences,
    pub p_start: usize,
    pub uv_start: usize,
}

#[derive(Debug, Clone, Copy)]
pub struct Polygon {
    pub geom_ref: GeomReferences,
    pub p_start: usize,
    pub p_count: usize,
    pub uv_start: usize,
    pub triangle_start: usize,
    pub triangle_count: usize,
}

impl Polygon {
    pub fn new(
        geom_ref: GeomReferences,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
    ) -> Self {
        Self {
            geom_ref,
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
        }
    }
    pub fn default() -> Self {
        Self {
            geom_ref: GeomReferences {
                node_id: 0,
                material_id: 0,
            },
            p_start: 0,
            p_count: 0,
            uv_start: 0,
            triangle_start: 0,
            triangle_count: 0,
        }
    }
}

#[derive(Debug)]
pub enum GeomElement {
    // 2D elements
    Points2D(Points),
    Rect2D(Points),
    Line2D(Points),
    Polygon2D(Polygon),

    // 3D elements
    Point3D(Point),
    Line3D(Points),
    Polygon3D(Polygon),
}
pub struct GeometryBuffer {
    pub max_size: usize,
    pub content: Box<[GeomElement]>,
    pub current_size: usize,
}

impl GeometryBuffer {
    fn add_line2d(
        &mut self,
        p_start: usize,
        point_count: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }
        let elem = GeomElement::Line2D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            point_start: p_start,
            point_count: point_count,
            uv_idx: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    fn add_rect2d(
        &mut self,
        top_left: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Rect2D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            point_start: top_left,
            point_count: 2,
            uv_idx: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    fn add_points_2d(
        &mut self,
        point_start: usize,
        point_count: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Points2D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            point_start,
            point_count: point_count,
            uv_idx,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    fn add_point(
        &mut self,
        pidx: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Point3D(Point {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            point_start: pidx,
            uv_idx,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    fn add_line3d(
        &mut self,
        p_start: usize,
        point_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }
        let elem = GeomElement::Line3D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            point_start: p_start,
            point_count: point_count,
            uv_idx: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    fn add_polygon2d(
        &mut self,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Polygon2D(Polygon {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    fn add_polygon_3d(
        &mut self,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Polygon3D(Polygon {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
}

#[pyclass]
pub struct GeometryBufferPy {
    pub buffer: GeometryBuffer,
}

#[pymethods]
impl GeometryBufferPy {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: usize) -> Self {
        let polygon_init = vec![Polygon::default(); max_size];

        let geom_elements: Vec<GeomElement> = polygon_init
            .into_iter()
            .map(GeomElement::Polygon2D)
            .collect();
        // Box the Vec<GeomElement>
        let content = geom_elements.into_boxed_slice();
        GeometryBufferPy {
            buffer: GeometryBuffer {
                max_size,
                content,
                current_size: 0,
            },
        }
    }
    fn add_line2d(
        &mut self,
        p_start: usize,
        point_count: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer
            .add_line2d(p_start, point_count, uv_start, node_id, material_id)
    }
    fn add_rect2d(
        &mut self,
        top_left: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer
            .add_rect2d(top_left, uv_start, node_id, material_id)
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
    fn add_point(
        &mut self,
        _py: Python,
        p_idx: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer.add_point(p_idx, uv_idx, node_id, material_id)
    }
    fn add_points_2d(
        &mut self,
        _py: Python,
        p_idx: usize,
        point_count: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer
            .add_points_2d(p_idx, point_count, uv_idx, node_id, material_id)
    }
    fn add_polygon2d(
        &mut self,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer.add_polygon2d(
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
            node_id,
            material_id,
        )
    }

    fn add_polygon_3d(
        &mut self,
        p_start: usize,
        p_count: usize,
        uv_start: usize,
        triangle_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer.add_polygon_3d(
            p_start,
            p_count,
            uv_start,
            triangle_start,
            triangle_count,
            node_id,
            material_id,
        )
    }

    /// Add a 3D line to the geometry buffer
    #[pyo3(signature = (p_start, point_count, uv_start, node_id, material_id))]
    fn add_line3d(
        &mut self,
        p_start: usize,
        point_count: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer
            .add_line3d(p_start, point_count, node_id, material_id, uv_start)
    }

    #[pyo3(signature = (geom_idx, new_material_id))]
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

    dict.into()
}
