use std::collections::BTreeMap;

use pyo3::{
    intern,
    types::{PyAnyMethods, PyDict},
    Bound, Py, PyAny, Python,
};

use super::{Color, GLYPH_STATIC_STR};

pub struct SegmentCache {
    data: BTreeMap<u64, Py<PyAny>>,
    bit_size_front: [u8; 3],
    bit_size_back: [u8; 3],
}

impl SegmentCache {
    pub fn new(bit_size_front: [u8; 3], bit_size_back: [u8; 3]) -> Self {
        SegmentCache {
            data: BTreeMap::new(),
            bit_size_front,
            bit_size_back,
        }
    }
    pub fn get_cache_size(&self) -> usize {
        self.data.len()
    }
    pub fn new_iso(bit_size: u8) -> Self {
        SegmentCache {
            data: BTreeMap::new(),
            bit_size_front: [bit_size; 3],
            bit_size_back: [bit_size; 3],
        }
    }
    pub fn set_bit_size_front(&mut self, r: u8, g: u8, b: u8) {
        self.bit_size_front = [r, g, b];
        self.data = BTreeMap::new()
    }

    pub fn set_bit_size_back(&mut self, r: u8, g: u8, b: u8) {
        self.bit_size_back = [r, g, b];
        self.data = BTreeMap::new()
    }
    ///
    ///
    /// # Examples
    ///
    /// ```
    /// use rtt3de::drawbuffer::segment_cache::SegmentCache;
    /// let value = 200;
    /// let bit_size = 4;
    /// assert_eq!(SegmentCache::reduce_value(value, bit_size),12 );
    /// ```
    pub fn reduce_value(value: u8, bit_size: u8) -> u8 {
        value >> (8 - bit_size)
    }

    /// Unreduce a reduced value by shifting it left by the number of bits retained
    /// and fill by 1s
    pub fn unreduce_value(value: u8, bit_size: u8) -> u8 {
        let mask = (1 << (8 - bit_size)) - 1;
        (value << (8 - bit_size)) | mask
    }

    pub fn get_reduced(&self, f: &Color, b: &Color, glyph: u8) -> [u8; 7] {
        // lets reduce the accuraccy of the color by reducing the bit count.
        let hfr = Self::reduce_value(f.r, self.bit_size_front[0]);
        let hfg = Self::reduce_value(f.g, self.bit_size_front[1]);
        let hfb = Self::reduce_value(f.b, self.bit_size_front[2]);

        let hbr = Self::reduce_value(b.r, self.bit_size_back[0]);
        let hbg = Self::reduce_value(b.g, self.bit_size_back[1]);
        let hbb = Self::reduce_value(b.b, self.bit_size_back[2]);

        // now assemblate a hash value based on this.
        [hfr, hfg, hfb, hbr, hbg, hbb, glyph]
    }

    pub fn reduced_to_triplet(&self, reduced_tuple: [u8; 7]) -> ([u8; 3], [u8; 3], u8) {
        // unreduce a reduced value by shifting it left by the number of bits retained
        // and fill by 1s
        let front_color = [
            Self::unreduce_value(reduced_tuple[0], self.bit_size_front[0]),
            Self::unreduce_value(reduced_tuple[1], self.bit_size_front[1]),
            Self::unreduce_value(reduced_tuple[2], self.bit_size_front[2]),
        ];

        let back_color = [
            Self::unreduce_value(reduced_tuple[3], self.bit_size_back[0]),
            Self::unreduce_value(reduced_tuple[4], self.bit_size_back[1]),
            Self::unreduce_value(reduced_tuple[5], self.bit_size_back[2]),
        ];

        (front_color, back_color, reduced_tuple[6])
    }

    pub fn insert_with_hash(&mut self, hash_value: u64, value: Py<PyAny>) {
        self.data.insert(hash_value, value);
    }

    pub fn get_with_hash(&self, hash_value: u64) -> Option<&Py<PyAny>> {
        self.data.get(&hash_value)
    }

    pub fn reduced_tuple_to_int(&self, reduced_tuple: [u8; 7]) -> u64 {
        let mut hash: u64 = 0;

        for i in 0..3 {
            // Shift the hash left by the number of bits retained and add the reduced number
            hash = (hash << self.bit_size_front[i]) | reduced_tuple[i] as u64;
        }

        for i in 0..3 {
            // Retain only the highest bits as specified by bit_reductions[i]
            // Shift the hash left by the number of bits retained and add the reduced number
            hash = (hash << self.bit_size_back[i]) | reduced_tuple[i + 3] as u64;
        }

        // Add glyph without any bit reduction
        hash = (hash << 8) | reduced_tuple[6] as u64;

        hash
    }

    pub fn estimate_max_combinations(bit_size_front: [u8; 3], bit_size_back: [u8; 3]) -> u64 {
        let front_combinations = (1 << bit_size_front[0]) as u64
            * (1 << bit_size_front[1]) as u64
            * (1 << bit_size_front[2]) as u64;
        let back_combinations = (1 << bit_size_back[0]) as u64
            * (1 << bit_size_back[1]) as u64
            * (1 << bit_size_back[2]) as u64;

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
    let dict = PyDict::new(py);
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

// test module for reduce_value function
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reduce_value() {
        let value = 200;
        let bit_size = 4;
        assert_eq!(SegmentCache::reduce_value(value, bit_size), 12);

        for value in 0..255 {
            for bit_size in 1..8 {
                let reduced = SegmentCache::reduce_value(value, bit_size);
                assert!(reduced < 2u8.pow(bit_size as u32));
            }
        }
    }

    #[test]
    fn test_unreduce() {
        let value = 200;
        let bit_size = 4;
        let reduced = SegmentCache::reduce_value(value, bit_size);
        let unreduced = SegmentCache::unreduce_value(reduced, bit_size);
        assert_eq!(unreduced, 207);

        assert_eq!(
            SegmentCache::unreduce_value(SegmentCache::reduce_value(255, 2), 2),
            255
        );
    }

    #[test]
    fn test_combination() {
        let bit_size_front = [2, 2, 2];
        let bit_size_back = [2, 2, 2];
        let max_combinations =
            SegmentCache::estimate_max_combinations(bit_size_front, bit_size_back);

        assert_eq!(max_combinations, (4 * 4 * 4) * (4 * 4 * 4) * 256);

        let bit_size_front = [3, 3, 3];
        let bit_size_back = [3, 3, 3];
        let max_combinations =
            SegmentCache::estimate_max_combinations(bit_size_front, bit_size_back);

        assert_eq!(max_combinations, (8 * 8 * 8) * (8 * 8 * 8) * 256); // 67 Million combinations (2^26)
    }
}
