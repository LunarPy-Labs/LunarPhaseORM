use pyo3::prelude::*;
use std::fmt::Write;

#[pyclass]
pub struct QueryCompiler;

#[pymethods]
impl QueryCompiler {
    #[new]
    pub fn new() -> Self {
        Self
    }

    /// Formats placeholder based on database dialect: sqlite (?), postgres ($N), mysql (%s)
    pub fn get_placeholder(&self, dialect: &str, index: usize) -> String {
        match dialect.to_lowercase().as_str() {
            "postgres" | "postgresql" => format!("${}", index),
            "mysql" => "%s".to_string(),
            _ => "?".to_string(),
        }
    }

    /// Compiles SELECT query with pre-allocated buffer
    #[pyo3(signature = (table, columns, wheres, joins, order_by, limit=None, offset=None, dialect="sqlite"))]
    pub fn compile_select(
        &self,
        table: &str,
        columns: Vec<String>,
        wheres: Vec<(String, String, String)>,
        joins: Vec<(String, String, String)>,
        order_by: Vec<(String, String)>,
        limit: Option<usize>,
        offset: Option<usize>,
        dialect: &str,
    ) -> PyResult<(String, Vec<String>)> {
        let cols_str = if columns.is_empty() {
            "*".to_string()
        } else {
            columns.join(", ")
        };

        let mut sql = String::with_capacity(256);
        let _ = write!(sql, "SELECT {} FROM {}", cols_str, table);

        let mut params = Vec::with_capacity(wheres.len());
        let mut param_idx = 1;

        // JOINs
        for (jtype, jtable, jcond) in joins {
            let _ = write!(sql, " {} JOIN {} ON {}", jtype.to_uppercase(), jtable, jcond);
        }

        // WHEREs
        if !wheres.is_empty() {
            sql.push_str(" WHERE ");
            for (i, (col, op, val_str)) in wheres.into_iter().enumerate() {
                if i > 0 {
                    sql.push_str(" AND ");
                }
                let ph = self.get_placeholder(dialect, param_idx);
                param_idx += 1;
                let _ = write!(sql, "{} {} {}", col, op, ph);
                params.push(val_str);
            }
        }

        // ORDER BY
        if !order_by.is_empty() {
            sql.push_str(" ORDER BY ");
            for (i, (col, dir)) in order_by.into_iter().enumerate() {
                if i > 0 {
                    sql.push_str(", ");
                }
                let _ = write!(sql, "{} {}", col, dir.to_uppercase());
            }
        }

        // LIMIT & OFFSET
        if let Some(l) = limit {
            let _ = write!(sql, " LIMIT {}", l);
        }
        if let Some(o) = offset {
            let _ = write!(sql, " OFFSET {}", o);
        }

        Ok((sql, params))
    }

    /// Compiles INSERT query with pre-allocated buffer
    pub fn compile_insert(&self, table: &str, columns: Vec<String>, dialect: &str) -> PyResult<String> {
        let placeholders: Vec<String> = (1..=columns.len())
            .map(|i| self.get_placeholder(dialect, i))
            .collect();

        let cols_str = columns.join(", ");
        let ph_str = placeholders.join(", ");

        let mut sql = String::with_capacity(128);
        let _ = write!(sql, "INSERT INTO {} ({}) VALUES ({})", table, cols_str, ph_str);
        if dialect.to_lowercase().contains("postgres") {
            sql.push_str(" RETURNING *");
        }
        Ok(sql)
    }

    /// Compiles UPDATE query with pre-allocated buffer
    pub fn compile_update(
        &self,
        table: &str,
        columns: Vec<String>,
        pk_col: &str,
        dialect: &str,
    ) -> PyResult<String> {
        let mut set_clauses = Vec::with_capacity(columns.len());
        let mut idx = 1;
        for col in &columns {
            set_clauses.push(format!("{} = {}", col, self.get_placeholder(dialect, idx)));
            idx += 1;
        }

        let pk_ph = self.get_placeholder(dialect, idx);
        let mut sql = String::with_capacity(128);
        let _ = write!(
            sql,
            "UPDATE {} SET {} WHERE {} = {}",
            table,
            set_clauses.join(", "),
            pk_col,
            pk_ph
        );
        Ok(sql)
    }

    /// Compiles DELETE query
    pub fn compile_delete(&self, table: &str, pk_col: &str, dialect: &str) -> PyResult<String> {
        let ph = self.get_placeholder(dialect, 1);
        Ok(format!("DELETE FROM {} WHERE {} = {}", table, pk_col, ph))
    }
}
