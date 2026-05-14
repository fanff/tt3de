use pyo3::prelude::*;

use pyo3::{
    exceptions::PyValueError,
    pyclass, pymethods,
    types::{PyBytes, PyDict, PyList},
    Bound, Py, PyResult, Python,
};

use crate::drawbuffer::blend::{BlendMode, GlyphPolicy};
use crate::material::materials::Material;
use crate::material::shader_material::{ShaderMaterial, ShaderSeedRegisters};
use crate::ttsl::{ttslpy::convert_and_fill_register, Registers};
use crate::material::textured::BaseTexture;
use crate::texturebuffer;
use crate::texturebuffer::toglyph_methods_py::ToGlyphMethodPy;

fn parse_blend_mode(input: &str) -> PyResult<BlendMode> {
    match input {
        "replace" => Ok(BlendMode::Replace),
        "alpha_blend" => Ok(BlendMode::AlphaBlend),
        "additive" => Ok(BlendMode::Additive),
        "glyph_dither" => Ok(BlendMode::GlyphDither),
        "half_block_composite" => Ok(BlendMode::HalfBlockComposite),
        _ => Err(PyValueError::new_err(
            "blend_mode must be one of: replace, alpha_blend, additive, glyph_dither, half_block_composite",
        )),
    }
}

fn blend_mode_to_str(mode: BlendMode) -> &'static str {
    match mode {
        BlendMode::Replace => "replace",
        BlendMode::AlphaBlend => "alpha_blend",
        BlendMode::Additive => "additive",
        BlendMode::GlyphDither => "glyph_dither",
        BlendMode::HalfBlockComposite => "half_block_composite",
    }
}

fn parse_glyph_policy(input: &str) -> PyResult<GlyphPolicy> {
    match input {
        "preserve_existing" => Ok(GlyphPolicy::PreserveExisting),
        "replace_from_shader" => Ok(GlyphPolicy::ReplaceFromShader),
        _ => Err(PyValueError::new_err(
            "glyph_policy must be one of: preserve_existing, replace_from_shader",
        )),
    }
}

fn glyph_policy_to_str(policy: GlyphPolicy) -> &'static str {
    match policy {
        GlyphPolicy::PreserveExisting => "preserve_existing",
        GlyphPolicy::ReplaceFromShader => "replace_from_shader",
    }
}

#[pyclass(subclass)]
#[derive(Clone)]
pub struct MaterialPy {}
#[pymethods]
impl MaterialPy {
    #[new]
    pub fn new() -> Self {
        MaterialPy {}
    }
}
impl MaterialPy {
    pub fn to_native(_py: Python, _mat: &MaterialPy) -> Material {
        Material::DoNothing {}
    }
}

#[pyclass(extends=MaterialPy)]
#[derive(Clone)]
pub struct BaseTexturePy {
    #[pyo3(get, set)]
    pub albedo_texture_idx: usize,
    #[pyo3(get, set)]
    pub albedo_texture_subid: usize,
    #[pyo3(get, set)]
    pub glyph_texture_idx: usize,
    #[pyo3(get, set)]
    pub glyph_texture_subid: usize,

    #[pyo3(get, set)]
    pub front: bool,
    #[pyo3(get, set)]
    pub back: bool,
    #[pyo3(get, set)]
    pub glyph: bool,
    #[pyo3(get, set)]
    pub glyph_uv_0: bool,

