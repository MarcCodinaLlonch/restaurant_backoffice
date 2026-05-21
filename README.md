# 🍽️ Assignment — Restaurant BackOffice

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Rich](https://img.shields.io/badge/CLI-Rich-blueviolet.svg)](https://rich.readthedocs.io/)

## 📖 Description

This is an interactive console application developed in Python to manage a restaurant's *Back Office*. This academic project is designed following a **Layered Architecture** and strictly implements the **Repository** and **Unit of Work (UoW)** design patterns.

The application allows you to manage employees, categories, allergens, dishes, menus, and sales. It demonstrates the complete management of relational databases in a practical and structured way, including 1:1, 1:N, N:M, and N:M relationships with extra attributes. The User Interface (UI) uses the **Rich** library to display tables, panels, and text with a professional format in the terminal.

## 👤 Authorship

- **Author:** Marc Codina Llonch
- **Subject:** M0488 — Multiplatform Application Development (DAM)

## 📚 Table of Contents

1. [System Requirements](#️-system-requirements)
2. [Main Features](#-main-features)
3. [Installation Guide](#-installation-guide)
4. [User Guide](#-user-guide)

## ⚙️ System Requirements

| Requirement | Detail |
|---|---|
| Operating System | Windows, macOS, or Linux |
| Runtime Environment | [Python 3.10 or higher](https://www.python.org/downloads/) |
| Database | PostgreSQL (Development environment) or SQLite (Test environment) |

## ✨ Main Features

- **Architecture:** Strict separation between the UI (Presentation) and the domain/data. The UI never executes SQL sentences or interacts directly with SQLAlchemy.
- **Relationship Management:**
  - **1:1 (Employees ↔ Credentials):** Atomic management of users with secure passwords (SHA-256 hash) and automatic cascade deletion (`delete-orphan`).
  - **1:N (Categories → Dishes):** Maintenance of referential integrity where a dish must belong to an existing category.
  - **N:M (Dishes ↔ Allergens / Menus ↔ Dishes):** Advanced use of the ORM to manage intermediate tables transparently using the `.append()` method.
  - **N:M with attributes (Sales):** Modeling of a specific entity (`Sale`) with a composite primary key `(id_menu, id_employee, sale_date)` and its own attributes (`quantity_sold`).
- **Secure Transactions:** Use of the **Unit of Work** pattern to ensure that complex operations are saved atomically (either completely saved or rolled back).
- **User Interface:** Use of **Rich** to generate visual panels, structured data tables, and color-coded status messages.
- **Defensive Programming:** Input validation in the console (e.g., using `.isdigit()`) to prevent unexpected program crashes.

## 🚀 Installation Guide

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPOSITORY_URL>
   cd restaurant_backoffice
   ```
2. **Create and activate a virtual environment:**
   ```bash
   # Windows:
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/macOS:
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure the environment:**
   Make sure to have a `.env` file in the root folder with the `ENVIRONMENT` variable pointing to your environment (e.g., `development` for PostgreSQL or `test` for in-memory SQLite):
   ```env
   ENVIRONMENT=development
   ```

## 📖 User Guide

| Action | How to do it |
|---|---|
| Start the application | Run `python app.py` in the terminal. |
| Navigate the menu | Type the number of the desired option and press `Enter`. |
| Go back | Press `0` from any submenu. |
| Cancel modifications | Leave the text blank (press `Enter` without text) in the update forms. |