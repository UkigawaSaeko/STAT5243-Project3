# A/B Test Statistical Analysis (Project 3)

## Overview
This project conducts a statistical analysis of an A/B test comparing two design variants (Group A vs Group B).

The analysis focuses on:
- User perception (willingness & embarrassment surveys)
- User behavior (click-through rate and conversion)

## Data
The analysis is based on three datasets:
- willingness.csv: survey responses on user willingness (1–5 scale)
- embarrassment.csv: survey responses on user embarrassment (1–5 scale)
- Behavior.csv: behavioral metrics (impressions, clicks, add-to-cart)

## Methods
We apply multiple statistical techniques to ensure robust conclusions:

- Two-sample t-test (mean comparison)
- Mann–Whitney U test (robustness check)
- Effect size (Cohen’s d)
- Confidence intervals (95%)
- Proportion z-test (CTR & conversion rate)
- Funnel analysis (impression → click → purchase)

## Results Summary
- Group B significantly improves willingness
- Group B significantly reduces embarrassment
- Behavioral improvements (CTR, conversion) are positive but not statistically significant

## Conclusion
Group B demonstrates strong improvements in user perception and promising behavioral trends.  
Further experiments with larger sample sizes are recommended to confirm behavioral effects.

## How to Run
Install dependencies:

pip install pandas numpy scipy statsmodels matplotlib

Then run:
- statistical_analysis.ipynb