    #[pyo3(get, set)]
    pub front_uv_0: bool,
    #[pyo3(get, set)]
    pub back_uv_0: bool,
    #[pyo3(get, set)]
    pub glyph_method: ToGlyphMethodPy,
    blend_mode: BlendMode,
    glyph_policy: GlyphPolicy,
}
impl BaseTexturePy {
    pub fn to_native(&self) -> BaseTexture {
        BaseTexture {
            albedo_texture_idx: self.albedo_texture_idx,
            albedo_texture_subid: self.albedo_texture_subid,
            glyph_texture_idx: self.glyph_texture_idx,
            glyph_texture_subid: self.glyph_texture_subid,
            front: self.front,
            back: self.back,
            glyph: self.glyph,
            front_uv_0: self.front_uv_0,
            back_uv_0: self.back_uv_0,
            glyph_uv_0: self.glyph_uv_0,
            to_glyph_method: self.glyph_method.to_method(), //self.glyph_method.to_method(),
            blend_mode: self.blend_mode,
            glyph_policy: self.glyph_policy,
        }
    }
}
#[pymethods]
impl BaseTexturePy {
    #[new]
    #[pyo3(signature = (albedo_texture_idx=0, albedo_texture_subid=0, glyph_texture_idx=0, glyph_texture_subid=0, front=true, back=true, glyph=true, front_uv_0=true, back_uv_0=true, glyph_uv_0=true, glyph_method=None, blend_mode=None, glyph_policy=None))]
    fn new(
        albedo_texture_idx: usize,
        albedo_texture_subid: usize,
        glyph_texture_idx: usize,
        glyph_texture_subid: usize,
        front: bool,
        back: bool,
        glyph: bool,
        front_uv_0: bool,
        back_uv_0: bool,
        glyph_uv_0: bool,
        glyph_method: Option<ToGlyphMethodPy>,
        blend_mode: Option<&str>,
        glyph_policy: Option<&str>,
    ) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        let blend_mode = blend_mode
            .map(parse_blend_mode)
            .transpose()
            .unwrap_or(None)
            .unwrap_or(BlendMode::Replace);
        let glyph_policy = glyph_policy
            .map(parse_glyph_policy)
            .transpose()
            .unwrap_or(None)
            .unwrap_or(GlyphPolicy::PreserveExisting);
        let glyph_method = match glyph_method {
            Some(gm) => gm,
            None => ToGlyphMethodPy {
                met_id: 0,
                glyph_idx: 0,
                glyph_set: (0, 0, 0, 0),
            },
        };
        PyClassInitializer::from(parent).add_subclass(BaseTexturePy {
            albedo_texture_idx,
            albedo_texture_subid,
            glyph_texture_idx,
            glyph_texture_subid,
            front,
            back,
            glyph,
            front_uv_0,
            back_uv_0,
            glyph_uv_0,
            glyph_method: glyph_method,
            blend_mode,
            glyph_policy,
        })
    }

    #[getter]
    fn blend_mode(&self) -> String {
        blend_mode_to_str(self.blend_mode).to_string()
    }

    #[setter]
    fn set_blend_mode(&mut self, value: &str) -> PyResult<()> {
        self.blend_mode = parse_blend_mode(value)?;
        Ok(())
    }

    #[getter]
    fn glyph_policy(&self) -> String {
        glyph_policy_to_str(self.glyph_policy).to_string()
    }

    #[setter]
    fn set_glyph_policy(&mut self, value: &str) -> PyResult<()> {
        self.glyph_policy = parse_glyph_policy(value)?;
        Ok(())
    }
}

#[pyclass(extends=MaterialPy)]
#[derive(Clone)]
pub struct StaticColorPy {
    #[pyo3(get, set)]
    pub front: bool,
    #[pyo3(get, set)]
    pub back: bool,
    #[pyo3(get, set)]
    pub glyph: bool,

    #[pyo3(get, set)]
    pub front_color: (u8, u8, u8, u8),
    #[pyo3(get, set)]
    pub back_color: (u8, u8, u8, u8),

    #[pyo3(get, set)]
    glyph_idx: u8,
    blend_mode: BlendMode,
    glyph_policy: GlyphPolicy,
}

#[pymethods]
impl StaticColorPy {
    #[new]
    #[pyo3(signature = (front, back, glyph, front_color, back_color, glyph_idx, blend_mode=None, glyph_policy=None))]
    fn new(
        front: bool,
        back: bool,
        glyph: bool,
        front_color: (u8, u8, u8, u8),
        back_color: (u8, u8, u8, u8),
        glyph_idx: u8,
        blend_mode: Option<&str>,
        glyph_policy: Option<&str>,
    ) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        let blend_mode = blend_mode
            .map(parse_blend_mode)
            .transpose()
            .unwrap_or(None)
            .unwrap_or(BlendMode::Replace);
        let glyph_policy = glyph_policy
            .map(parse_glyph_policy)
            .transpose()
            .unwrap_or(None)
            .unwrap_or(GlyphPolicy::PreserveExisting);
        PyClassInitializer::from(parent).add_subclass(StaticColorPy {
            front,
            back,
            glyph,
            front_color,
            back_color,
            glyph_idx,
            blend_mode,
            glyph_policy,
        })
    }
}
impl StaticColorPy {
    pub fn to_native(&self) -> Material {
        Material::StaticColor {
            front: self.front,
            back: self.back,
            glyph: self.glyph,
            front_color: texturebuffer::RGBA {
                r: self.front_color.0,
                g: self.front_color.1,
                b: self.front_color.2,
                a: self.front_color.3,
            },
            back_color: texturebuffer::RGBA {
                r: self.back_color.0,
                g: self.back_color.1,
                b: self.back_color.2,
                a: self.back_color.3,
            },
            glyph_idx: self.glyph_idx,
            blend_mode: self.blend_mode,
            glyph_policy: self.glyph_policy,
        }
    }
}

