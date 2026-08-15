use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct ColumnDef {
    pub name: String,
    pub data_type: String,
    pub is_null: bool,
    pub is_pk: bool,
}

#[pyclass]
pub struct SchemaDiffEngine;

#[pymethods]
impl SchemaDiffEngine {
    #[new]
    pub fn new() -> Self {
        Self
    }

    /// Compares model metadata against database introspection table structure.
    /// Returns upgrade_statements and downgrade_statements.
    pub fn diff_table(
        &self,
        table_name: &str,
        model_fields: &Bound<'_, PyDict>,
        db_columns: &Bound<'_, PyDict>,
        _dialect: &str,
    ) -> PyResult<(Vec<String>, Vec<String>)> {
        let mut upgrade = Vec::new();
        let mut downgrade = Vec::new();

        let mut expected_fields: HashMap<String, (String, bool, bool)> = HashMap::new(); // (type, nullable, pk)
        for (k, v) in model_fields.iter() {
            let col_name = k.extract::<String>()?;
            let col_info = v.downcast::<PyDict>()?;
            let dtype = col_info
                .get_item("data_type")?
                .map(|x| x.extract::<String>().unwrap_or_else(|_| "TEXT".to_string()))
                .unwrap_or_else(|| "TEXT".to_string());
            let nullable = col_info
                .get_item("nullable")?
                .map(|x| x.extract::<bool>().unwrap_or(true))
                .unwrap_or(true);
            let pk = col_info
                .get_item("primary_key")?
                .map(|x| x.extract::<bool>().unwrap_or(false))
                .unwrap_or(false);

            expected_fields.insert(col_name, (dtype, nullable, pk));
        }

        let mut actual_fields: HashMap<String, String> = HashMap::new();
        for (k, v) in db_columns.iter() {
            let col_name = k.extract::<String>()?;
            let dtype = v.extract::<String>()?;
            actual_fields.insert(col_name, dtype);
        }

        // Table doesn't exist in DB -> Create Table
        if actual_fields.is_empty() {
            let mut col_defs = Vec::new();
            for (name, (dtype, nullable, pk)) in &expected_fields {
                let mut def = format!("{} {}", name, dtype);
                if *pk {
                    def.push_str(" PRIMARY KEY");
                }
                if !nullable && !pk {
                    def.push_str(" NOT NULL");
                }
                col_defs.push(def);
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({});",
                table_name,
                col_defs.join(", ")
            );
            let drop_sql = format!("DROP TABLE IF EXISTS {};", table_name);
            upgrade.push(create_sql);
            downgrade.push(drop_sql);
            return Ok((upgrade, downgrade));
        }

        // Check for missing columns -> ADD COLUMN
        for (name, (dtype, nullable, pk)) in &expected_fields {
            if !actual_fields.contains_key(name) {
                let mut def = format!("ALTER TABLE {} ADD COLUMN {} {}", table_name, name, dtype);
                if !nullable && !pk {
                    def.push_str(" NOT NULL");
                }
                def.push(';');
                upgrade.push(def);
                downgrade.push(format!(
                    "ALTER TABLE {} DROP COLUMN {};",
                    table_name, name
                ));
            }
        }

        Ok((upgrade, downgrade))
    }
}
