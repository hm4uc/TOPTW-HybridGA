# Personalized Tourist Trip Design Algorithm - Hybrid Genetic Algorithm

![Python](https://img.shields.io/badge/Backend-Python%20FastAPI-blue)
![Flutter](https://img.shields.io/badge/Mobile-Flutter-02569B)
![License](https://img.shields.io/github/license/hm4uc/TOPTW-HybridGA)

## 📖 Introduction
This repository contains the source code for the Bachelor Thesis: **"Building a Context-Aware Tourist Trip Planner System based on Hybrid Genetic Algorithm"**.

The system solves the **Team Orienteering Problem with Time Windows (TOPTW)** by focusing on user personalization. Instead of using static scores, the algorithm optimizes the itinerary based on individual user interests (User-Dependent Scores), Budget, and Time Constraints.

## 🚀 Key Features
* **User-Centric Optimization:** Maximizes total trip score based on user preferences (Culture, Food, Nature, etc.).
* **Hybrid Genetic Algorithm (HGA):** * Integrates **Genetic Algorithm (GA)** for global exploration.
    * Incorporates **2-opt Local Search (Smart Mutation)** for fast convergence and route refinement.
* **Constraints Handling:** Efficiently handles Hard Constraints:
    * 💰 Budget Limits.
    * ⏰ Time Budget (Start/End time).
    * ⏳ Time Windows (Opening/Closing hours of POIs).
* **Cross-Platform Mobile App:** Built with Flutter for visualizing routes on Google Maps.

## 🛠 Tech Stack

### Backend (Computational Core)
* **Language:** Python 3.13.9
* **Framework:** FastAPI
* **Libraries:** NumPy, Uvicorn.
* **Algorithm:** Custom implementation of Hybrid GA using OOP.

### Mobile (Client)
* **Framework:** Flutter (Dart)
* **Maps:** Google Maps SDK
* **State Management:** Bloc

## 📂 Project Structure

```text
TOPTW-HybridGA/
├── backend/                # Python Server & Algorithm
│   ├── app/
│   │   ├── main.py         # API Entry point
│   │   ├── models/         # Data structures (POI, UserProfile)
│   │   ├── algorithms/     # Genetic Algorithm Core
│   │   │   ├── ga.py       # Main Loop
│   │   │   ├── operators.py# Crossover & Selection
│   │   │   └── hybrid.py   # 2-opt Local Search (Smart Mutation)
│   ├── data/               # Solomon Benchmark & Real POI Data
│   └── requirements.txt    # Python dependencies
│
├── mobile/                 # Flutter Application
│   ├── lib/
│   │   ├── screens/        # UI Screens (Input, Map)
│   │   ├── services/       # API Connectors
│   │   └── main.dart
│   └── pubspec.yaml
└── README.md
```

## 📝 License

Distributed under the MIT License. See LICENSE for more information.

**Author:** Hoàng Minh Đức

**Faculty of Information Technology - VNU UET**
