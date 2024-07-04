use std::borrow::BorrowMut;

use nalgebra_glm::Number;
use nalgebra_glm::Scalar;
use nalgebra_glm::TVec3;
use nalgebra_glm::Vec3;

use crate::material::apply_material;
use crate::material::MaterialBuffer;
use crate::texturebuffer::TextureBuffer;
use crate::texturebuffer::RGBA;

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
pub struct PixInfo<T: nalgebra_glm::Number> {
    pub w: TVec3<T>,
    pub w_1: TVec3<T>,
    pub material_id: usize,
    pub primitive_id: usize,
    pub node_id: usize,
    pub geometry_id: usize,
}

#[derive(Clone, Copy)]
pub struct DepthBufferCell<A: Scalar, const L: usize> {
    pub pixinfo: [usize; L], // referencing pixel info per index
    pub depth: [A; L],
    // alternativelly, an array of tuple ? !
    //content: [(usize, A); L],
}

pub struct DrawBuffer<const L: usize, A: Number> {
    /// seems like this should be done that way ? R rows, C column , L depth layer, A ccurcy
    pub depthbuffer: Box<[DepthBufferCell<A, L>]>,
    pub canvas: Box<[CanvasCell]>,
    pub pixbuffer: Box<[PixInfo<A>]>,
    pub row_count: usize,
    pub col_count: usize,
}

#[derive(Clone, Copy)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

impl Color {
    pub fn copy_from(&mut self, rgba: &RGBA) {
        self.r = rgba.r;
        self.g = rgba.g;
        self.b = rgba.b;
        self.a = rgba.a;
    }
}

#[derive(Clone, Copy)]
pub struct CanvasCell {
    pub front_color: Color,
    pub back_color: Color,
    pub glyph: u8,
}

impl<D: Scalar, const L: usize> DepthBufferCell<D, L> {
    #[inline(always)]
    fn clear(&mut self, value: D, idx: usize) {
        for (layeridx, (d, p)) in self
            .depth
            .iter_mut()
            .zip(self.pixinfo.iter_mut())
            .enumerate()
        {
            *d = value;
            *p = idx + layeridx;
        }
    }

    fn set_init_pix_ref(&mut self, idx: usize) {
        for layer in 0..L {
            let lol = &mut (self.pixinfo[layer]);
            *(lol) = idx + layer
        }
    }

    fn roll_from(&mut self, index: usize) {
        if index >= L {
            return;
        }

        let slice = &mut self.pixinfo[index..];
        slice.rotate_left(1);

        let depth_slice = &mut self.depth[index..];
        depth_slice.rotate_left(1);
    }
}

impl<T: nalgebra_glm::Number> PixInfo<T> {
    fn clear(&mut self) {
        self.material_id = 0;
        self.primitive_id = 0;
        self.node_id = 0;
        self.geometry_id = 0;
    }

