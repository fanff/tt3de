use pyo3::{prelude::*, types::PyDict};

#[derive(Debug, Clone, Copy)]
pub struct GeomReferences {
    pub node_id: usize,
    pub material_id: usize,
}

#[derive(Debug)]
pub struct Point {
    pub geom_ref: GeomReferences,
    pub pa: usize,
    pub uv_idx: usize,
}

#[derive(Debug)]
pub struct Line {
    pub geom_ref: GeomReferences,
    pub p_start: usize,
    pub uv_start: usize,
}

#[derive(Debug, Clone, Copy)]
pub struct Polygon {
    pub geom_ref: GeomReferences,
    pub p_start: usize,
    pub uv_start: usize,
    pub triangle_count: usize,
}

impl Polygon {
    pub fn new(
        geom_ref: GeomReferences,
        p_start: usize,
        uv_start: usize,
        triangle_count: usize,
    ) -> Self {
        Self {
            geom_ref,
            p_start,
            uv_start,
            triangle_count,
        }
    }
}

#[derive(Debug)]
pub enum GeomElement {
    Point3D(Point),
    Line3D(Line),
    Polygon2D(Polygon),
    PolygonFan3D(Polygon),
    Polygon3D(Polygon),
}

pub struct GeometryBuffer {
    pub max_size: usize,
    pub content: Box<[GeomElement]>,
    pub current_size: usize,
}

impl GeometryBuffer {
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
            pa: pidx,
            uv_idx,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    fn add_line3d(
        &mut self,
        p_start: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }
        let elem = GeomElement::Line3D(Line {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            p_start: p_start,
            uv_start: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    fn add_polygon2d(
        &mut self,
        p_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
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
            uv_start,
            triangle_count,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    fn add_polygon_fan_3d(
        &mut self,
        p_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::PolygonFan3D(Polygon {
            geom_ref: GeomReferences {
                node_id,
                material_id,
            },
            p_start,
            uv_start,
            triangle_count,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    fn add_polygon_3d(
        &mut self,
        p_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
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
            uv_start,
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
        let polygon_init = vec![
            Polygon {
                geom_ref: GeomReferences {
                    node_id: 0,
                    material_id: 0,
                },
                p_start: 0,
                uv_start: 0,
                triangle_count: 1,
            };
            max_size
        ];

        let geom_elements: Vec<GeomElement> = polygon_init
            .into_iter()
            .map(GeomElement::Polygon2D)
            .collect();
        // Step 3: Box the Vec<GeomElement>
        let content = geom_elements.into_boxed_slice();
        GeometryBufferPy {
            buffer: GeometryBuffer {
                max_size: max_size,
                content,
                current_size: 0,
            },
        }
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
        py: Python,
        p_idx: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
    ) -> usize {
        self.buffer.add_point(p_idx, uv_idx, node_id, material_id)
    }
    fn add_polygon2d(
        &mut self,
        p_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        self.buffer
            .add_polygon2d(p_start, triangle_count, node_id, material_id, uv_start)
    }
    fn add_polygon_fan_3d(
        &mut self,
        p_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        self.buffer
            .add_polygon_fan_3d(p_start, triangle_count, node_id, material_id, uv_start)
    }
    fn add_polygon_3d(
        &mut self,
        p_start: usize,
        triangle_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        self.buffer
            .add_polygon_3d(p_start, triangle_count, node_id, material_id, uv_start)
    }

    fn add_line3d(
        &mut self,
        p_start: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
    ) -> usize {
        self.buffer
            .add_line3d(p_start, node_id, material_id, uv_start)
    }
}

fn geometry_into_dict(py: Python, pi: &GeomElement) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);

    match pi {
        GeomElement::Point3D(pi) => {
            dict.set_item("pa", pi.pa).unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &pi.geom_ref))
                .unwrap();
        }
        GeomElement::Line3D(l) => {
            dict.set_item("_type", "Line3D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &l.geom_ref))
                .unwrap();
            dict.set_item("p_start", l.p_start).unwrap();
            dict.set_item("uv_start", l.uv_start).unwrap();
        }
        GeomElement::Polygon2D(p) => {
            dict.set_item("_type", "Polygon2D").unwrap();
            dict.set_item("geom_ref", geometry_ref_into_dict(py, &p.geom_ref))
                .unwrap();
            dict.set_item("p_start", p.p_start).unwrap();
            dict.set_item("triangle_count", p.triangle_count).unwrap();
            dict.set_item("uv_start", p.uv_start).unwrap();
        }
        GeomElement::PolygonFan3D(p) => {
            dict.set_item("_type", "PolygonFan3D").unwrap();
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
    }
    dict.into()
}
fn geometry_ref_into_dict(py: Python, pi: &GeomReferences) -> Py<PyDict> {
    let dict = PyDict::new_bound(py);

    dict.set_item("node_id", pi.node_id).unwrap();
    dict.set_item("material_id", pi.material_id).unwrap();

    dict.into()
}
