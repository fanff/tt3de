use nalgebra_glm::vec3;
use nalgebra_glm::Scalar;
use nalgebra_glm::TVec3;

/// Represents information about a pixel with variable accuracy.
///
/// # Type Parameters
///
/// - `T`: A scalar type that implements the `nalgebra_glm::Scalar` trait. This allows the vectors to have variable precision.
///
/// # Fields
///
/// - `w`: A 3D vector of type `T`, representing some vector information about the pixel.
/// - `w_1`: Another 3D vector of type `T`, representing additional vector information about the pixel.
/// - `material_id`: An identifier for the material, typically used to reference a material in a materials database or array.
/// - `primitive_id`: An identifier for the primitive (e.g., a geometric primitive like a triangle or sphere).
/// - `node_id`: An identifier for the node, possibly in a scene graph or spatial partitioning structure.
/// - `geometry_id`: An identifier for the geometry, which could refer to a specific geometric object or model.
#[derive(Clone, Copy)]
pub struct PixInfo<T: nalgebra_glm::Scalar> {
    pub w: TVec3<T>,
    pub w_1: TVec3<T>,
    pub material_id: usize,
    pub primitive_id: usize,
    pub node_id: usize,
    pub geometry_id: usize,
}

impl<T: nalgebra_glm::Scalar> PixInfo<T> {
    fn clear(&mut self) {
        self.material_id = 0;
        self.primitive_id = 0;
        self.node_id = 0;
        self.geometry_id = 0;
    }
}
// Function to create an initialized PixInfo instance
pub fn create_pixinfo_init_f32() -> PixInfo<f32> {
    PixInfo {
        w: TVec3::zeros(),
        w_1: TVec3::zeros(),
        material_id: 0,
        primitive_id: 0,
        node_id: 0,
        geometry_id: 0,
    }
}

// A is the "accuracy of the detph buffer, expect a f32 here"
// could be a u8 for simple rendering engine; with flat 2D and layers
// L is the layer count ; more layer means more potential material stacking effects
#[derive(Clone, Copy)]
pub struct DepthBufferCell<A: Scalar, const L: usize> {
    pub pixinfo: [usize; L], // referencing pixel info per index // maybe index map ?
    pub depth: [A; L],
    // alternativelly, an array of tuple ? !
    //content: [(usize, A); L],
}
impl<D: Scalar, const L: usize> DepthBufferCell<D, L> {
    #[inline(always)]
    fn clear(&mut self, value: D) {
        for (d, p) in self.depth.iter_mut().zip(self.pixinfo.iter_mut()) {
            *d = value;
            *p = 0;
        }
    }
}

pub const DEPTH_BUFFER_CELL_INIT_F32_3L: DepthBufferCell<f32, 3> = DepthBufferCell {
    pixinfo: [0, 1, 2],
    depth: [0.1, 0.2, 0.3],
};
pub const DEPTH_BUFFER_CELL_INIT_F32_2L: DepthBufferCell<f32, 2> = DepthBufferCell {
    pixinfo: [0, 0],
    depth: [0.0, 0.0],
};

#[derive(Clone, Copy)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

#[derive(Clone, Copy)]
pub struct CanvasCell {
    pub front_color: Color,
    pub back_color: Color,
    pub glyph: u32,
}
pub const CANVAS_CELL_INIT: CanvasCell = CanvasCell {
    back_color: Color {
        r: 0,
        g: 0,
        b: 0,
        a: 0,
    },
    front_color: Color {
        r: 0,
        g: 0,
        b: 0,
        a: 0,
    },
    glyph: 0,
};

pub struct DrawBuffer<const L: usize, A: Scalar> {
    /// seems like this should be done that way ? R rows, C column , L depth layer, A ccurcy
    pub depthbuffer: Box<[DepthBufferCell<A, L>]>,
    pub canvas: Box<[CanvasCell]>,
    pub pixbuffer: Box<[PixInfo<A>]>,
    pub row_count: usize,
    pub col_count: usize,
}

// here theL ( layer) are like.. bounded; A is accuracy of the depth buffer (f32 usually)
impl<const L: usize, A: Scalar> DrawBuffer<L, A> {
    pub fn new(
        row_count: usize,
        col_count: usize,
        default_depth: DepthBufferCell<A, L>,
        inipix: PixInfo<A>,
    ) -> Self {
        // this store the depth for every cell, for every "layer" + and index
        let depthbuffer = vec![default_depth; row_count * col_count].into_boxed_slice();

        // this store specific propertiees in RxCxL. The index inside the depth buffer is actually pointing into this
        // array.
        // reason is that we will often do "compare and move/swap"; by using the index I guess the swap is just "swaping u8, instead of swapping the whole struc";
        let pixbuffer = vec![inipix; row_count * col_count * L].into_boxed_slice();

        // this stores the actually pixel "color pair + glyph"
        let canvas = vec![CANVAS_CELL_INIT; row_count * col_count].into_boxed_slice();

        DrawBuffer {
            depthbuffer,
            canvas,
            pixbuffer,
            col_count,
            row_count,
        }
    }

    #[inline(always)] // should this help ?!
    pub fn clear_depth(&mut self, value: A) {
        for depth_cell in self.depthbuffer.iter_mut() {
            depth_cell.clear(value);
        }
    }

    pub fn get_depth(&self, r: usize, c: usize, l: usize) -> A {
        let x = self.depthbuffer[r * self.col_count + c];
        let d = x.depth[l];
        d
    }

    pub fn get_depth_buffer_cell(&self, r: usize, c: usize) -> DepthBufferCell<A, L> {
        let x = self.depthbuffer[r * self.col_count + c];

        x
    }

    pub fn get_canvas_cell(&self, r: usize, c: usize) -> CanvasCell {
        let x = self.canvas[r * self.col_count + c];
        x
    }

    // will apply the material for every pixel.
    pub fn apply_material(&mut self) {
        let mut dummyvar = 0;
        for (depth_cell, canvascell) in self.depthbuffer.iter().zip(self.canvas.iter_mut()) {
            for depth_layer in (0..L).rev() {
                let loll = self.pixbuffer[depth_cell.pixinfo[depth_layer]];
                if loll.material_id == 3 {
                    dummyvar += 1;
                } else if loll.material_id == 2 {
                    dummyvar -= 1;
                }

                canvascell.back_color = Color {
                    r: dummyvar,
                    g: 0,
                    b: 0,
                    a: 0,
                }
            }
        }
    }
}
