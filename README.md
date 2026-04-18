# STAT5243 Project 3: A/B Testing for Sensitive Purchase Assistant

##  Project Overview
This project investigates how different assistant framings affect user behavior and perception in a sensitive purchase context (e.g., acne treatment products). We implement and evaluate an A/B test comparing:

- **Control (A):** Human advisor
- **Treatment (B):** Private AI assistant

The goal is to assess whether a private AI assistant improves:
- Willingness to seek help
- Perceived embarrassment
- Behavioral engagement (CTR, add-to-cart)

---

##  Research Design
- **Experimental Unit:** Browser session
- **Assignment:** Randomized (50/50 split between A and B)
- **Platform:** Shiny for Python web application
- **Data Sources:**
  - Survey (Likert scale: willingness & embarrassment)
  - Google Analytics 4 (CTR, add-to-cart, funnel)

---

##  Key Features
- Real-time A/B assignment via frontend logic
- Integrated survey at the end of user flow
- Google Analytics tracking for behavioral metrics
- Clean UI simulating a real e-commerce environment
- Full statistical analysis pipeline (see report)

---

##  Project Structure
```

Project 3/
│
├── app.py # Main Shiny application
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
├── www/ # Frontend assets (JS, CSS, images)
├── photo/ # Static images
├── logs/ # Logging directory
├── rsconnect-python/ # Deployment config
├── Project 3.pdf # Final report
└── README.md # Project documentation

````

---

##  Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-link>
cd Project\ 3
````

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

##  Running the Application

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:8000
```

---

##  Live Deployment

If available, access the deployed app here:

👉 [https://5243freya.shinyapps.io/stat5243-project3/](https://5243freya.shinyapps.io/stat5243-project3/)

---

##  Data Collection

* **Time Period:** April 10 – April 17, 2026
* **Recruitment:** Distributed via personal networks (classmates, friends, family)
* **Survey:**

  * Appears at the end of user interaction
  * Voluntary participation
* **Behavioral Data:**

  * Collected via Google Analytics 4
  * Metrics:

    * Impressions
    * Clicks (assistant interaction)
    * Add-to-cart events

---

##  Reproducibility

To reproduce the full workflow:

1. Run the app locally
2. Interact with both A/B variants
3. Collect survey and GA data
4. Use statistical methods described in the report:

   * Welch t-test
   * Mann–Whitney U
   * Cohen’s d
   * Two-proportion z-test
   * Power analysis

> Note: Google Analytics data requires access to the configured GA4 property.

---

##  Dependencies

Key libraries used:

* `shiny` (Shiny for Python)
* `scipy`
* `statsmodels`
* `numpy`
* `pandas`

Full list in `requirements.txt`.

---

##  Limitations

* Convenience sampling (not fully representative)
* Session-level randomization (not user-level)
* Behavioral data underpowered for small effects
* GA tracking depends on correct event instrumentation

---

##  Authors

* Freya Chen
* Yunjie Huang
* Pingyu Zhou
* Kaifeng Si

---

##  Report

See full analysis and results in:

📎 `Final_report.pdf`

---

##  Notes

This project is developed for **STAT5243** and demonstrates:

* Experimental design
* A/B testing implementation
* Statistical inference
* Data-driven product insights



## Troubleshooting

- No realtime hits: verify property / `G-` ID, data filters, ad blockers.
- Deploy fails: ensure `rsconnect` is from Python 3.12/3.11, not 3.14.