    // A is the "accuracy of the detph buffer, expect a f32 here"
    // could be a u8 for simple rendering engine; with flat 2D and layers
    // L is the layer count ; more layer means more potential material stacking effects
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

pub const DEPTH_BUFFER_CELL_INIT_F32_3L: DepthBufferCell<f32, 3> = DepthBufferCell {
    pixinfo: [0, 1, 2],
    depth: [0.1, 0.2, 0.3],
};
pub const DEPTH_BUFFER_CELL_INIT_F32_2L: DepthBufferCell<f32, 2> = DepthBufferCell {
    pixinfo: [0, 0],
    depth: [0.0, 0.0],
};

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

// here theL ( layer) are like.. bounded; A is accuracy of the depth buffer (f32 usually)
impl<const L: usize, A: Number> DrawBuffer<L, A> {
    pub fn new(
        row_count: usize,
        col_count: usize,
        default_depth: DepthBufferCell<A, L>,
        inipix: PixInfo<A>,
    ) -> Self {
        // this store the depth for every cell, for every "layer" + and index
        let mut depthbuffer = vec![default_depth; row_count * col_count].into_boxed_slice();

        // this store specific propertiees in RxCxL. The index inside the depth buffer is actually pointing into this
        // array.
        // reason is that we will often do "compare and move/swap"; by using the index I guess the swap is just "swaping u8, instead of swapping the whole struc";
        let pixbuffer = vec![inipix; row_count * col_count * L].into_boxed_slice();

        // we init the depth buffer with the pixel info.
        // each cell has L layers of depth,
        // and the info of the layers are within "pixbuffer"
        // the pix
        for row in 0..row_count {
            for col in 0..col_count {
                let idx = (row * col_count + col);

                (&mut depthbuffer[idx]).set_init_pix_ref(idx * L);
            }
        }

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
        for (idx, depth_cell) in self.depthbuffer.iter_mut().enumerate() {
            depth_cell.clear(value, idx * L);
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

    pub fn get_min_max_depth(&self, layer: usize) -> (A, A) {
        let mut min_value: A = A::max_value();
        let mut max_value: A = A::min_value();

        for depth_cell in self.depthbuffer.iter() {
            let content = depth_cell.depth[layer];

            if content < min_value {
                min_value = content;
            }
            if content > max_value {
                max_value = content;
            }
        }

        (min_value, max_value)
    }

    pub fn set_canvas_content(
        &mut self,
        r: usize,
        c: usize,
        front_color: Color,
        back_color: Color,
        glyph: u8,
    ) {
        let idx = r * self.col_count + c;
        let mut stuff = self.canvas[idx];
        stuff.front_color = front_color;
        stuff.back_color = back_color;
        stuff.glyph = glyph;
    }

    // will apply the material for every pixel.
    pub fn apply_material<const TEXTURESIZE: usize>(
        &mut self,
        material_buffer: &MaterialBuffer,
        texture_buffer: &TextureBuffer<TEXTURESIZE>,
    ) {
        for (depth_cell, canvascell) in self.depthbuffer.iter().zip(self.canvas.iter_mut()) {
            for depth_layer in (0..L).rev() {
                let pix_info = self.pixbuffer[depth_cell.pixinfo[depth_layer]];

                apply_material(material_buffer, texture_buffer, &pix_info, canvascell);
            }
        }
    }

    // The set_depth_content function is responsible for setting a new depth value into a
    // layered depth buffer while ensuring that the existing values are correctly shifted to
    // maintain the order.
    // This function updates both the depth buffer and the associated pixel information.
    pub fn set_depth_content(
        &mut self,
        row: usize,
        col: usize,
        depth: A,
        w: nalgebra_glm::TVec3<A>,
        w_alt: nalgebra_glm::TVec3<A>,
        node_id: usize,
        geom_id: usize,
        material_id: usize,
        primitive_id: usize,
    ) {
        let the_point = row * self.col_count + col;
        let mut the_layer = 0; // starting at layer 0

        let the_cell = &mut self.depthbuffer[the_point];
        while the_layer < L {
            let pix_info_at_layer = (self.pixbuffer[the_cell.pixinfo[the_layer]]);

            let depth_at_layer = the_cell.depth[the_layer];

            if pix_info_at_layer.geometry_id == geom_id {
                return; // We do not want to change anything if our own geometry has already set something at this location.
            } else if depth < depth_at_layer {
                // we are closer to this level of depth. So we can locate the new
                // value here.
                // the existing value need to be pushed "down the layers";
                // Like, if we currently set layer 1;
                // then the new value of the layer 2 is the previous layer1 ; the new of 3 is 2 etc.. :
                // like a shifting operation of +1 index.
                // the last element will be "droped" ; so we keep the pixel idx of the last layer before doing anything
                if the_layer + 1 < L {
                    let last_pix_index = the_cell.pixinfo[L - 1];
                    for moving_layer_idx in (the_layer + 1..L).rev() {
                        the_cell.pixinfo[moving_layer_idx] = the_cell.pixinfo[moving_layer_idx - 1];
                        the_cell.depth[moving_layer_idx] = the_cell.depth[moving_layer_idx - 1];
                    }

                    // now I grab the pix idx for me :)
                    the_cell.pixinfo[the_layer] = last_pix_index;

                    // and now I can set the content at the right location
                    let pix_info_dest = &mut (self.pixbuffer[last_pix_index]);
                    the_cell.depth[the_layer] = depth; // Set the depth
                    pix_info_dest.primitive_id = primitive_id;
                    pix_info_dest.geometry_id = geom_id;
                    pix_info_dest.node_id = node_id;
                    pix_info_dest.material_id = material_id;

                    // Store the vectors
                    pix_info_dest.w = w;
                    pix_info_dest.w_1 = w_alt;

                    return;
                } else {
                    // we are at the last layer. There is no way to push down anything; we just will replace.
                    the_cell.depth[the_layer] = depth; // Set the depth
                    let pix_info_dest = (self.pixbuffer[the_cell.pixinfo[the_layer]]).borrow_mut();
                    pix_info_dest.primitive_id = primitive_id;
                    pix_info_dest.geometry_id = geom_id;
                    pix_info_dest.node_id = node_id;
                    pix_info_dest.material_id = material_id;

                    // Store the vectors
                    pix_info_dest.w = w;
                    pix_info_dest.w_1 = w_alt;

                    return;
                }
            } else {
                the_layer += 1;
            }
        }
    }
}
