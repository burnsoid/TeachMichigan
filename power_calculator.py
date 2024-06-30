import streamlit as st
import numpy as np
import pandas as pd
from statsmodels.stats.power import TTestIndPower
from statsmodels.stats.power import tt_ind_solve_power

# Set page config
st.set_page_config(page_title="Power Calculator", page_icon="📊", layout="wide")

def calculate_power(n_teachers, outcome_share, effect_size, students_per_teacher=22, use_clustering=False, icc=0):
    n_treatment = int(n_teachers * outcome_share)
    n_control = n_treatment  # Equal number in comparison group
    
    if use_clustering and icc > 0:
        # Adjust for clustering
        deff = 1 + (students_per_teacher - 1) * icc
        effective_n_treatment = n_treatment * students_per_teacher / deff
        effective_n_control = n_control * students_per_teacher / deff
    else:
        effective_n_treatment = n_treatment * students_per_teacher
        effective_n_control = n_control * students_per_teacher
    
    power_analysis = TTestIndPower()
    power = power_analysis.solve_power(
        effect_size=effect_size,
        nobs1=effective_n_treatment,
        ratio=1,  # Equal sized groups
        alpha=0.05,
        alternative='two-sided'
    )
    return power

def calculate_sample_size(effect_size, outcome_share, students_per_teacher=22, use_clustering=False, icc=0):
    if use_clustering and icc > 0:
        # Adjust for clustering
        deff = 1 + (students_per_teacher - 1) * icc
    else:
        deff = 1
    
    n = tt_ind_solve_power(effect_size=effect_size, alpha=0.05, power=0.8, ratio=1, alternative='two-sided')
    total_teachers = int(np.ceil((n * deff) / (students_per_teacher * outcome_share)))
    return total_teachers * 2  # Double for equal sized intervention and comparison groups

st.title('Interactive Power Calculator for TeachMichigan Evaluation')

st.write("""
Statistical power is a crucial concept in research design that measures the likelihood of detecting a true effect when it exists. If a study evaluating an intervention is underpowered, there could be a positive effect but the analysis will likely not be able to detect it. Statistical power depends on several factors: sample size, effect size, significance level, variation in thte variables of interest, and study design. Of these, study design and sample size are the factors most under the control of the intervention designers and researchers. It is therefore important to design interventions such that they can be evaluated in a straightforward manner and ensure a sample size that gives evaluators the best chance to detect an effect. 

This power calculator allows users to investigate the issue of power within the context of TeachMichigan by 1) estimating the level of statistical power for a given analysis, and 2) estimating the number of fellows that would be needed to achieve adequate statistical power.

To simplify power calculations, this calculator assumes:
- Conventional levels of statistical significance (0.05) and power (0.80)
- Equal-sized treatment and comparison groups
- Two-sided tests
- Equal variance between groups
- 22 students per teacher (approximately the average in Michigan)

For TeachMichigan, it's important to consider that while most outcomes are measured at the student level, the intervention is implemented at the teacher level. This "clustering" of students in classrooms can be accounted for using the intraclass correlation coefficient (ICC), which measures the similarity of outcomes within teacher groups. The implication of this for statistical power is that a higher ICC, meaning greater similarity of outcomes within teacher groups, typically reduces the effective sample size of an analysis and therefore statistical power.

For context on effect sizes in education research, Kraft (2019) analyzed nearly 2000 effect sizes and suggests the following framework, which roughly divides that distribution of effect sizes into thirds:
- Small effect: < 0.05
- Medium effect: 0.05 to < 0.20
- Large effect: ≥ 0.20

Reference: Kraft, M. A. (2019). Interpreting Effect Sizes of Education Interventions. (EdWorkingPaper: 19-10). Retrieved from Annenberg Institute at Brown University: http://www.edworkingpapers.com/ai19-10
""")

calculation_type = st.radio("Select calculation type:", ("Calculate Power", "Calculate Required Sample Size"))

if calculation_type == "Calculate Power":
    n_teachers = st.slider('Number of TeachMichigan fellows:', 0, 1000, 25)
    outcome_share = st.slider('Percentage of fellows associated with student outcomes:', 0, 100, 100) / 100

    st.markdown(f'**Total number of teachers in the evaluation: {n_teachers * 2}**')
    st.markdown(f'**Number of teachers in intervention group: {n_teachers}**')
    st.write(f'Number of teachers in comparison group: {n_teachers}')
    st.write(f'Effective number of teachers in intervention group: {int(n_teachers * outcome_share)}')
    st.write(f'Effective number of teachers in comparison group: {int(n_teachers * outcome_share)}')

else:
    effect_size = st.slider('Effect Size:', 0.03, 0.24, 0.12, 0.03)
    outcome_share = st.slider('Percentage of fellows associated with student outcomes:', 0, 100, 100) / 100

use_clustering = st.radio("Account for clustering in calculations?", ("No", "Yes"))

if use_clustering == "Yes":
    st.write("""
    Intraclass Correlation Coefficient (ICC):
    The ICC measures the degree of correlation between observations within the same cluster (in this case, students within a teacher's classroom).
    - A higher ICC (closer to 0.5) indicates that students within the same classroom are more similar to each other.
    - A lower ICC (closer to 0) indicates that students within the same classroom are less similar to each other.
    - Use a higher ICC if some teachers are believed to be meaningfully more effective than others within the treatment and control groups.
    - Use a lower ICC if student outcomes are expected to be more independent of their teacher, or if teacher effectiveness is believed to be relatively uniform within the treatment and control groups.
    - Note: An ICC can be as high as 1, but this calculator stops at 0.5 to allow the user to more easily make small adjustments with the slider.

    Accounting for clustering (by using an ICC > 0) typically reduces the effective sample size, which can result in lower power or require a larger sample size.
    """)

    icc = st.slider('Intraclass Correlation Coefficient (ICC):', 0.0, 0.5, 0.2, 0.01)

if calculation_type == "Calculate Power":
    results = []
    for effect_size in np.arange(0.03, 0.25, 0.03):
        power = calculate_power(n_teachers, outcome_share, effect_size, use_clustering=(use_clustering=="Yes"), icc=icc if use_clustering=="Yes" else 0)
        results.append({'Effect Size': effect_size, 'Power': power})

    results_df = pd.DataFrame(results)
    st.write('Power for different effect sizes:')
    
    def color_power(val):
        color = 'green' if val >= 0.8 else 'black'
        return f'color: {color}'
    
    st.dataframe(results_df.style.format({'Effect Size': '{:.2f}', 'Power': '{:.3f}'}).applymap(color_power, subset=['Power']))

else:
    required_teachers = calculate_sample_size(effect_size, outcome_share, use_clustering=(use_clustering=="Yes"), icc=icc if use_clustering=="Yes" else 0)
    st.markdown(f'**Required number of teachers (total for both intervention and comparison groups): {required_teachers}**')
    st.markdown(f'**Minimum number of fellows needed: {required_teachers // 2}**')

st.write("""

Understanding these results:
- For power calculations: Higher power (closer to 1) indicates a greater likelihood of detecting a true effect if it exists. Typically, a power of 0.80 or higher is considered adequate.
- For sample size calculations: The result shows the total number of teachers needed (split equally between intervention and comparison groups) to achieve 80% power for detecting the specified effect size.

""")
