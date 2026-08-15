use pyo3::prelude::*;
use pyo3::types::{PyList, PySequence};
use rustc_hash::FxHashSet;

#[pyclass]
#[derive(Default)]
pub struct BatchAggregator {
    int_keys: FxHashSet<i64>,
    str_keys: FxHashSet<String>,
}

#[pymethods]
impl BatchAggregator {
    #[new]
    pub fn new() -> Self {
        Self {
            int_keys: FxHashSet::default(),
            str_keys: FxHashSet::default(),
        }
    }

    /// Add an integer foreign key directly (Zero string formatting overhead)
    pub fn add_key_int(&mut self, key: i64) -> bool {
        self.int_keys.insert(key)
    }

    /// Add a string foreign key
    pub fn add_key_str(&mut self, key: String) -> bool {
        self.str_keys.insert(key)
    }

    /// Dynamically add key checking type
    pub fn add_key(&mut self, key: &Bound<'_, PyAny>) -> PyResult<bool> {
        if let Ok(val) = key.extract::<i64>() {
            Ok(self.int_keys.insert(val))
        } else if let Ok(val) = key.extract::<String>() {
            Ok(self.str_keys.insert(val))
        } else {
            let str_val = key.to_string();
            Ok(self.str_keys.insert(str_val))
        }
    }

    /// Batch add keys in a single FFI boundary call
    pub fn add_keys_batch(&mut self, keys: &Bound<'_, PySequence>) -> PyResult<usize> {
        let len = keys.len()?;
        let mut added = 0;
        for i in 0..len {
            let item = keys.get_item(i)?;
            if let Ok(val) = item.extract::<i64>() {
                if self.int_keys.insert(val) {
                    added += 1;
                }
            } else if let Ok(val) = item.extract::<String>() {
                if self.str_keys.insert(val) {
                    added += 1;
                }
            } else {
                let str_val = item.to_string();
                if self.str_keys.insert(str_val) {
                    added += 1;
                }
            }
        }
        Ok(added)
    }

    /// Returns deduplicated keys as a PyList constructed directly in Rust
    pub fn get_keys<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty_bound(py);
        for k in &self.int_keys {
            list.append(k)?;
        }
        for k in &self.str_keys {
            list.append(k)?;
        }
        Ok(list)
    }

    pub fn clear(&mut self) {
        self.int_keys.clear();
        self.str_keys.clear();
    }

    pub fn len(&self) -> usize {
        self.int_keys.len() + self.str_keys.len()
    }

    pub fn is_empty(&self) -> bool {
        self.int_keys.is_empty() && self.str_keys.is_empty()
    }
}
