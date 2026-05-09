use std::cell::RefCell;
use std::sync::atomic::{AtomicU64, Ordering};

use nalgebra_glm::{vec2, vec3, Vec2, Vec3};

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::texture_buffer::TextureBuffer,
    ttsl::{decode_instrs_256, run_ttsl, Instr, Registers},
    vertexbuffer::uv_buffer::UVBuffer,
};

use super::materials::RenderMaterial;

/// Incremented at the start of each full-buffer [`crate::drawbuffer::drawbuffer::apply_material_on`]
/// / [`crate::drawbuffer::drawbuffer::apply_material_on_parallel`] pass so thread-local shader register
/// caches do not reuse state across passes (e.g. after seed/uniform updates).
static MATERIAL_APPLY_GENERATION: AtomicU64 = AtomicU64::new(0);

pub(super) fn bump_material_apply_generation() {
    MATERIAL_APPLY_GENERATION.fetch_add(1, Ordering::AcqRel);
}

#[derive(Clone)]
pub struct ShaderMaterial {
    pub instrs: [Instr; 256],
    pub seed_regs: ShaderSeedRegisters,
    pub input_binding: ShaderInputBinding,
    pub default_glyph: Option<u8>,
}

#[derive(Clone)]
pub struct ShaderSeedRegisters {
    regs: Registers,
}

impl ShaderSeedRegisters {
    pub fn new() -> Self {
        Self {
            regs: Registers::new(),
        }
    }

    pub fn from_registers(regs: Registers) -> Self {
        Self { regs }
    }

    pub fn clone_registers(&self) -> Registers {
        self.regs.clone()
    }

    /// Copies the seed register banks into `dst` (same effect as assigning `clone_registers()`).
    pub fn copy_seed_into(&self, dst: &mut Registers) {
        dst.clone_from(&self.regs);
    }

    pub fn set_f32(&mut self, reg_id: usize, value: f32) {
        if reg_id < self.regs.f32_.len() {
            self.regs.f32_[reg_id] = value;
        }
    }

    pub fn set_v3(&mut self, reg_id: usize, value: Vec3) {
        if reg_id < self.regs.v3.len() {
            self.regs.v3[reg_id] = value;
        }
    }

    pub fn get_f32(&self, reg_id: usize) -> f32 {
        if reg_id < self.regs.f32_.len() {
            self.regs.f32_[reg_id]
        } else {
            0.0
        }
    }

    pub fn set_i32(&mut self, reg_id: usize, value: i32) {
        if reg_id < self.regs.i32_.len() {
            self.regs.i32_[reg_id] = value;
        }
    }

    pub fn get_i32(&self, reg_id: usize) -> i32 {
        if reg_id < self.regs.i32_.len() {
            self.regs.i32_[reg_id]
        } else {
            0
        }
    }

    pub fn set_v2(&mut self, reg_id: usize, value: Vec2) {
        if reg_id < self.regs.v2.len() {
            self.regs.v2[reg_id] = value;
        }
    }

    pub fn get_v2(&self, reg_id: usize) -> Vec2 {
        if reg_id < self.regs.v2.len() {
            self.regs.v2[reg_id]
        } else {
            Vec2::zeros()
        }
    }
}

impl Default for ShaderSeedRegisters {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy)]
pub struct ShaderInputBinding {
    pub uv_v2_reg: usize,
    pub uv1_v2_reg: usize,
    pub fragpos_v2_reg: usize,
    pub uv_v3_reg: usize,
    pub uv1_v3_reg: usize,
    pub primitive_id_i32_reg: usize,
    pub material_id_i32_reg: usize,
    pub node_id_i32_reg: usize,
    pub geometry_id_i32_reg: usize,
    pub time_f32_reg: Option<usize>,
    /// Register for ``tt_DeltaTime`` (``float``, seconds); updated via seed only — not per pixel.
    pub delta_time_f32_reg: Option<usize>,
    /// Register for ``tt_Frame`` (``int``); updated via seed only — not per pixel.
    pub frame_i32_reg: Option<usize>,
    /// Register index for ``tt_Resolution`` (``glm.vec2`` uniform); updated via seed only — not per pixel.
    pub resolution_v2_reg: Option<usize>,
    /// Register for ``tt_FrontFacing`` (``bool``); updated from ``PixInfo::front_facing`` each pixel.
    pub front_facing_bool_reg: Option<usize>,
    /// Register for ``tt_FragDepth`` (``float``); updated from the active depth layer each pixel.
    pub frag_depth_f32_reg: Option<usize>,
    /// Register for ``tt_LineCoord`` (``float``, typically \[0, 1\] along rasterized lines).
    pub line_coord_f32_reg: Option<usize>,
    /// Register for ``tt_PointCoord`` (``vec2``, typically \[0, 1\] within a point sprite).
    pub point_coord_v2_reg: Option<usize>,
}

