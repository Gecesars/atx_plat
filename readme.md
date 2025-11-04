# ATXCOVER

**Microwave and RF Synthesis, Analysis, and Design Tools**

---

## 📡 Project Overview

**ATXCOVER** is a comprehensive suite of tools designed for the synthesis, analysis, and design of microwave and RF systems. It integrates various modules to facilitate the development and management of RF components and systems, providing engineers with a robust platform for their projects.

---

## 🧰 Features

- **Antenna Design and Analysis**: Tools for designing and simulating various antenna configurations.
- **RF Component Simulation**: Modules for simulating RF components such as filters, amplifiers, and mixers.
- **Signal Processing Utilities**: Functions for analyzing and processing RF signals.
- **Data Visualization**: Interactive charts and graphs for visualizing simulation results.
- **SNMP Management**: Integration with SNMP for monitoring and managing networked RF devices.
- **Coverage Planner**: Dual-overlay (dBµV/m & dBm) map with ITU-R P.452 loss breakdown, tilt-aware antenna gains and receiver management.
- **Automatic Context Data**: TX municipality/elevation discovery (SRTM + reverse geocoding) and climate snapshots agregated from the last 360 days via Open-Meteo.
- **Professional UX**: Sticky navigation, polished control panel, live spinners and climate/location warnings to highlight pending updates.
- **Azimute Inteligente**: Ajuste fino do rumo da antena com feedback instantâneo (linha pontilhada orientada e normalização automática 0-359°).

---

---


### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Gecesars/ATXCOVER.git
   cd ATXCOVER
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   python app.py
   ```

   The application will be accessible at `http://localhost:5000`.

---

## 🐳 Docker Deployment

To run the application in a Docker container:

```bash
docker build -t atxcover .
docker run -p 5000:5000 atxcover
```

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/Gecesars/ATXCOVER/blob/main/LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

---

## 📬 Contact

For questions or suggestions, please open an issue on the [GitHub repository](https://github.com/Gecesars/ATXCOVER/issues).
