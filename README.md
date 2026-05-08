# 🚨 AIDRA — Adaptive Intelligent Disaster Response Agent

> A hybrid AI simulation system for real-time disaster response planning, built from scratch using search algorithms, constraint satisfaction, machine learning, and fuzzy logic.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![AI](https://img.shields.io/badge/AI-Hybrid%20System-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Course](https://img.shields.io/badge/Course-AIC--201-purple)

---

## 📌 Overview

AIDRA simulates an intelligent emergency response system operating in a dynamic urban disaster environment. A live animated city grid shows fires spreading, roads collapsing, and ambulances navigating in real time — while an AI agent coordinates search, planning, resource allocation, and victim prioritization autonomously.

Built for the **AIC-201 Complex Computing Problem (CCP)** under **Dr. Arshad Farhad**, Semester 5-A.

**Developed by:**
- [Your Name] — [@yourgithub](https://github.com/yourgithub)
- [Partner Name] — [@partnergithub](https://github.com/partnergithub)

---

## 🎬 Demo

> *(Add a screen recording GIF or screenshot here)*

```
[INSERT DEMO GIF HERE]
```

---

## 🧠 AI Components

AIDRA integrates **6 AI techniques** into a single coherent decision-making pipeline:

### 1. 🗺️ Search & Pathfinding
Four algorithms implemented **from scratch**, run and compared on every mission:

| Algorithm | Strategy | Nodes Explored | Optimal? |
|---|---|---|---|
| **BFS** | Breadth-First | High | ✅ Yes (unweighted) |
| **DFS** | Depth-First | Variable | ❌ No |
| **Greedy Best-First** | Heuristic only | Low | ❌ No |
| **A\*** | Cost + Heuristic | Moderate | ✅ Yes |

A second variant, **A\* Safe**, applies a fire-penalty cost function to produce routes that avoid hazard zones. Manhattan distance is used as the heuristic.

---

### 2. 🌡️ Fuzzy Logic Router
Decides between the **fastest route** (through hazard zones) vs. the **safest route** (longer, avoids fire) using three fuzzy input variables:

- **Hazard level** → `low / medium / high`
- **Distance ratio** (safe path / fast path cost)
- **Victim urgency** → `low / high`

The Fuzzy Router outputs a score and a human-readable justification for every routing decision.

---

### 3. 🤖 Machine Learning — Survival Prediction
Three classifiers trained **from scratch** (no scikit-learn) on a 300-record synthetic dataset:

| Model | Input Features | Output |
|---|---|---|
| **K-Nearest Neighbors** (k=3) | health, urgency, distance, risk | Survival probability |
| **Naive Bayes** (Gaussian) | health, urgency, distance, risk | Survival probability |
| **Decision Tree** (CART, depth=5) | health, urgency, distance, risk | Survival probability |

An **ensemble average** of all three probabilities informs victim prioritization. Full evaluation metrics (Accuracy, Precision, Recall, F1, Confusion Matrix) are computed on an 80/20 train-test split.

---

### 4. 📐 Constraint Satisfaction Problem (CSP)
Ambulance and kit allocation modelled as a CSP:

- **Variables:** which ambulance serves each victim
- **Constraints:** max 2 victims per ambulance simultaneously; total kits ≤ 10
- **Solver:** Backtracking with **MRV (Minimum Remaining Values)** heuristic + forward checking
- Reports MRV backtracking count vs. plain backtracking to quantify heuristic improvement

---

### 5. 🔥 Simulated Annealing (Local Search)
Optimizes the rescue tour order across all victims — minimizing total travel cost.

- Initial random tour, temperature T = 80, cooling rate = 0.93
- Swap-based neighbourhood function
- Accepts worse solutions probabilistically to escape local optima

---

### 6. 🧩 Priority Scoring & Dynamic Replanning
Each victim receives a composite priority score:

```
score = urgency × 3 + (100 − health) / 10 + (1 − survival_probability) × 5
```

When the environment changes (road block, fire spread, new victim, kit depletion), the agent **replans and reallocates** automatically with a logged justification.

---

## 🗺️ Environment Model

```
Grid Size : 9 × 13 cells
Rescue Base : (4, 4)
Hospitals : (1,11)  (4,11)
Fire Zones : 13 pre-set cells (spread dynamically at 8% probability per tick)
Blocked Roads : Dynamic (initial + random events)
Victims : 5 initial (2 critical, 2 moderate, 1 minor) + dynamic spawns (max 8 total)
Ambulances : 2
Medical Kits : 10
```

---

## 📊 KPIs Tracked

| Metric | Description |
|---|---|
| Victims Saved | Count rescued out of total |
| Average Rescue Time | Mean time per rescue (seconds) |
| Risk Exposure Score | Fraction of path cells inside fire zones |
| Path Optimality Ratio | Cost found / best known cost across algorithms |
| Resource Utilization | Ambulances / kits used effectively |
| ML Metrics | Accuracy, Precision, Recall, F1, Confusion Matrix |
| Algorithm Runtimes | Per-algorithm timing in milliseconds |

---

## 🖥️ GUI Features

- **Live animated city map** — fire, routes, ambulances, victims rendered in real time
- **Search expansion visualization** — watch BFS/A\* explore the grid cell by cell
- **Algorithm comparison panel** — nodes explored, path cost, runtime for all 4 algorithms
- **Fuzzy logic panel** — membership values and decision reasoning per rescue
- **KPI dashboard** — live-updated metrics with a bar chart per rescue
- **Decision log** — timestamped event log for every agent action and replan
- **Speed slider** — control simulation speed
- **Performance report viewer** — CSV report accessible from within the GUI

---

## 📁 Project Structure

```
AIDRA/
├── AIDRA_v4_fixed.py          # Main application (single-file)
├── aidra_survival_data.csv    # Auto-generated training dataset (300 records)
├── aidra_performance_report.csv  # Generated after each simulation run
└── README.md
```

---

## ⚙️ Requirements & Setup

### Prerequisites
- Python 3.8 or higher
- Tkinter (included in standard Python on Windows/macOS; see below for Linux)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AIDRA.git
cd AIDRA

# No external dependencies required — pure Python standard library only
# tkinter is included with most Python distributions

# Linux users: install tkinter if missing
sudo apt-get install python3-tk

# Run the simulation
python AIDRA_v4_fixed.py
```

---

## 🚀 How to Use

1. **Run** the script — the GUI launches automatically
2. **Select an algorithm** from the dropdown (A\*, BFS, DFS, Greedy)
3. **Toggle** search expansion visualization on/off
4. **Adjust speed** using the slider
5. **Press ▶ START** to deploy the agent
6. Watch the agent navigate the city, respond to events, and log decisions
7. **Press ■ STOP** to pause or **↺ RESET** to start fresh
8. **Open Report** to view the saved CSV performance summary

---

## 🔬 Key Design Decisions

**Why ensemble ML instead of one model?**
No single model was clearly dominant. Averaging KNN, Naive Bayes, and Decision Tree predictions produces a more robust survival estimate that directly feeds into prioritization scoring.

**Why Fuzzy Logic over a threshold rule?**
Disaster scenarios involve inherently imprecise data. Fuzzy membership functions model the gradual transition between "safe enough" and "too dangerous" more realistically than binary if-else rules.

**Why Simulated Annealing for tour optimization?**
The rescue tour problem is NP-hard in general. SA provides near-optimal solutions quickly without exhaustive search, and its probabilistic acceptance of worse solutions prevents getting stuck in poor orderings.

**Why MRV in CSP?**
The MRV heuristic consistently reduces backtracking by assigning the most-constrained ambulance slot first, which the system measures and reports on every run.

---

## 📋 Academic Context

This project was built to satisfy the **CCP (Complex Computing Problem)** requirements for AIC-201, which maps to the following Graduate Attributes:

| Requirement | Implementation |
|---|---|
| Multiple AI components integrated | Search + CSP + ML + Fuzzy + SA |
| Dynamic environment + replanning | Road blocks, fire spread, new victims, kit depletion |
| Search visualization / traceability | Live grid expansion + algorithm comparison panel |
| Performance KPIs | 5 metrics tracked per run + ML evaluation |
| Comparative evaluation | 4 search algorithms, CSP with/without MRV, 3 ML models |

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

Built under the guidance of **Dr. Arshad Farhad**, AIC-201, Semester 5-A.
All AI components (KNN, Naive Bayes, Decision Tree, Fuzzy Logic, CSP, A\*, SA) implemented from scratch using Python's standard library only.
