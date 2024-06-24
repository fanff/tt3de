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

pub struct Point {
    geom_ref: GeomReferences,
    pa: usize,
    pb: usize,
}

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
    Line,
    Polygon(Polygon),
}

#[pyclass]
pub struct GeometryBuffer {
    max_size: i32,
    content: Box<[GeomElement]>,
}

#[pymethods]
impl GeometryBuffer {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: i32) -> Self {
        let polygon_init = vec![
            Polygon {
                geom_ref: GeomReferences {
                    node_id: 0,
                    material_id: 0,
                },
                p_start: 0,
                p_end: 0,
            };
            max_size as usize
        ];

        let geom_elements: Vec<GeomElement> =
            polygon_init.into_iter().map(GeomElement::Polygon).collect();
        // Step 3: Box the Vec<GeomElement>
        let content = geom_elements.into_boxed_slice();

        GeometryBuffer { max_size, content }
    }
}

