import streamlit as st
import pandas as pd
import numpy_financial as npf
import matplotlib.pyplot as plt

# Streamlit app
st.title("Retirement Cashflow Calculator")

# Input values
with st.sidebar:
    start_age = st.number_input("Start Age", value=25, step=1)
    retire_age = st.number_input("Retirement Age", value=60, step=1)
    death_age = st.number_input("Death Age", value=80, step=1)
    initial_salary = st.number_input("Initial Salary", value=15000, step=1000)
    initial_wealth = st.number_input("Initial Wealth", value=0, step=1000)
    contribution_rate = st.slider("Contribution Rate (in %)", min_value=0.0, max_value=50.0, value=8.0, step=0.1) / 100
    employer_contribution_rate = st.slider("Employer Contribution Rate (in %)", min_value=0.0, max_value=50.0, value=8.0, step=0.1) / 100
    inflation_rate = st.slider("Inflation Rate (in %)", min_value=0.0, max_value=10.0, value=0.0, step=0.1) / 100
    replacement_cost_lst = st.multiselect("Select Replacement Cost(s) (Fraction of Salary)", [15, 20, 25,  30,35,  40,45 ,  50,55,  60, 70, 80], default=[ 15, 20,25, 30, ])
    replacement_cost_lst = [x / 100 for x in replacement_cost_lst]  # Convert to fraction
    salary_growth_rate = st.slider("Salary Growth Rate (in %)", min_value=0.0, max_value=10.0, value=7.5, step=0.1) / 100
    discount_rate = st.slider("Return after Retire (in %)", min_value=0.0, max_value=10.0, value=0.0, step=0.1) / 100
    calculate = st.button("Submit")

if calculate:
    # Calculated parameters
    working_years = retire_age - start_age
    retirement_years = death_age - retire_age
    retirement_months = retirement_years * 12

    # Function to calculate retirement cashflow
    def calculate_retirement_cashflow(initial_salary, initial_wealth, contribution_rate, employer_contribution_rate, salary_growth_rate, working_years, 
                                      replacement_cost, inflation_rate, discount_rate, 
                                      retire_age, retirement_months):
        final_salary = initial_salary * ((1 + salary_growth_rate) ** (working_years-1))
        retirement_monthly_expenses = final_salary * replacement_cost

        adjusted_retirement_monthly_expenses = [
            retirement_monthly_expenses * (1 + inflation_rate) ** (i // 12) for i in range(retirement_months)
        ]

        adjusted_retirement_df = pd.DataFrame({
            "Age": [retire_age + (i // 12) for i in range(retirement_months)],
            "Month": range(1, retirement_months + 1),
            "Monthly_Expenses": adjusted_retirement_monthly_expenses
        })

        adjusted_retirement_df["Cumulative_Expenses"] = adjusted_retirement_df["Monthly_Expenses"].cumsum()

        monthly_discount_rate = discount_rate / 12
        adjusted_retirement_df["Discount_Factor"] = [
            (1 + monthly_discount_rate) ** (-i) for i in range(1, retirement_months + 1)
        ]
        adjusted_retirement_df["PV_Cashflow"] = (
            adjusted_retirement_df["Monthly_Expenses"] * adjusted_retirement_df["Discount_Factor"]
        )

        total_present_value = adjusted_retirement_df["PV_Cashflow"].sum()
        return adjusted_retirement_df, total_present_value, retirement_monthly_expenses, final_salary

    # Run calculations for multiple replacement costs
    results = []
    final_salary_displayed = None
    for replacement_cost in replacement_cost_lst:
        adjusted_retirement_df, total_present_value, retirement_monthly_expenses, final_salary = calculate_retirement_cashflow(
            initial_salary, initial_wealth, contribution_rate, employer_contribution_rate, salary_growth_rate, working_years, 
            replacement_cost, inflation_rate, discount_rate, 
            retire_age, retirement_months
        )

        # Display final salary and ratio only once
        if final_salary_displayed is None:
            st.subheader("Final Salary and Wealth Information")
            st.write(f"Final Salary: {final_salary:,.2f}")
            final_salary_displayed = True


        # Define cashflows
        monthly_savings = [(initial_salary * ((1 + salary_growth_rate) ** (month // 12)) * (contribution_rate + employer_contribution_rate)) 
                           for month in range(working_years * 12)]






        
        savings_df = pd.DataFrame({
            "Month": range(1, working_years * 12 + 1),
            "Monthly_Savings": monthly_savings
        })



        
        cashflows = [-saving for saving in savings_df["Monthly_Savings"]]
        cashflows.append(total_present_value + initial_wealth)  # Add initial wealth to total present value

        # Calculate IRR
        calculated_irr = npf.irr(cashflows)
        annualized_irr = ((1 + calculated_irr) ** 12) - 1

        results.append({
            "Replacement Cost (%)": replacement_cost * 100,
            "Retirement Monthly Expenses": retirement_monthly_expenses,
            "IRR (Monthly)": calculated_irr,
            "IRR (Annualized %)": annualized_irr * 100
        })

    # Display results
    results_df = pd.DataFrame(results) 

    #  savings_df 
    st.write(savings_df )
    
    st.subheader("Results")
    st.write(results_df)

    # Plot the graph
    fig, ax = plt.subplots()
    ax.plot(results_df["Retirement Monthly Expenses"], results_df["IRR (Annualized %)"])
    ax.set_xlabel("Retirement Monthly Expenses")
    ax.set_ylabel("IRR (Annualized %)")
    ax.set_title("Retirement Monthly Expenses vs. IRR")
    st.pyplot(fig)