impl Default for ShaderInputBinding {
    fn default() -> Self {
        // Must match `RegisterAllocatorPass` in `python/tt3de/ttsl/compiler.py`: built-in
        // pixel vec2s are allocated V2 registers 1..=5 in order for `tt_FragCoord`,
        // `tt_TexCoord0`, `tt_TexCoord1`, `tt_FragPos`, `tt_PointCoord`. PixInfo UVs belong in registers 2–3;
        // `tt_FragPos` is filled from `PixInfo::frag_pos` (see `DrawBuffer::set_depth_content`).
        // `tt_PrimitiveID` is pinned by the allocator to `regs.i32_[0]`; the remaining PixInfo
        // i32 IDs (material_id / node_id / geometry_id) are not yet TTSL-named and live in the
        // i32 indices the allocator reserves (1..=3) so they cannot alias user temps.
        Self {
            uv_v2_reg: 2,
            uv1_v2_reg: 3,
            fragpos_v2_reg: 4,
            // Must stay aligned with `RegisterAllocatorPass` in `compiler.py`, which skips
            // these `v3` indices so TTSL temps cannot collide before `render_mat` fills UVs.
            uv_v3_reg: 0,
            uv1_v3_reg: 1,
            primitive_id_i32_reg: 0,
            material_id_i32_reg: 1,
            node_id_i32_reg: 2,
            geometry_id_i32_reg: 3,
            time_f32_reg: None,
            delta_time_f32_reg: None,
            frame_i32_reg: None,
            resolution_v2_reg: None,
            front_facing_bool_reg: None,
            frag_depth_f32_reg: None,
            line_coord_f32_reg: None,
            point_coord_v2_reg: None,
        }
    }
}

pub(crate) fn write_per_pixel_inputs_to_registers<const DEPTHLAYER: usize>(
    bind: &ShaderInputBinding,
    pixinfo: &PixInfo<f32>,
    depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
    depth_layer: usize,
    regs: &mut Registers,
) {
    regs.v2[bind.uv_v2_reg] = pixinfo.uv;
    regs.v2[bind.uv1_v2_reg] = pixinfo.uv_1;
    regs.v2[bind.fragpos_v2_reg] = pixinfo.frag_pos;
    regs.v3[bind.uv_v3_reg] = vec3(pixinfo.uv.x, pixinfo.uv.y, 0.0);
    regs.v3[bind.uv1_v3_reg] = vec3(pixinfo.uv_1.x, pixinfo.uv_1.y, 0.0);
    regs.i32_[bind.primitive_id_i32_reg] = pixinfo.primitive_id as i32;
    regs.i32_[bind.material_id_i32_reg] = pixinfo.material_id as i32;
    regs.i32_[bind.node_id_i32_reg] = pixinfo.node_id as i32;
    regs.i32_[bind.geometry_id_i32_reg] = pixinfo.geometry_id as i32;
    if let Some(reg_id) = bind.front_facing_bool_reg {
        if reg_id < regs.bool_.len() {
            regs.bool_[reg_id] = pixinfo.front_facing;
        }
    }
    if let Some(reg_id) = bind.frag_depth_f32_reg {
        if reg_id < regs.f32_.len() && depth_layer < DEPTHLAYER {
            regs.f32_[reg_id] = depth_cell.depth[depth_layer];
        }
    }
    if let Some(reg_id) = bind.line_coord_f32_reg {
        if reg_id < regs.f32_.len() {
            regs.f32_[reg_id] = pixinfo.line_coord;
        }
    }
    if let Some(reg_id) = bind.point_coord_v2_reg {
        if reg_id < regs.v2.len() {
            regs.v2[reg_id] = pixinfo.point_coord;
        }
    }
}

impl ShaderMaterial {
    pub fn new(instrs: [Instr; 256]) -> Self {
        Self {
            instrs,
            seed_regs: ShaderSeedRegisters::default(),
            input_binding: ShaderInputBinding::default(),
            default_glyph: None,
        }
    }