#[pyclass(extends=MaterialPy)]
pub struct ShaderPy {
    pub bytecode: Vec<u8>,
    pub time_f32_reg: Option<usize>,
    pub delta_time_f32_reg: Option<usize>,
    pub frame_i32_reg: Option<usize>,
    pub resolution_v2_reg: Option<usize>,
    pub near_f32_reg: Option<usize>,
    pub far_f32_reg: Option<usize>,
    pub front_facing_bool_reg: Option<usize>,
    pub frag_depth_f32_reg: Option<usize>,
    pub line_coord_f32_reg: Option<usize>,
    pub point_coord_v2_reg: Option<usize>,
    pub default_glyph: Option<u8>,
    pub blend_mode: BlendMode,
    pub glyph_policy: GlyphPolicy,
    /// Same layout as ``RegisterSettings.get_register_list()`` (list of 6 dicts), or ``None``.
    #[pyo3(get, set)]
    pub register_seed: Option<Py<PyAny>>,
}

impl ShaderPy {
    pub fn build_native(&self, py: Python<'_>) -> PyResult<ShaderMaterial> {
        let seed_registers: Option<Registers> = if let Some(seed) = &self.register_seed {
            let seq = seed.bind(py);
            let list = seq.cast::<PyList>().map_err(|_| {
                PyValueError::new_err("register_seed must be a list of 6 dicts")
            })?;
            if list.len() != 6 {
                return Err(PyValueError::new_err(
                    "register_seed must be a sequence of exactly 6 dicts (bool, f32, i32, v2, v3, v4 banks)",
                ));
            }
            let mut regs = Registers::new();
            let d0: Py<PyDict> = list.get_item(0)?.extract()?;
            let d1: Py<PyDict> = list.get_item(1)?.extract()?;
            let d2: Py<PyDict> = list.get_item(2)?.extract()?;
            let d3: Py<PyDict> = list.get_item(3)?.extract()?;
            let d4: Py<PyDict> = list.get_item(4)?.extract()?;
            let d5: Py<PyDict> = list.get_item(5)?.extract()?;
            convert_and_fill_register(
                &mut regs,
                d0.clone_ref(py),
                d1.clone_ref(py),
                d2.clone_ref(py),
                d3.clone_ref(py),
                d4.clone_ref(py),
                d5.clone_ref(py),
                py,
            );
            Some(regs)
        } else {
            None
        };

        let mut mat = ShaderMaterial::from_bytecode(&self.bytecode)
            .with_time_f32_reg(self.time_f32_reg)
            .with_delta_time_f32_reg(self.delta_time_f32_reg)
            .with_frame_i32_reg(self.frame_i32_reg)
            .with_resolution_v2_reg(self.resolution_v2_reg)
            .with_near_f32_reg(self.near_f32_reg)
            .with_far_f32_reg(self.far_f32_reg)
            .with_front_facing_bool_reg(self.front_facing_bool_reg)
            .with_frag_depth_f32_reg(self.frag_depth_f32_reg)
            .with_line_coord_f32_reg(self.line_coord_f32_reg)
            .with_point_coord_v2_reg(self.point_coord_v2_reg)
            .with_default_glyph(self.default_glyph)
            .with_blend_mode(self.blend_mode)
            .with_glyph_policy(self.glyph_policy);
        if let Some(regs) = seed_registers {
            mat = mat.with_seed_registers(ShaderSeedRegisters::from_registers(regs));
        }
        Ok(mat)
    }
}

