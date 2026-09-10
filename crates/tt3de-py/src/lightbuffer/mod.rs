use pyo3::{
    exceptions::PyValueError, pyclass, pymethods, types::PyAnyMethods, Bound, Py, PyAny, PyResult,
    Python,
};
use tt3de_core::lightbuffer::{LightBuffer, LightError, LightType, MAX_LIGHTS};
use tt3de_core::ttsl::TtslLightEnv;

use crate::utils::{convert_glm_vec3, convert_pymat4, vec3_to_pyglm};

fn light_err(err: LightError) -> pyo3::PyErr {
    PyValueError::new_err(err.to_string())
}

fn parse_vec3(py: Python<'_>, value: Bound<'_, PyAny>) -> PyResult<nalgebra_glm::Vec3> {
    if let Ok((x, y, z)) = value.extract::<(f32, f32, f32)>() {
        return Ok(nalgebra_glm::Vec3::new(x, y, z));
    }
    Ok(convert_glm_vec3(py, value.unbind()))
}

#[pyclass]
pub struct LightBufferPy {
    pub data: LightBuffer,
}

#[pymethods]
impl LightBufferPy {
    #[new]
    #[pyo3(signature = (capacity=16))]
    fn new(capacity: usize) -> PyResult<Self> {
        Ok(Self {
            data: LightBuffer::with_capacity(capacity).map_err(light_err)?,
        })
    }

    #[getter]
    fn capacity(&self) -> usize {
        self.data.user_capacity()
    }

    fn count(&self) -> usize {
        self.data.count()
    }

    fn max_lights(&self) -> usize {
        MAX_LIGHTS
    }

    fn set_ambient(
        &mut self,
        py: Python<'_>,
        index: usize,
        color: Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let color = parse_vec3(py, color)?;
        self.data.set_ambient(index, color).map_err(light_err)
    }

    fn set_directional(
        &mut self,
        py: Python<'_>,
        index: usize,
        color: Bound<'_, PyAny>,
        direction: Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let color = parse_vec3(py, color)?;
        let direction = parse_vec3(py, direction)?;
        self.data
            .set_directional(index, color, direction)
            .map_err(light_err)
    }

    fn set_point(
        &mut self,
        py: Python<'_>,
        index: usize,
        color: Bound<'_, PyAny>,
        position: Bound<'_, PyAny>,
        attenuation: Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let color = parse_vec3(py, color)?;
        let position = parse_vec3(py, position)?;
        let attenuation = parse_vec3(py, attenuation)?;
        self.data
            .set_point(index, color, position, attenuation)
            .map_err(light_err)
    }

    fn clear(&mut self, index: usize) -> PyResult<()> {
        self.data.clear(index).map_err(light_err)
    }

    fn light_type(&self, index: usize) -> i32 {
        self.data.light_type(index as i32)
    }

    fn light_color(&self, py: Python<'_>, index: usize) -> Py<PyAny> {
        vec3_to_pyglm(py, self.data.light_color(index as i32))
    }

    fn light_direction(&self, py: Python<'_>, index: usize) -> Py<PyAny> {
        vec3_to_pyglm(py, self.data.light_direction(index as i32))
    }

    fn light_position(&self, py: Python<'_>, index: usize) -> Py<PyAny> {
        vec3_to_pyglm(py, self.data.light_position(index as i32))
    }

    fn light_attenuation(&self, py: Python<'_>, index: usize) -> Py<PyAny> {
        vec3_to_pyglm(py, self.data.light_attenuation(index as i32))
    }

    /// Apply the camera view matrix so TTSL accessors return view-space values.
    fn update_view_space(&mut self, py: Python<'_>, view_matrix: Py<PyAny>) {
        let mat = convert_pymat4(py, &view_matrix);
        self.data.update_view_space(&mat);
    }

    #[staticmethod]
    fn type_name(ty: i32) -> &'static str {
        match LightType::from_i32(ty) {
            LightType::Empty => "empty",
            LightType::Ambient => "ambient",
            LightType::Directional => "directional",
            LightType::Point => "point",
        }
    }
}
