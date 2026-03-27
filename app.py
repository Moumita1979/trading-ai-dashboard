# Updated app.py to fix the pandas boolean error

# Ensure all rule values are converted to proper Python boolean values
import pandas as pd

# Example data frame

df = pd.DataFrame({
    'rule_name': ["rule1", "rule2", "rule3"],
    'rule_value': ["True", "False", "1"]
})

# Convert rule_value to boolean

df['rule_value'] = df['rule_value'].replace({"True": True, "False": False, "1": True, "0": False})

print(df)