    pub fn from_bytecode(bytecode: &[u8]) -> Self {
        Self::new(decode_instrs_256(bytecode))
    }

    pub fn with_seed_registers(mut self, seed_regs: ShaderSeedRegisters) -> Self {
        self.seed_regs = seed_regs;
        self
    }

    pub fn with_input_binding(mut self, input_binding: ShaderInputBinding) -> Self {
        self.input_binding = input_binding;
        self
    }

    pub fn with_time_f32_reg(mut self, time_f32_reg: Option<usize>) -> Self {
        self.input_binding.time_f32_reg = time_f32_reg;
        self
    }

    pub fn with_delta_time_f32_reg(mut self, delta_time_f32_reg: Option<usize>) -> Self {
        self.input_binding.delta_time_f32_reg = delta_time_f32_reg;
        self
    }

    pub fn with_frame_i32_reg(mut self, frame_i32_reg: Option<usize>) -> Self {
        self.input_binding.frame_i32_reg = frame_i32_reg;
        self
    }

    pub fn with_resolution_v2_reg(mut self, resolution_v2_reg: Option<usize>) -> Self {
        self.input_binding.resolution_v2_reg = resolution_v2_reg;
        self
    }

    pub fn with_front_facing_bool_reg(mut self, front_facing_bool_reg: Option<usize>) -> Self {
        self.input_binding.front_facing_bool_reg = front_facing_bool_reg;
        self
    }

    pub fn with_frag_depth_f32_reg(mut self, frag_depth_f32_reg: Option<usize>) -> Self {
        self.input_binding.frag_depth_f32_reg = frag_depth_f32_reg;
        self
    }

    pub fn with_line_coord_f32_reg(mut self, line_coord_f32_reg: Option<usize>) -> Self {
        self.input_binding.line_coord_f32_reg = line_coord_f32_reg;
        self
    }

    pub fn with_point_coord_v2_reg(mut self, point_coord_v2_reg: Option<usize>) -> Self {
        self.input_binding.point_coord_v2_reg = point_coord_v2_reg;
        self
    }

    pub fn set_time_seconds(&mut self, seconds: f32) {
        if let Some(reg_id) = self.input_binding.time_f32_reg {
            self.seed_regs.set_f32(reg_id, seconds);
        }
    }

    pub fn set_delta_time_seconds(&mut self, dt_seconds: f32) {
        if let Some(reg_id) = self.input_binding.delta_time_f32_reg {
            self.seed_regs.set_f32(reg_id, dt_seconds);
        }
    }

    pub fn set_frame_counter(&mut self, frame: u32) {
        let value = frame.min(i32::MAX as u32) as i32;
        if let Some(reg_id) = self.input_binding.frame_i32_reg {
            self.seed_regs.set_i32(reg_id, value);
        }
    }

    /// Writes ``tt_Resolution`` as ``(width_cells, height_cells)``. Non-positive components become ``1.0``
    /// (engine default aspect until the host sets a real buffer size).
    pub fn set_resolution_cells(&mut self, width_cells: f32, height_cells: f32) {
        let w = if width_cells > 0.0 { width_cells } else { 1.0 };
        let h = if height_cells > 0.0 { height_cells } else { 1.0 };
        if let Some(reg_id) = self.input_binding.resolution_v2_reg {
            self.seed_regs.set_v2(reg_id, vec2(w, h));
        }
    }

    pub fn with_default_glyph(mut self, default_glyph: Option<u8>) -> Self {
        self.default_glyph = default_glyph;
        self
    }
}

/// Thread-local TTSL register scratch + cache key for skipping redundant seed copies.
///
/// After each [`run_ttsl`], we [`ShaderSeedRegisters::copy_seed_into`] the TLS buffer again so the
/// VM’s clobbered registers do not leak into the next pixel. When the next invocation targets the
/// same `(material_id, ShaderMaterial)` as the previous one on this OS thread **within the same
/// apply generation**, we can skip the initial seed reload and only patch per-pixel inputs.
struct ShaderRenderTls {
    apply_generation: u64,
    last_shader_bits: usize,
    last_material_id: usize,
    regs: Registers,
}

impl ShaderRenderTls {
    fn new() -> Self {
        Self {
            apply_generation: u64::MAX,
            last_shader_bits: 0,
            last_material_id: usize::MAX,
            regs: Registers::new(),
        }
    }

