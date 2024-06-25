struct PrimitivReferences {
    node_id: usize,
    material_id: usize,
    geometry_id: usize,
}

enum PrimitiveElements {
    Point {
        fds: PrimitivReferences,
        pa: usize,
        pb: usize,
    },
    Line {
        fds: PrimitivReferences,
        pa: usize,
        pb: usize,
    },
    Triangle {
        fds: PrimitivReferences,
        p_start: usize,
        p_end: usize,
    },
    Static {
        index: usize,
    },
}
