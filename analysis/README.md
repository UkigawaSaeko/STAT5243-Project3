# 📊 A/B Test Statistical Analysis (Project 3)

## 🔍 Overview
This project presents a comprehensive statistical analysis of an A/B test comparing two design variants (**Group A vs Group B**).

The analysis evaluates both:
- **User perception** (survey-based metrics)
- **User behavior** (interaction-based metrics)

---

## 📁 Data Sources

The analysis is based on three datasets:

| Dataset | Description |
|--------|------------|
| `willingness.csv` | User willingness ratings (1–5 scale) |
| `embarrassment.csv` | User embarrassment ratings (1–5 scale) |
| `Behavior.csv` | Behavioral metrics (impressions, clicks, add-to-cart) |

---

## 🧪 Methods

To ensure robust and reliable conclusions, we applied:

### 📌 Statistical Tests
- Two-sample t-test (mean comparison)
- Mann–Whitney U test (non-parametric robustness check)

### 📌 Effect & Uncertainty
- Cohen’s d (effect size)
- 95% Confidence Intervals

### 📌 Behavioral Analysis
- Proportion z-test (CTR & conversion rate)
- Funnel analysis (Impression → Click → Purchase)

---

## 📈 Key Results

- ✅ **Willingness**: Group B significantly increases user willingness  
- ✅ **Embarrassment**: Group B significantly reduces user embarrassment  
- ⚠️ **Behavior Metrics**:
  - CTR and conversion rate improve under Group B  
  - However, results are **not statistically significant**

---

## 💡 Cross-Metric Insight

The experiment shows a **clear improvement in user perception**, which aligns with **positive but inconclusive behavioral trends**.

This suggests that:
> Improved perception may translate into behavioral gains, but larger sample sizes are required to confirm the effect.

---

## 🧾 Conclusion

Overall, **Group B is the superior design**. It delivers statistically significant improvements in both willingness and embarrassment, supported by large effect sizes.

Although behavioral improvements are not statistically significant, their consistent positive direction combined with limited statistical power suggests that the treatment is promising.

Further experiments with larger sample sizes are recommended to validate its impact on user behavior.

---

## ▶️ How to Run

Install dependencies:

```bash
pip install pandas numpy scipy statsmodels matplotlib