#[pymethods]
impl ShaderPy {
    #[new]
    #[pyo3(signature = (bytecode, time_f32_reg=None, delta_time_f32_reg=None, resolution_v2_reg=None, front_facing_bool_reg=None, frag_depth_f32_reg=None, line_coord_f32_reg=None, point_coord_v2_reg=None, default_glyph=None, register_seed=None, frame_i32_reg=None, near_f32_reg=None, far_f32_reg=None, blend_mode=None, glyph_policy=None))]
    fn new(
        bytecode: &Bound<'_, PyBytes>,
        time_f32_reg: Option<usize>,
        delta_time_f32_reg: Option<usize>,
        resolution_v2_reg: Option<usize>,
        front_facing_bool_reg: Option<usize>,
        frag_depth_f32_reg: Option<usize>,
        line_coord_f32_reg: Option<usize>,
        point_coord_v2_reg: Option<usize>,
        default_glyph: Option<u8>,
        register_seed: Option<Py<PyAny>>,
        frame_i32_reg: Option<usize>,
        near_f32_reg: Option<usize>,
        far_f32_reg: Option<usize>,
        blend_mode: Option<&str>,
        glyph_policy: Option<&str>,
    ) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        let bytes = bytecode.as_bytes();
        let blend_mode = blend_mode
            .map(parse_blend_mode)
            .transpose()
            .unwrap_or(None)
            .unwrap_or(BlendMode::Replace);
        let glyph_policy = glyph_policy
            .map(parse_glyph_policy)
            .transpose()
            .unwrap_or(None)
            .unwrap_or(GlyphPolicy::PreserveExisting);
        PyClassInitializer::from(parent).add_subclass(ShaderPy {
            bytecode: bytes.to_vec(),
            time_f32_reg,
            delta_time_f32_reg,
            frame_i32_reg,
            resolution_v2_reg,
            near_f32_reg,
            far_f32_reg,
            front_facing_bool_reg,
            frag_depth_f32_reg,
            line_coord_f32_reg,
            point_coord_v2_reg,
            default_glyph,
            blend_mode,
            glyph_policy,
            register_seed,
        })
    }

    #[getter]
    fn bytecode<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        PyBytes::new(py, &self.bytecode)
    }

    #[setter]
    fn set_bytecode(&mut self, value: &Bound<'_, PyBytes>) {
        self.bytecode = value.as_bytes().to_vec();
    }

    #[getter]
    fn time_f32_reg(&self) -> Option<usize> {
        self.time_f32_reg
    }

    #[setter]
    fn set_time_f32_reg(&mut self, value: Option<usize>) {
        self.time_f32_reg = value;
    }

    #[getter]
    fn delta_time_f32_reg(&self) -> Option<usize> {
        self.delta_time_f32_reg
    }

    #[setter]
    fn set_delta_time_f32_reg(&mut self, value: Option<usize>) {
        self.delta_time_f32_reg = value;
    }

    #[getter]
    fn frame_i32_reg(&self) -> Option<usize> {
        self.frame_i32_reg
    }

    #[setter]
    fn set_frame_i32_reg(&mut self, value: Option<usize>) {
        self.frame_i32_reg = value;
    }

    #[getter]
    fn resolution_v2_reg(&self) -> Option<usize> {
        self.resolution_v2_reg
    }

    #[setter]
    fn set_resolution_v2_reg(&mut self, value: Option<usize>) {
        self.resolution_v2_reg = value;
    }

    #[getter]
    fn near_f32_reg(&self) -> Option<usize> {
        self.near_f32_reg
    }

    #[setter]
    fn set_near_f32_reg(&mut self, value: Option<usize>) {
        self.near_f32_reg = value;
    }

    #[getter]
    fn far_f32_reg(&self) -> Option<usize> {
        self.far_f32_reg
    }

    #[setter]
    fn set_far_f32_reg(&mut self, value: Option<usize>) {
        self.far_f32_reg = value;
    }

    #[getter]
    fn front_facing_bool_reg(&self) -> Option<usize> {
        self.front_facing_bool_reg
    }

    #[setter]
    fn set_front_facing_bool_reg(&mut self, value: Option<usize>) {
        self.front_facing_bool_reg = value;
    }

    #[getter]
    fn frag_depth_f32_reg(&self) -> Option<usize> {
        self.frag_depth_f32_reg
    }

    #[setter]
    fn set_frag_depth_f32_reg(&mut self, value: Option<usize>) {
        self.frag_depth_f32_reg = value;
    }

    #[getter]
    fn line_coord_f32_reg(&self) -> Option<usize> {
        self.line_coord_f32_reg
    }

    #[setter]
    fn set_line_coord_f32_reg(&mut self, value: Option<usize>) {
        self.line_coord_f32_reg = value;
    }

    #[getter]
    fn point_coord_v2_reg(&self) -> Option<usize> {
        self.point_coord_v2_reg
    }

    #[setter]
    fn set_point_coord_v2_reg(&mut self, value: Option<usize>) {
        self.point_coord_v2_reg = value;
    }

    #[getter]
    fn default_glyph(&self) -> Option<u8> {
        self.default_glyph
    }

    #[setter]
    fn set_default_glyph(&mut self, value: Option<u8>) {
        self.default_glyph = value;
    }

    #[getter]
    fn blend_mode(&self) -> String {
        blend_mode_to_str(self.blend_mode).to_string()
    }

    #[setter]
    fn set_blend_mode(&mut self, value: &str) -> PyResult<()> {
        self.blend_mode = parse_blend_mode(value)?;
        Ok(())
    }

    #[getter]
    fn glyph_policy(&self) -> String {
        glyph_policy_to_str(self.glyph_policy).to_string()
    }

    #[setter]
    fn set_glyph_policy(&mut self, value: &str) -> PyResult<()> {
        self.glyph_policy = parse_glyph_policy(value)?;
        Ok(())
    }
}

#[pyclass(extends=MaterialPy)]
#[derive(Clone)]
pub struct StaticGlyphPy {
    #[pyo3(get, set)]
    pub glyph_idx: u8,
}
#[pymethods]
impl StaticGlyphPy {
    #[new]
    fn new(glyph_idx: u8) -> PyClassInitializer<Self> {
        let parent = MaterialPy::new();
        PyClassInitializer::from(parent).add_subclass(StaticGlyphPy { glyph_idx })
    }
}