    fn sync_apply_generation(&mut self) {
        let g = MATERIAL_APPLY_GENERATION.load(Ordering::Relaxed);
        if self.apply_generation != g {
            self.apply_generation = g;
            self.last_shader_bits = 0;
            self.last_material_id = usize::MAX;
        }
    }
}

thread_local! {
    static SHADER_RENDER_TLS: RefCell<ShaderRenderTls> = RefCell::new(ShaderRenderTls::new());
}

/// Clears the `(shader, material_id)` TLS fast-path key so the next [`ShaderMaterial::render_mat`]
/// reloads the seed. Used in tests; production relies on [`bump_material_apply_generation`] each pass.
#[cfg(test)]
pub(super) fn test_only_force_tls_shader_cache_miss() {
    SHADER_RENDER_TLS.with(|tls| {
        let mut t = tls.borrow_mut();
        t.last_shader_bits = 0;
        t.last_material_id = usize::MAX;
    });
}

impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize>
    RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for ShaderMaterial
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<f32>,
    ) {
        let self_bits = self as *const ShaderMaterial as usize;
        let material_id = pixinfo.material_id;

        SHADER_RENDER_TLS.with(|tls| {
            let mut t = tls.borrow_mut();
            t.sync_apply_generation();

            let cache_hit =
                t.last_shader_bits == self_bits && t.last_material_id == material_id;
            if !cache_hit {
                self.seed_regs.copy_seed_into(&mut t.regs);
                t.last_shader_bits = self_bits;
                t.last_material_id = material_id;
            }

            let bind = self.input_binding;
            let regs = &mut t.regs;
            write_per_pixel_inputs_to_registers(&bind, pixinfo, depth_cell, depth_layer, regs);

            let (front, back, glyph) =
                run_ttsl(&self.instrs, regs, Some(texture_buffer as &dyn crate::ttsl::TtslTextureEnv));
            cell.front_color = Color::new_opaque_from_vec3(&front);
            cell.back_color = Color::new_opaque_from_vec3(&back);
            if glyph == 0 {
                if let Some(default_glyph) = self.default_glyph {
                    cell.glyph = default_glyph;
                } else {
                    cell.glyph = 0;
                }
            } else {
                cell.glyph = glyph.clamp(0, 255) as u8;
            }

            // Restore seed snapshot so a cache hit on the next invocation starts from correct banks.
            self.seed_regs.copy_seed_into(regs);
        });
    }
}

#[cfg(test)]
mod tests {
    use nalgebra_glm::{vec2, vec3};

    use crate::{
        drawbuffer::drawbuffer::PixInfo,
        primitivbuffer::{primitiv_triangle::PTriangle3D, primitivbuffer::PrimitiveElements},
        texturebuffer::texture_buffer::TextureBuffer,
        ttsl::Registers,
        vertexbuffer::uv_buffer::UVBuffer,
    };

    use super::*;

    #[test]
    fn test_shader_material_writes_front_back_and_glyph() {
        let mut canvas_cell = CanvasCell::default();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let mut pixinfo = PixInfo::new();
        pixinfo.set_uv(vec2(0.5, 0.25));
        pixinfo.set_uv_1(vec2(0.25, 0.75));
        // Bytecode reads glyph from i32 reg 1, which is the ``material_id`` shadow slot in
        // ``ShaderInputBinding::default()`` (``tt_PrimitiveID`` lives in i32 reg 0).
        pixinfo.material_id = 42;

        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);

        let shader = ShaderMaterial::from_bytecode(&[83, 0, 0, 1, 1, 0]);

        shader.render_mat(
            &mut canvas_cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(canvas_cell.front_color, Color::new(128, 64, 0, 255));
        assert_eq!(canvas_cell.back_color, Color::new(64, 192, 0, 255));
        assert_eq!(canvas_cell.glyph, 42);
    }

    #[test]
    fn test_shader_material_uses_seed_registers() {
        let mut canvas_cell = CanvasCell::default();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let pixinfo = PixInfo::new();

        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);

        let mut regs = Registers::new();
        regs.v3[7] = vec3(0.2, 0.4, 0.6);
        regs.i32_[9] = 99;

        let shader = ShaderMaterial::from_bytecode(&[83, 0, 7, 7, 9, 0])
            .with_seed_registers(ShaderSeedRegisters::from_registers(regs));

