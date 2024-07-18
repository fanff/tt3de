use fastnoise_lite::{FastNoiseLite, NoiseType};

use super::RGBA;

pub struct NoiseTexture {
    pub seed: i32,
    pub int_config: i32,
    pub noise: FastNoiseLite,
}

impl Clone for NoiseTexture {
    fn clone(&self) -> Self {
        let mut noise = FastNoiseLite::new();
        noise.set_seed(Some(self.seed));
        match self.int_config {
            0 => noise.set_noise_type(Some(NoiseType::OpenSimplex2)),
            1 => noise.set_noise_type(Some(NoiseType::Cellular)),
            2 => noise.set_noise_type(Some(NoiseType::Perlin)),
            3 => noise.set_noise_type(Some(NoiseType::Value)),
            _ => noise.set_noise_type(Some(NoiseType::OpenSimplex2)),
        }
        NoiseTexture {
            seed: self.seed,
            int_config: self.int_config,
            noise,
        }
    }
}

impl NoiseTexture {
    pub fn new(seed: i32, int_config: i32) -> Self {
        let mut noise = FastNoiseLite::new();
        noise.set_seed(Some(seed));
        match int_config {
            0 => noise.set_noise_type(Some(NoiseType::OpenSimplex2)),
            1 => noise.set_noise_type(Some(NoiseType::Cellular)),
            2 => noise.set_noise_type(Some(NoiseType::Perlin)),
            3 => noise.set_noise_type(Some(NoiseType::Value)),
            _ => noise.set_noise_type(Some(NoiseType::OpenSimplex2)),
        }
        Self {
            seed,
            int_config,
            noise,
        }
    }
    pub fn uv_map(&self, u: f32, v: f32) -> RGBA {
        let nv = self.noise.get_noise_2d(u, v);
        RGBA {
            r: (nv * 255.0) as u8,
            g: (nv * 255.0) as u8,
            b: (nv * 255.0) as u8,
            a: 255,
        }
    }
}
