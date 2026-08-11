<div align="center">
  <img width="254" height="254" alt="logo" src="https://github.com/user-attachments/assets/32b24c36-eb89-4736-b288-9745280f78c5" />
</div>

# 🌖 LunarPhaseORM

> **Smart Sync. Zero N+1. Pure Async.**

LunarPhaseORM is an async-first ORM for Python.

It is built for applications where database performance matters, with
automatic change tracking, eager loading, and async database operations.

## ✨ Features

- ⚡ **Async-first** — built around Python's `async`/`await` and designed
  for async frameworks such as FastAPI, Sanic, and Litestar.
- 🧠 **Smart change tracking** — only fields that have changed are included
  in `UPDATE` queries.
- 🚫 **Avoid N+1 queries** — relationships can be loaded in batches instead
  of triggering a query for every object.
- 🛡️ **Type-friendly models** — define your models using normal Python
  type hints with good IDE support.

## 📦 Installation

Install LunarPhaseORM from PyPI:

```bash
pip install lunarphase-orm
