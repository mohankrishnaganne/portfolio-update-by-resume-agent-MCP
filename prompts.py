HTML_PROMPT = """You are an expert web developer and career strategist.
I will provide the raw text of a resume. Convert the professional experience into a clean, modern HTML portfolio (single index.html file).

CRITICAL RULES:
1. Emphasize the candidate's background in Data Engineering, Data Analytics, ETL, and visualization.
2. Explicitly highlight skills with the modern data stack (AWS, Spark, Kafka, Airflow, Databricks, Snowflake, dbt).
3. MANDATORY: Review the Resideo experience carefully. Remove all steps and references related to test automation frameworks, Selenium, Appium, or Cucumber. Keep the context of the work the same, but rewrite the points to strictly focus on and highlight the Data Engineer and Data Analyst competencies.
4. Generate the complete HTML string only. Do not include markdown, tool call syntax, or any explanatory text outside the HTML.
5. Include a unique timestamp-based meta tag in the HTML so each upload produces a distinct version and a fresh GitHub commit.
6. Use the provided resume text to generate the portfolio content as a fresh update every time.
"""