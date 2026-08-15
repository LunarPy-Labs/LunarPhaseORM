mod batcher;
mod compiler;
mod migration_diff;
mod state_tracker;

use batcher::BatchAggregator;
use compiler::QueryCompiler;
use migration_diff::SchemaDiffEngine;
use pyo3::prelude::*;
use state_tracker::StateTracker;

#[pymodule]
fn _lunarphase_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<StateTracker>()?;
    m.add_class::<QueryCompiler>()?;
    m.add_class::<BatchAggregator>()?;
    m.add_class::<SchemaDiffEngine>()?;
    Ok(())
}