        shader.render_mat(
            &mut canvas_cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(canvas_cell.front_color, Color::new(51, 102, 153, 255));
        assert_eq!(canvas_cell.back_color, Color::new(51, 102, 153, 255));
        assert_eq!(canvas_cell.glyph, 99);
    }

    #[test]
    fn test_shader_material_time_uniform_setter_updates_seed_register() {
        let mut shader = ShaderMaterial::from_bytecode(&[83, 0, 0, 0, 0, 0]).with_time_f32_reg(Some(12));
        shader.set_time_seconds(3.25);
        assert_eq!(shader.seed_regs.get_f32(12), 3.25);
    }

    #[test]
    fn test_shader_material_delta_time_uniform_setter_updates_seed_register() {
        let mut shader =
            ShaderMaterial::from_bytecode(&[83, 0, 0, 0, 0, 0]).with_delta_time_f32_reg(Some(11));
        shader.set_delta_time_seconds(1.0 / 60.0);
        assert_eq!(shader.seed_regs.get_f32(11), 1.0 / 60.0);
    }

    #[test]
    fn test_shader_material_frame_uniform_setter_updates_seed_register() {
        let mut shader =
            ShaderMaterial::from_bytecode(&[83, 0, 0, 0, 0, 0]).with_frame_i32_reg(Some(6));
        shader.set_frame_counter(42);
        assert_eq!(shader.seed_regs.get_i32(6), 42);
        shader.set_frame_counter(u32::MAX);
        assert_eq!(shader.seed_regs.get_i32(6), i32::MAX);
    }

    #[test]
    fn test_shader_material_resolution_uniform_setter_updates_seed_register() {
        let mut shader =
            ShaderMaterial::from_bytecode(&[83, 0, 0, 0, 0, 0]).with_resolution_v2_reg(Some(7));
        shader.set_resolution_cells(80.0, 24.0);
        assert_eq!(shader.seed_regs.get_v2(7), vec2(80.0, 24.0));
        shader.set_resolution_cells(0.0, -5.0);
        assert_eq!(shader.seed_regs.get_v2(7), vec2(1.0, 1.0));
    }

