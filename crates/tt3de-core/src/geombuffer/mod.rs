#[derive(Debug, Clone, Copy)]
pub struct GeomReferences {
    pub node_id: usize,
    pub material_id: usize,
    pub transparent: bool,
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
                transparent: false,
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
    pub fn new(max_size: usize) -> Self {
        let content = vec![Polygon::default(); max_size]
            .into_iter()
            .map(GeomElement::Polygon2D)
            .collect::<Vec<_>>()
            .into_boxed_slice();
        Self {
            max_size,
            content,
            current_size: 0,
        }
    }
    pub fn add_line2d(
        &mut self,
        p_start: usize,
        point_count: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }
        let elem = GeomElement::Line2D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
            },
            point_start: p_start,
            point_count: point_count,
            uv_idx: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    pub fn add_rect2d(
        &mut self,
        top_left: usize,
        uv_start: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Rect2D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
            },
            point_start: top_left,
            point_count: 2,
            uv_idx: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    pub fn add_points_2d(
        &mut self,
        point_start: usize,
        point_count: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Points2D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
            },
            point_start,
            point_count: point_count,
            uv_idx,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }
    pub fn add_point_3d(
        &mut self,
        pidx: usize,
        uv_idx: usize,
        node_id: usize,
        material_id: usize,
        transparent: bool,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Point3D(Point {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
            },
            point_start: pidx,
            uv_idx,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    pub fn add_line3d(
        &mut self,
        p_start: usize,
        point_count: usize,
        node_id: usize,
        material_id: usize,
        uv_start: usize,
        transparent: bool,
    ) -> usize {
        if self.current_size >= self.max_size {
            return self.current_size;
        }
        let elem = GeomElement::Line3D(Points {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
            },
            point_start: p_start,
            point_count: point_count,
            uv_idx: uv_start,
        });

        self.content[self.current_size] = elem;
        self.current_size += 1;
        self.current_size - 1
    }

    pub fn add_polygon2d(
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
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Polygon2D(Polygon {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
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

    pub fn add_polygon_3d(
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
        if self.current_size >= self.max_size {
            return self.current_size;
        }

        let elem = GeomElement::Polygon3D(Polygon {
            geom_ref: GeomReferences {
                node_id,
                material_id,
                transparent,
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
