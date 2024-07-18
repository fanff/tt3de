use fastnoise_lite::*;


#[derive(Clone, Debug)]
pub struct NoiseMaterial {
    pub int_config: i32,
    pub seed: i32,
}

impl NoiseMaterial {
    pub fn new(config: i32, seed: i32) -> Self {
        Self {
            int_config: config,
            seed,
        }
    }
    pub fn make_instance(&self) -> FastNoiseLite {
        let mut noise = FastNoiseLite::new();
        match self.int_config {
            0 => noise.set_noise_type(Some(NoiseType::OpenSimplex2)),
            1 => noise.set_noise_type(Some(NoiseType::Cellular)),
            2 => noise.set_noise_type(Some(NoiseType::Perlin)),
            3 => noise.set_noise_type(Some(NoiseType::Value)),
            _ => noise.set_noise_type(Some(NoiseType::OpenSimplex2)),
        }
        noise.set_seed(Some(self.seed));
        noise
    }
}
