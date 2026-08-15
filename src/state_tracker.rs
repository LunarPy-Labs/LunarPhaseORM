use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

#[pyclass]
#[derive(Default)]
pub struct StateTracker {
    snapshot: HashMap<String, String>, // Store serialized JSON values for exact diffing
    current: HashMap<String, String>,
    py_cache: HashMap<String, PyObject>,
}

#[pymethods]
impl StateTracker {
    #[new]
    pub fn new() -> Self {
        Self {
            snapshot: HashMap::new(),
            current: HashMap::new(),
            py_cache: HashMap::new(),
        }
    }

    pub fn set_initial_state(&mut self, py: Python<'_>, data: &Bound<'_, PyDict>) -> PyResult<()> {
        self.snapshot.clear();
        self.current.clear();
        self.py_cache.clear();

        let json_mod = py.import_bound("json")?;
        for (k, v) in data.iter() {
            let key = k.extract::<String>()?;
            let serialized: String = if v.is_none() {
                "null".to_string()
            } else {
                json_mod
                    .call_method1("dumps", (&v,))?
                    .extract::<String>()
                    .unwrap_or_else(|_| v.to_string())
            };

            self.snapshot.insert(key.clone(), serialized.clone());
            self.current.insert(key.clone(), serialized);
            self.py_cache.insert(key, v.clone().unbind());
        }
        Ok(())
    }

    pub fn set_field(&mut self, py: Python<'_>, field: String, value: &Bound<'_, PyAny>) -> PyResult<()> {
        let json_mod = py.import_bound("json")?;
        let serialized: String = if value.is_none() {
            "null".to_string()
        } else {
            json_mod
                .call_method1("dumps", (value,))?
                .extract::<String>()
                .unwrap_or_else(|_| value.to_string())
        };

        self.current.insert(field.clone(), serialized);
        self.py_cache.insert(field, value.clone().unbind());
        Ok(())
    }

    pub fn get_field(&self, py: Python<'_>, field: &str) -> PyResult<PyObject> {
        if let Some(obj) = self.py_cache.get(field) {
            Ok(obj.clone_ref(py))
        } else {
            Ok(py.None())
        }
    }

    pub fn is_dirty(&self) -> bool {
        for (k, v) in &self.current {
            if let Some(snap_val) = self.snapshot.get(k) {
                if snap_val != v {
                    return true;
                }
            } else {
                return true; // New field added
            }
        }
        false
    }

    pub fn dirty_fields(&self) -> Vec<String> {
        let mut dirty = Vec::new();
        for (k, v) in &self.current {
            if let Some(snap_val) = self.snapshot.get(k) {
                if snap_val != v {
                    dirty.push(k.clone());
                }
            } else {
                dirty.push(k.clone());
            }
        }
        dirty
    }

    pub fn get_dirty_changes<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        for k in self.dirty_fields() {
            if let Some(val) = self.py_cache.get(&k) {
                dict.set_item(k, val.clone_ref(py))?;
            }
        }
        Ok(dict)
    }

    pub fn hydrate_snapshot(&mut self) {
        self.snapshot = self.current.clone();
    }

    pub fn get_current_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        for (k, v) in &self.py_cache {
            dict.set_item(k, v.clone_ref(py))?;
        }
        Ok(dict)
    }
}
