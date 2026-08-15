use pyo3::prelude::*;
use std::collections::HashSet;

#[pyclass]
#[derive(Default)]
pub struct BatchAggregator {
    keys: HashSet<String>,
}

#[pymethods]
impl BatchAggregator {
    #[new]
    pub fn new() -> Self {
        Self {
            keys: HashSet::new(),
        }
    }

    pub fn add_key(&mut self, key: String) -> bool {
        self.keys.insert(key)
    }

    pub fn get_keys(&self) -> Vec<String> {
        self.keys.iter().cloned().collect()
    }

    pub fn clear(&mut self) {
        self.keys.clear();
    }

    pub fn len(&self) -> usize {
        self.keys.len()
    }

    pub fn is_empty(&self) -> bool {
        self.keys.is_empty()
    }
}
