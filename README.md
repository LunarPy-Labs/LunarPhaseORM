<div align="center">
  <img width="254" height="254" alt="logo" src="https://github.com/user-attachments/assets/32b24c36-eb89-4736-b288-9745280f78c5" />
</div>

# LunarPhaseORM

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)
[![PyPI Version](https://img.shields.io/badge/pypi-v0.1.0-orange.svg)](https://pypi.org/)

> **Smart Sync. Zero N+1. Pure Async.**

**LunarPhaseORM** is a next-generation Object-Relational Mapper (ORM) for Python engineered specifically for high-performance backend architectures. Built ground-up with an *async-native* paradigm, LunarPhaseORM eliminates common bottlenecks found in traditional ORMs, such as the N+1 query problem and slow data state synchronization.

---

## ✨ Key Features

* **⚡ Pure Async Native:** Built natively using `async`/`await` primitives without blocking I/O, perfectly suited for modern frameworks like FastAPI, Sanic, or Litestar.
* **🧠 Smart Sync & State Tracking:** Tracks and detects attribute changes (*dirty tracking*) with precision so that `UPDATE` queries target only modified fields.
* **🚫 Zero N+1 Query Problem:** Features an intelligent eager-loading and batching mechanism that seamlessly resolves relational data without causing query spikes.
* **🛡️ Type-Safe & Expressive Schema:** Clean, explicit schema definitions with full Python type-hinting support for maximum IDE autocompletion and developer experience.

---

## 📦 Installation

Install via `pip`:

```bash
pip install lunarphase-orm
