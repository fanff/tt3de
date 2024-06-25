use nalgebra_glm::TVec4;
use pyo3::prelude::*;

#[derive(Debug)]
struct GeomReferences {
    node_id: usize,
    material_id: usize,
}

impl Clone for GeomReferences {
    fn clone(&self) -> Self {
        GeomReferences {
            node_id: self.node_id,
            material_id: self.material_id,
        }
    }
}

#[derive(Debug)]
pub struct Point {
    geom_ref: GeomReferences,
    pa: usize,
    pb: usize,
}

#[derive(Debug)]
pub struct Line {
    geom_ref: GeomReferences,
    pa: usize,
    pb: usize,
}

#[derive(Debug)]
pub struct Polygon {
    geom_ref: GeomReferences,
    p_start: usize,
    p_end: usize,
}

impl Clone for Polygon {
    fn clone(&self) -> Self {
        Polygon {
            geom_ref: self.geom_ref.clone(), // assuming GeomReferences implements Clone
            p_start: self.p_start,
            p_end: self.p_end,
        }
    }
}

#[derive(Debug)]
pub enum GeomElement {
    Point,
    Line(Line),
    Polygon(Polygon),
}

pub struct GeometryBuffer {
    max_size: usize,
    content: Box<[GeomElement]>,
}

impl GeometryBuffer {
    fn add_point() {}
    fn add_polygon() {}
}

#[pyclass]
pub struct GeometryBufferPy {
    buffer: GeometryBuffer,
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
                p_end: 0,
            };
            max_size
        ];

        let geom_elements: Vec<GeomElement> =
            polygon_init.into_iter().map(GeomElement::Polygon).collect();
        // Step 3: Box the Vec<GeomElement>
        let content = geom_elements.into_boxed_slice();
        GeometryBufferPy {
            buffer: GeometryBuffer {
                max_size: max_size,
                content,
            },
        }
    }
}
