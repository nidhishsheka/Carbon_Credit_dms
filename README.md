# Carbon Emission & Carbon Credit Management System

A database-driven web application for tracking industrial carbon emissions, calculating emission limits, and determining carbon credits based on environmental policies.

The system records emission-producing activities, computes emissions using emission factors, and compares actual emissions against allowed limits to evaluate carbon credit eligibility.

---

## Features

- Add and manage establishments
- Record emission-producing activities
- Automatic emission calculation using emission factors
- Track baseline emissions and allowed limits
- Generate carbon credit reports
- Dashboard showing system statistics

---

## Key Calculations

### Emission Calculation

```
Emission = Quantity × Emission Factor
```

Example

```
500 kg coal × 2.42 = 1210 kg CO₂
```

### Carbon Credit

```
Carbon Credit = (Allowed Limit − Actual Emission) / 1000
```

1 Carbon Credit = **1 tonne CO₂ equivalent (tCO₂e)**

---

## Tech Stack

- Backend: Python (Flask)
- Database: SQLite
- Frontend: HTML, CSS
- Tools: VS Code

---

## System Architecture

```
User (Browser)
      │
      ▼
Frontend (HTML / CSS)
      │
      ▼
Flask Application (Python Backend)
      │
      ▼
SQLite Database
      │
      ▼
Carbon Emission Calculations
```

---

## Data Flow

```
Add Establishment
      ↓
Record Activity Data
      ↓
Emission Calculation
(Quantity × Emission Factor)
      ↓
Emission Records Stored
      ↓
Compare With Allowed Limit
      ↓
Carbon Credit Report Generated
```

---

## Database Entities

Main tables used in the system:

```
Establishment
Emission_Source
Emission_Factor
Activity_Data
Emission_Record
Baseline_Emission
Allowed_Limit
Carbon_Credit
Reduction_Policy
```

---

## Project Structure

```
dms_proj
│
├── app.py
├── cc.db
├── README.md
│
├── templates
│   ├── dashboard.html
│   ├── add_entity.html
│   ├── add_activity.html
│   ├── emissions.html
│   └── report.html
│
└── static
    └── style.css
```

---

## Running the Project

Install Flask

```
pip install flask
```

Run the application

```
python3 app.py
```

Open in browser

```
http://127.0.0.1:5000
```

---

## Purpose

This project was developed as part of a **Database Management Systems (DBMS) course project** to demonstrate:

- ER modeling
- relational database implementation
- SQL joins and derived calculations
- integration of databases with a web interface