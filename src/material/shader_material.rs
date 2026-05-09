use nalgebra_glm::vec3;

use crate::{
    drawbuffer::drawbuffer::{CanvasCell, Color, DepthBufferCell, PixInfo},
    primitivbuffer::primitivbuffer::PrimitiveElements,
    texturebuffer::texture_buffer::TextureBuffer,
    ttsl::{decode_instrs_256, run_ttsl, Instr, Registers},
    vertexbuffer::uv_buffer::UVBuffer,
};

use super::materials::RenderMaterial;

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

    pub fn set_f32(&mut self, reg_id: usize, value: f32) {
        if reg_id < self.regs.f32_.len() {
            self.regs.f32_[reg_id] = value;
        }
    }

    pub fn get_f32(&self, reg_id: usize) -> f32 {
        if reg_id < self.regs.f32_.len() {
            self.regs.f32_[reg_id]
        } else {
            0.0
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
    pub uv_v3_reg: usize,
    pub uv1_v3_reg: usize,
    pub primitive_id_i32_reg: usize,
    pub material_id_i32_reg: usize,
    pub node_id_i32_reg: usize,
    pub geometry_id_i32_reg: usize,
    pub time_f32_reg: Option<usize>,
}

impl Default for ShaderInputBinding {
    fn default() -> Self {
        // Must match `RegisterAllocatorPass` in `python/tt3de/ttsl/compiler.py`: built-in
        // pixel vec2s are allocated V2 registers 1, 2, 3 in order for `tt_FragCoord`,
        // `tt_TexCoord0`, `tt_TexCoord1`. PixInfo UVs belong in the latter two slots.
        Self {
            uv_v2_reg: 2,
            uv1_v2_reg: 3,
            uv_v3_reg: 0,
            uv1_v3_reg: 1,
            primitive_id_i32_reg: 0,
            material_id_i32_reg: 1,
            node_id_i32_reg: 2,
            geometry_id_i32_reg: 3,
            time_f32_reg: None,
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

    pub fn set_time_seconds(&mut self, seconds: f32) {
        if let Some(reg_id) = self.input_binding.time_f32_reg {
            self.seed_regs.set_f32(reg_id, seconds);
        }
    }

    pub fn with_default_glyph(mut self, default_glyph: Option<u8>) -> Self {
        self.default_glyph = default_glyph;
        self
    }
}

impl<const TEXTURE_BUFFER_SIZE: usize, const DEPTHLAYER: usize>
    RenderMaterial<TEXTURE_BUFFER_SIZE, DEPTHLAYER> for ShaderMaterial
{
    fn render_mat(
        &self,
        cell: &mut CanvasCell,
        _depth_cell: &DepthBufferCell<f32, DEPTHLAYER>,
        _depth_layer: usize,
        pixinfo: &PixInfo<f32>,
        _primitive_element: &PrimitiveElements,
        _texture_buffer: &TextureBuffer<TEXTURE_BUFFER_SIZE>,
        _uv_buffer: &UVBuffer<f32>,
    ) {
        let mut regs = self.seed_regs.clone_registers();

        // Only write runtime-varying inputs used by the default shader bridge.
        let bind = self.input_binding;
        regs.v2[bind.uv_v2_reg] = pixinfo.uv;
        regs.v2[bind.uv1_v2_reg] = pixinfo.uv_1;
        regs.v3[bind.uv_v3_reg] = vec3(pixinfo.uv.x, pixinfo.uv.y, 0.0);
        regs.v3[bind.uv1_v3_reg] = vec3(pixinfo.uv_1.x, pixinfo.uv_1.y, 0.0);
        regs.i32_[bind.primitive_id_i32_reg] = pixinfo.primitive_id as i32;
        regs.i32_[bind.material_id_i32_reg] = pixinfo.material_id as i32;
        regs.i32_[bind.node_id_i32_reg] = pixinfo.node_id as i32;
        regs.i32_[bind.geometry_id_i32_reg] = pixinfo.geometry_id as i32;

        let (front, back, glyph) = run_ttsl(&self.instrs, &mut regs);
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
    }
}

#[cfg(test)]
mod tests {
    use nalgebra_glm::{vec2, vec3};

    use crate::{
        primitivbuffer::{primitiv_triangle::PTriangle3D, primitivbuffer::PrimitiveElements},
        texturebuffer::texture_buffer::TextureBuffer,
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
        pixinfo.material_id = 42;

        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);

        let shader = ShaderMaterial::from_bytecode(&[82, 0, 0, 1, 1, 0]);

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

        let shader = ShaderMaterial::from_bytecode(&[82, 0, 7, 7, 9, 0])
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
        let mut shader = ShaderMaterial::from_bytecode(&[82, 0, 0, 0, 0, 0]).with_time_f32_reg(Some(12));
        shader.set_time_seconds(3.25);
        assert_eq!(shader.seed_regs.get_f32(12), 3.25);
    }

    #[test]
    fn test_shader_material_default_glyph_is_used_when_vm_returns_zero() {
        let mut canvas_cell = CanvasCell::default();
        let depth_cell: DepthBufferCell<f32, 2> = DepthBufferCell::new();
        let pixinfo = PixInfo::new();
        let primitive_element = PrimitiveElements::Triangle3D(PTriangle3D::zero());
        let texture_buffer: TextureBuffer<16> = TextureBuffer::new(1);
        let uv_buffer: UVBuffer<f32> = UVBuffer::new(4);

        let shader = ShaderMaterial::from_bytecode(&[82, 0, 0, 0, 0, 0]).with_default_glyph(Some(219));
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
}
