import streamlit as st
import pandas as pd
import numpy_financial as npf
import matplotlib.pyplot as plt

# Calculate Probability of Breakeven (PoB)
import scipy.stats as stats

# Streamlit app
st.title("Retirement Cashflow Calculator")

# Load the uploaded CSV file to inspect its contents
file_path = 'Asset return.csv'
asset_return_data = pd.read_csv(file_path)
asset_return_data["Port return"] = asset_return_data["Port return"].str.rstrip('%').astype(float) / 100
asset_return_data["Port vol"] = asset_return_data["Port vol"].str.rstrip('%').astype(float) / 100



# Define a function to calculate wealth with returns
def calculate_wealth_with_return(monthly_savings, start_age, initial_wealth, asset_return_data):
    cumulative_wealth = initial_wealth
    wealth_with_return = []

    for month in range(len(monthly_savings)):
        age = start_age + (month // 12)
        # Fetch the return for the current age
        annual_return = asset_return_data.loc[asset_return_data["Age"] == age, "Port return"].values
        monthly_return = annual_return[0] / 12 if len(annual_return) > 0 else 0

        # Update cumulative wealth with monthly savings and return
        cumulative_wealth = cumulative_wealth * (1 + monthly_return) + monthly_savings[month]
        wealth_with_return.append(cumulative_wealth)

    return wealth_with_return




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


    filtered_asset_data = asset_return_data[asset_return_data["Age"] >= start_age]
    # Calculate the average return for filtered data
    average_return_filtered = filtered_asset_data["Port return"].mean()
    st.write(f"Average model Portfolio Return (Start Age {start_age}): {average_return_filtered:.2%}")
    average_vol_filtered = filtered_asset_data["Port vol"].mean()
    st.write(f"Average model Portfolio volatility (Start Age {start_age}): {average_vol_filtered:.2%}")







    

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
    total_present_lst  = []
    dic_adjusted_retirement_df =  {}
    for replacement_cost in replacement_cost_lst:
        adjusted_retirement_df, total_present_value, retirement_monthly_expenses, final_salary = calculate_retirement_cashflow(
            initial_salary, initial_wealth, contribution_rate, employer_contribution_rate, salary_growth_rate, working_years, 
            replacement_cost, inflation_rate, discount_rate, 
            retire_age, retirement_months
        )
        dic_adjusted_retirement_df[replacement_cost] = adjusted_retirement_df

        # Display final salary and ratio only once
        if final_salary_displayed is None:
            st.subheader("Final Salary and Wealth Information")
            st.write(f"Final Salary: {final_salary:,.2f}")
            final_salary_displayed = True


        # Define cashflows
        monthly_savings = [(initial_salary * ((1 + salary_growth_rate) ** (month // 12)) * (contribution_rate + employer_contribution_rate)) 
                           for month in range(working_years * 12)]




        # Add Age and Wealth columns to savings_df
        savings_df = pd.DataFrame({
            "Month": range(1, working_years * 12 + 1),
            "Monthly_Savings": monthly_savings,
            "Age": [start_age + (month // 12) for month in range(working_years * 12)],
        })

   
        # Calculate cumulative wealth
        savings_df["Wealth"] = savings_df["Monthly_Savings"].cumsum() + initial_wealth



        # Add Wealth with Return
        savings_df["Wealth_with_Return"] = calculate_wealth_with_return(
            monthly_savings, start_age, initial_wealth, asset_return_data )




        
        cashflows = [-saving for saving in savings_df["Monthly_Savings"]]
        cashflows.append(total_present_value + initial_wealth)  # Add initial wealth to total present value
        total_present_lst.append(total_present_value)

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
    results_df["เงินที่ต้องมีก่อนเกษียณ"] = total_present_lst
#    st.write(pd.DataFrame( total_present_lst ) )

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

    # Create tabs dynamically based on selected replacement costs
    tabs = st.tabs([f"📈 {int(cost * 100)}% Replacement Cost" for cost in replacement_cost_lst])
    
    # Iterate through tabs and display relevant data
    for i, cost in enumerate(replacement_cost_lst):
        with tabs[i]:
            st.subheader(f"Details for {int(cost * 100)}% Replacement Cost")
            
            # Filter the results for the specific replacement cost
            result = results[i]
            
            st.write(f"Retirement Monthly Expenses: {result['Retirement Monthly Expenses']:,.2f}")
            #st.write(f"IRR (Monthly): {result['IRR (Monthly']:.6f}")
            st.write(f"IRR (Annualized %): {result['IRR (Annualized %)']:.2f}")

            aa = (average_return_filtered *100) -  result['IRR (Annualized %)'] 
            st.write(f"Return - IRR : {aa} %")

            
            # Using the cumulative distribution function (CDF) of the normal distribution
            pob = stats.norm.cdf((average_return_filtered - aa) / average_vol_filtered )
            pob_percentage = pob * 100  # Convert to percentage
            #st.write(f"ความน่าจะเป็นในการบรรลุเป้าหมาย: {pob_percentage  } %")


            
            # If you want to show additional details like savings_df or adjusted_retirement_df
            #st.write("Savings DataFrame:")
            retirement = dic_adjusted_retirement_df[cost]

            merged_df = pd.merge(savings_df, retirement, on='Age', how='outer')
            merged_df = merged_df.fillna(method='ffill')
            merged_df["Cumulative_PV_Cashflow"] =  merged_df["PV_Cashflow"].cumsum()
            merged_df = merged_df.fillna(0)
            merged_df["final Wealth"] =  merged_df["Wealth_with_Return"] -  merged_df["Cumulative_PV_Cashflow"] 
            
            
            st.write(merged_df )


            unique_a = merged_df.drop_duplicates(subset=['Age'], keep='first')
            #st.write(unique_a )
            fig, ax = plt.subplots()
            ax.plot(unique_a ["Age"],unique_a ["final Wealth"])
            ax.set_xlabel("Age")
            ax.set_ylabel("final Wealth")
            ax.set_title("final Wealth")
            st.pyplot(fig)

    
            # Optional: Add any other details or visualizations specific to this replacement cost

