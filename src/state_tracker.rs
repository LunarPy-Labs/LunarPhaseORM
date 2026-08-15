use pyo3::prelude::*;
use pyo3::types::PyDict;
use rustc_hash::FxHashMap;
use std::time::Instant;

struct FieldEntry {
    snapshot: String,
    current: String,
    py_obj: PyObject,
}

#[pyclass]
#[derive(Default)]
pub struct StateTracker {
    fields: FxHashMap<String, FieldEntry>,
}

#[pymethods]
impl StateTracker {
    #[new]
    pub fn new() -> Self {
        Self {
            fields: FxHashMap::default(),
        }
    }

    pub fn set_initial_state(&mut self, _py: Python<'_>, data: &Bound<'_, PyDict>) -> PyResult<()> {
        self.fields.clear();
        self.fields.reserve(data.len());

        for (k, v) in data.iter() {
            let key = k.extract::<String>()?;
            let str_val = v.to_string();
            self.fields.insert(
                key,
                FieldEntry {
                    snapshot: str_val.clone(),
                    current: str_val,
                    py_obj: v.clone().unbind(),
                },
            );
        }
        Ok(())
    }

    pub fn set_field(&mut self, _py: Python<'_>, field: String, value: &Bound<'_, PyAny>) -> PyResult<()> {
        let str_val = value.to_string();
        let py_obj = value.clone().unbind();

        if let Some(entry) = self.fields.get_mut(&field) {
            entry.current = str_val;
            entry.py_obj = py_obj;
        } else {
            self.fields.insert(
                field,
                FieldEntry {
                    snapshot: str_val.clone(),
                    current: str_val,
                    py_obj,
                },
            );
        }
        Ok(())
    }

    pub fn get_field(&self, py: Python<'_>, field: &str) -> PyResult<PyObject> {
        if let Some(entry) = self.fields.get(field) {
            Ok(entry.py_obj.clone_ref(py))
        } else {
            Ok(py.None())
        }
    }

    pub fn is_dirty(&self) -> bool {
        self.fields.values().any(|e| e.snapshot != e.current)
    }

    pub fn dirty_fields(&self) -> Vec<String> {
        self.fields
            .iter()
            .filter_map(|(k, e)| {
                if e.snapshot != e.current {
                    Some(k.clone())
                } else {
                    None
                }
            })
            .collect()
    }

    pub fn get_dirty_changes<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        for (k, e) in &self.fields {
            if e.snapshot != e.current {
                dict.set_item(k, e.py_obj.clone_ref(py))?;
            }
        }
        Ok(dict)
    }

    pub fn hydrate_snapshot(&mut self) {
        for entry in self.fields.values_mut() {
            entry.snapshot = entry.current.clone();
        }
    }

    pub fn get_current_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        for (k, e) in &self.fields {
            dict.set_item(k, e.py_obj.clone_ref(py))?;
        }
        Ok(dict)
    }

    /// Pure Rust Native Benchmark (Rust -> Rust) executing 100% in C/Rust memory using FxHashMap
    #[staticmethod]
    pub fn benchmark_pure_rust(count: usize) -> f64 {
        let start = Instant::now();
        let mut trackers: Vec<NativeRustTracker> = (0..count)
            .map(|i| NativeRustTracker::new(i))
            .collect();

        for tracker in &mut trackers {
            tracker.set_field("age", "26");
            let _ = tracker.is_dirty();
            tracker.hydrate();
        }

        start.elapsed().as_secs_f64()
    }
}

/// Standalone Pure Rust Native Tracker using FxHashMap for exact Rust -> Rust timing
struct NativeRustTracker {
    fields: FxHashMap<String, (String, String)>, // (snapshot, current)
}

impl NativeRustTracker {
    fn new(id: usize) -> Self {
        let mut fields = FxHashMap::default();
        fields.insert("id".to_string(), (id.to_string(), id.to_string()));
        fields.insert("name".to_string(), ("Alice".to_string(), "Alice".to_string()));
        fields.insert("age".to_string(), ("25".to_string(), "25".to_string()));
        fields.insert("active".to_string(), ("true".to_string(), "true".to_string()));
        Self { fields }
    }

    fn set_field(&mut self, field: &str, value: &str) {
        if let Some(entry) = self.fields.get_mut(field) {
            entry.1 = value.to_string();
        }
    }

    fn is_dirty(&self) -> bool {
        self.fields.values().any(|(snap, curr)| snap != curr)
    }

    fn hydrate(&mut self) {
        for entry in self.fields.values_mut() {
            entry.0 = entry.1.clone();
        }
    }
}