    #[test]
    fn test_write_per_pixel_inputs_writes_primitive_id_to_default_i32_reg_zero() {
        // `ShaderInputBinding::default()` mirrors the TTSL `RegisterAllocatorPass`, which
        // pins `tt_PrimitiveID` to i32 reg 0 (explicit allocator special-case in
        // `compiler.py`); `material_id` lives in the adjacent reserved shadow slot at i32 reg 1.
        let bind = ShaderInputBinding::default();
        assert_eq!(bind.primitive_id_i32_reg, 0);
        assert_eq!(bind.material_id_i32_reg, 1);

        let mut pixinfo = PixInfo::new();
        pixinfo.primitive_id = 42;
        pixinfo.material_id = 7;
        let mut regs = Registers::new();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 0, &mut regs);
        assert_eq!(regs.i32_[bind.primitive_id_i32_reg], 42);
        assert_eq!(regs.i32_[bind.material_id_i32_reg], 7);
    }

    #[test]
    fn test_write_per_pixel_inputs_sets_tt_front_facing_register() {
        let bind = ShaderInputBinding {
            front_facing_bool_reg: Some(14),
            ..ShaderInputBinding::default()
        };
        let mut pixinfo = PixInfo::new();
        pixinfo.front_facing = false;
        let mut regs = Registers::new();
        regs.bool_[14] = true;
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 0, &mut regs);
        assert!(!regs.bool_[14]);

        pixinfo.front_facing = true;
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 0, &mut regs);
        assert!(regs.bool_[14]);
    }

    #[test]
    fn test_write_per_pixel_inputs_sets_tt_frag_depth_register() {
        let bind = ShaderInputBinding {
            frag_depth_f32_reg: Some(5),
            ..ShaderInputBinding::default()
        };
        let mut depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        depth_cell.depth[0] = 0.375;
        depth_cell.depth[1] = 0.625;
        let pixinfo = PixInfo::new();
        let mut regs = Registers::new();
        regs.f32_[5] = -1.0;
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 0, &mut regs);
        assert_eq!(regs.f32_[5], 0.375);
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 1, &mut regs);
        assert_eq!(regs.f32_[5], 0.625);
    }

    #[test]
    fn test_write_per_pixel_inputs_sets_tt_line_coord_register() {
        let bind = ShaderInputBinding {
            line_coord_f32_reg: Some(6),
            ..ShaderInputBinding::default()
        };
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let mut pixinfo = PixInfo::new();
        pixinfo.line_coord = 0.625;
        let mut regs = Registers::new();
        regs.f32_[6] = -1.0;
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 0, &mut regs);
        assert_eq!(regs.f32_[6], 0.625);
    }

    #[test]
    fn test_write_per_pixel_inputs_sets_tt_point_coord_register() {
        let bind = ShaderInputBinding {
            point_coord_v2_reg: Some(7),
            ..ShaderInputBinding::default()
        };
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let mut pixinfo = PixInfo::new();
        pixinfo.point_coord = vec2(0.25, 0.75);
        let mut regs = Registers::new();
        regs.v2[7] = vec2(-1.0, -1.0);
        super::write_per_pixel_inputs_to_registers(&bind, &pixinfo, &depth_cell, 0, &mut regs);
        assert_eq!(regs.v2[7], vec2(0.25, 0.75));
    }

    #[test]
    fn test_shader_material_default_glyph_is_used_when_vm_returns_zero() {
        let mut canvas_cell = CanvasCell::default();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let pixinfo = PixInfo::new();
        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);

        let shader = ShaderMaterial::from_bytecode(&[83, 0, 0, 0, 0, 0]).with_default_glyph(Some(219));
        shader.render_mat(
            &mut canvas_cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );
        assert_eq!(canvas_cell.glyph, 219);
    }

    /// Two consecutive invocations on the same OS thread with the same `(shader, material_id)`
    /// must still apply the second pixel's inputs (TLS fast path after post-VM seed restore).
    #[test]
    fn test_shader_material_tls_cache_preserves_per_pixel_inputs() {
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);
        let shader = ShaderMaterial::from_bytecode(&[83, 0, 0, 1, 1, 0]);

        let mut pix_a = PixInfo::new();
        pix_a.set_uv(vec2(0.5, 0.25));
        pix_a.set_uv_1(vec2(0.25, 0.75));
        pix_a.material_id = 1;

        let mut pix_b = PixInfo::new();
        pix_b.set_uv(vec2(0.9, 0.1));
        pix_b.set_uv_1(vec2(0.1, 0.9));
        pix_b.material_id = 1;

        let mut cell_a = CanvasCell::default();
        let mut cell_b = CanvasCell::default();
        shader.render_mat(
            &mut cell_a,
            &depth_cell,
            0,
            &pix_a,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );
        shader.render_mat(
            &mut cell_b,
            &depth_cell,
            0,
            &pix_b,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );

        assert_eq!(cell_a.front_color, Color::new(128, 64, 0, 255));
        assert_eq!(cell_a.back_color, Color::new(64, 192, 0, 255));
        assert_eq!(cell_a.glyph, 1);

        assert_eq!(cell_b.front_color, Color::new(230, 25, 0, 255));
        assert_eq!(cell_b.back_color, Color::new(25, 230, 0, 255));
        assert_eq!(cell_b.glyph, 1);
    }

    /// TLS seed cache must miss after uniforms change. Production relies on
    /// [`super::bump_material_apply_generation`] each full-buffer apply; here we force a miss with
    /// [`super::test_only_force_tls_shader_cache_miss`] (parallel unit tests share a global generation
    /// counter and would race otherwise).
    #[test]
    fn test_tls_seed_cache_miss_sees_updated_uniforms() {
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let pixinfo = PixInfo::new();
        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);

        let mut regs = Registers::new();
        regs.v3[7] = vec3(0.2, 0.4, 0.6);
        regs.i32_[9] = 99;
        let mut shader =
            ShaderMaterial::from_bytecode(&[83, 0, 7, 7, 9, 0]).with_seed_registers(
                ShaderSeedRegisters::from_registers(regs),
            );

        let mut cell = CanvasCell::default();
        shader.render_mat(
            &mut cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );
        let first = cell.front_color;
        assert_eq!(first, Color::new(51, 102, 153, 255));

        shader.seed_regs.set_v3(7, vec3(0.0, 1.0, 0.0));
        shader.render_mat(
            &mut cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );
        assert_eq!(first, cell.front_color);

        super::test_only_force_tls_shader_cache_miss();
        shader.render_mat(
            &mut cell,
            &depth_cell,
            0,
            &pixinfo,
            &primitive_element,
            &texture_buffer,
            &uv_buffer,
        );
        assert_eq!(cell.front_color, Color::new(0, 255, 0, 255));
    }
}
