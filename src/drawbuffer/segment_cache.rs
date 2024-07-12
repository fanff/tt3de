use std::collections::HashMap;

use pyo3::{
    intern,
    types::{PyAnyMethods, PyDict},
    Bound, Py, PyAny, Python,
};

use super::{Color, GLYPH_STATIC_STR};

pub struct SegmentCache {
    data: HashMap<u64, Py<PyAny>>,
    bit_size_front: [u8; 3],
    bit_size_back: [u8; 3],
}

impl SegmentCache {
    pub fn new(bit_size_front: [u8; 3], bit_size_back: [u8; 3]) -> Self {
        SegmentCache {
            data: HashMap::new(),
            bit_size_front,
            bit_size_back,
        }
    }
    pub fn set_bit_size_front(&mut self, r: u8, g: u8, b: u8) {
        self.bit_size_front = [r, g, b];
        self.data = HashMap::new()
    }

    pub fn set_bit_size_back(&mut self, r: u8, g: u8, b: u8) {
        self.bit_size_back = [r, g, b];
        self.data = HashMap::new()
    }

    pub fn get_reduced(&self, f: Color, b: Color, glyph: u8) -> [u8; 7] {
        // lets reduce the accuraccy of the color by reducing the bit count.
        let hfr = f.r >> (8 - self.bit_size_front[0]);
        let hfg = f.g >> (8 - self.bit_size_front[1]);
        let hfb = f.b >> (8 - self.bit_size_front[2]);

        let hbr = b.r >> (8 - self.bit_size_back[0]);
        let hbg = b.g >> (8 - self.bit_size_back[1]);
        let hbb = b.b >> (8 - self.bit_size_back[2]);

        // now assemblate a hash value based on this.
        [hfr, hfg, hfb, hbr, hbg, hbb, glyph]
    }

    pub fn insert_with_hash(&mut self, hash_value: u64, value: Py<PyAny>) {
        self.data.insert(hash_value, value);
    }

    pub fn get_with_hash(&self, hash_value: u64) -> Option<&Py<PyAny>> {
        self.data.get(&hash_value)
    }

    pub fn hash_tuple_to_int(&self, hash_tuple: [u8; 7]) -> u64 {
        let mut hash: u64 = 0;

        for i in 0..3 {
            // Retain only the highest bits as specified by bit_reductions[i]
            let reduced_num = hash_tuple[i] >> (8 - self.bit_size_front[i]);
            // Shift the hash left by the number of bits retained and add the reduced number
            hash = (hash << self.bit_size_front[i]) | reduced_num as u64;
        }

        for i in 0..3 {
            // Retain only the highest bits as specified by bit_reductions[i]
            let reduced_num = hash_tuple[i] >> (8 - self.bit_size_back[i]);
            // Shift the hash left by the number of bits retained and add the reduced number
            hash = (hash << self.bit_size_back[i]) | reduced_num as u64;
        }

        // Add  without any bit reduction
        hash = (hash << 8) | hash_tuple[6] as u64;

        hash
    }

    pub fn estimate_max_combinations(&self) -> u64 {
        let front_combinations = (1 << self.bit_size_front[0]) as u64
            * (1 << self.bit_size_front[1]) as u64
            * (1 << self.bit_size_front[2]) as u64;
        let back_combinations = (1 << self.bit_size_back[0]) as u64
            * (1 << self.bit_size_back[1]) as u64
            * (1 << self.bit_size_back[2]) as u64;

        front_combinations * back_combinations * 256 // 256 possible glyph values (u8)
    }
}
pub fn create_textual_segment(
    py: Python,
    reduced_hash: [u8; 7],
    color_triplet_class: &Bound<PyAny>,
    color_class: &Bound<PyAny>,
    segment_class: &Bound<PyAny>,
    style_class: &Bound<PyAny>,
) -> Py<PyAny> {
    let dict = PyDict::new_bound(py);
    let f_triplet = color_triplet_class
        .call1((reduced_hash[0], reduced_hash[1], reduced_hash[2]))
        .unwrap();
    let b_triplet = color_triplet_class
        .call1((reduced_hash[3], reduced_hash[4], reduced_hash[5]))
        .unwrap();
    dict.set_item(
        intern!(py, "color"),
        color_class
            .call_method1(intern!(py, "from_triplet"), (f_triplet,))
            .unwrap(),
    )
    .unwrap();

    dict.set_item(
        intern!(py, "bgcolor"),
        color_class
            .call_method1(intern!(py, "from_triplet"), (b_triplet,))
            .unwrap(),
    )
    .unwrap();
    let theglyph = GLYPH_STATIC_STR[reduced_hash[6] as usize];
    let anewseg = segment_class
        .call1((theglyph, &style_class.call((), Some(&dict)).unwrap()))
        .unwrap();
    anewseg.into()
}
