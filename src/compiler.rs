use pyo3::prelude::*;

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
            _ => "?".to_string(), // sqlite default
        }
    }

    /// Compiles SELECT query
    #[pyo3(signature = (table, columns, wheres, joins, order_by, limit=None, offset=None, dialect="sqlite"))]
    pub fn compile_select(
        &self,
        table: &str,
        columns: Vec<String>,
        wheres: Vec<(String, String, String)>, // (col, op, val_str)
        joins: Vec<(String, String, String)>,  // (join_type, table, condition)
        order_by: Vec<(String, String)>,       // (col, direction)
        limit: Option<usize>,
        offset: Option<usize>,
        dialect: &str,
    ) -> PyResult<(String, Vec<String>)> {
        let cols_str = if columns.is_empty() {
            "*".to_string()
        } else {
            columns.join(", ")
        };

        let mut sql = format!("SELECT {} FROM {}", cols_str, table);
        let mut params = Vec::new();
        let mut param_idx = 1;

        // JOINs
        for (jtype, jtable, jcond) in joins {
            sql.push_str(&format!(" {} JOIN {} ON {}", jtype.to_uppercase(), jtable, jcond));
        }

        // WHEREs
        if !wheres.is_empty() {
            sql.push_str(" WHERE ");
            let mut where_clauses = Vec::new();
            for (col, op, val_str) in wheres {
                let ph = self.get_placeholder(dialect, param_idx);
                param_idx += 1;
                where_clauses.push(format!("{} {} {}", col, op, ph));
                params.push(val_str);
            }
            sql.push_str(&where_clauses.join(" AND "));
        }

        // ORDER BY
        if !order_by.is_empty() {
            sql.push_str(" ORDER BY ");
            let order_clauses: Vec<String> = order_by
                .into_iter()
                .map(|(c, dir)| format!("{} {}", c, dir.to_uppercase()))
                .collect();
            sql.push_str(&order_clauses.join(", "));
        }

        // LIMIT & OFFSET
        if let Some(l) = limit {
            sql.push_str(&format!(" LIMIT {}", l));
        }
        if let Some(o) = offset {
            sql.push_str(&format!(" OFFSET {}", o));
        }

        Ok((sql, params))
    }

    /// Compiles INSERT query
    pub fn compile_insert(&self, table: &str, columns: Vec<String>, dialect: &str) -> PyResult<String> {
        let placeholders: Vec<String> = (1..=columns.len())
            .map(|i| self.get_placeholder(dialect, i))
            .collect();

        let cols_str = columns.join(", ");
        let ph_str = placeholders.join(", ");

        let mut sql = format!("INSERT INTO {} ({}) VALUES ({})", table, cols_str, ph_str);
        if dialect.to_lowercase().contains("postgres") {
            sql.push_str(" RETURNING *");
        }
        Ok(sql)
    }

    /// Compiles UPDATE query for dirty attributes
    pub fn compile_update(
        &self,
        table: &str,
        columns: Vec<String>,
        pk_col: &str,
        dialect: &str,
    ) -> PyResult<String> {
        let mut set_clauses = Vec::new();
        let mut idx = 1;
        for col in &columns {
            set_clauses.push(format!("{} = {}", col, self.get_placeholder(dialect, idx)));
            idx += 1;
        }

        let pk_ph = self.get_placeholder(dialect, idx);
        let sql = format!(
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
