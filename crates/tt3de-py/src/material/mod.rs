use crate::{material::materials_py::*, utils::convert_tuple_rgba};
use pyo3::{exceptions::PyValueError, pyclass, pymethods, types::PyTuple, Bound, PyResult, Python};
use tt3de_core::material::{materials::Material, MaterialBuffer};
pub mod materials_py;

#[pyclass]
pub struct MaterialBufferPy {
    pub content: MaterialBuffer,
}

#[pymethods]
impl MaterialBufferPy {
    #[new]
    #[pyo3(signature = (max_size=64))]
    fn new(max_size: usize) -> Self {
        MaterialBufferPy {
            content: MaterialBuffer::new(max_size),
        }
    }
    fn add_material(&mut self, _py: Python, _mat: Bound<'_, MaterialPy>) -> usize {
        panic!("Not implemented");
    }

    fn set_material(&mut self, _py: Python, _idx: usize, _mat: Bound<'_, MaterialPy>) {
        panic!("Not implemented");
    }

    fn add_base_texture<'py>(&mut self, _py: Python<'py>, mat: &BaseTexturePy) -> usize {
        self.content
            .add_material(Material::BaseTexture(mat.to_native()))
    }

    fn add_static_color(&mut self, _py: Python, mat: &StaticColorPy) -> usize {
        self.content.add_material(mat.to_native())
    }

    fn add_shader(&mut self, py: Python<'_>, mat: &Bound<'_, ShaderPy>) -> PyResult<usize> {
        let native = mat.borrow().build_native(py)?;
        Ok(self.content.add_material(Material::Shader(native)))
    }

    fn clear(&mut self) {
        self.content.clear()
    }
    fn count(&self) -> usize {
        self.content.current_size
    }

    fn add_textured(&mut self, _py: Python, albedo_texture_idx: usize, glyph_idx: u8) -> usize {
        self.content.add_textured(albedo_texture_idx, glyph_idx)
    }

    fn add_static(
        &mut self,
        _py: Python,
        front_rgba: &Bound<PyTuple>,
        back_rgba: &Bound<PyTuple>,
        glyph_idx: u8,
    ) -> usize {
        let fr = convert_tuple_rgba(front_rgba).unwrap();
        let bg = convert_tuple_rgba(back_rgba).unwrap();
        self.content.add_static(fr, bg, glyph_idx)
    }

    fn add_debug_depth(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_depth(glyph_idx)
    }

    fn add_debug_uv(&mut self, _py: Python, glyph_idx: u8) -> usize {
        self.content.add_debug_uv(glyph_idx)
    }

    fn set_shader_time(&mut self, material_idx: usize, time_seconds: f32) -> PyResult<()> {
        if material_idx >= self.content.current_size {
            return Err(PyValueError::new_err("material_idx out of range"));
        }

        match &mut self.content.mats[material_idx] {
            Material::Shader(shader) => {
                shader.set_time_seconds(time_seconds);
                Ok(())
            }
            _ => Err(PyValueError::new_err(
                "material at material_idx is not a Shader material",
            )),
        }
    }

    fn set_shader_delta_time(&mut self, material_idx: usize, dt_seconds: f32) -> PyResult<()> {
        if material_idx >= self.content.current_size {
            return Err(PyValueError::new_err("material_idx out of range"));
        }

        match &mut self.content.mats[material_idx] {
            Material::Shader(shader) => {
                shader.set_delta_time_seconds(dt_seconds);
                Ok(())
            }
            _ => Err(PyValueError::new_err(
                "material at material_idx is not a Shader material",
            )),
        }
    }

    fn set_shader_frame(&mut self, material_idx: usize, frame: u32) -> PyResult<()> {
        if material_idx >= self.content.current_size {
            return Err(PyValueError::new_err("material_idx out of range"));
        }

        match &mut self.content.mats[material_idx] {
            Material::Shader(shader) => {
                shader.set_frame_counter(frame);
                Ok(())
            }
            _ => Err(PyValueError::new_err(
                "material at material_idx is not a Shader material",
            )),
        }
    }

    fn set_shader_resolution(
        &mut self,
        material_idx: usize,
        width_cells: f32,
        height_cells: f32,
    ) -> PyResult<()> {
        if material_idx >= self.content.current_size {
            return Err(PyValueError::new_err("material_idx out of range"));
        }

        match &mut self.content.mats[material_idx] {
            Material::Shader(shader) => {
                shader.set_resolution_cells(width_cells, height_cells);
                Ok(())
            }
            _ => Err(PyValueError::new_err(
                "material at material_idx is not a Shader material",
            )),
        }
    }

    fn set_shader_near(&mut self, material_idx: usize, near_clip_distance: f32) -> PyResult<()> {
        if material_idx >= self.content.current_size {
            return Err(PyValueError::new_err("material_idx out of range"));
        }

        match &mut self.content.mats[material_idx] {
            Material::Shader(shader) => {
                shader.set_near_clip_distance(near_clip_distance);
                Ok(())
            }
            _ => Err(PyValueError::new_err(
                "material at material_idx is not a Shader material",
            )),
        }
    }

    fn set_shader_far(&mut self, material_idx: usize, far_clip_distance: f32) -> PyResult<()> {
        if material_idx >= self.content.current_size {
            return Err(PyValueError::new_err("material_idx out of range"));
        }

        match &mut self.content.mats[material_idx] {
            Material::Shader(shader) => {
                shader.set_far_clip_distance(far_clip_distance);
                Ok(())
            }
            _ => Err(PyValueError::new_err(
                "material at material_idx is not a Shader material",
            )),
        }
    }
}
