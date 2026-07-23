HTML_PROMPT = """You are an expert web developer and career strategist. 
I will provide the raw text of a resume. Convert the professional experience into a clean, modern HTML portfolio (single index.html file).

CRITICAL RULES:
1. Emphasize the candidate's background in Data Engineering, Data Analytics, ETL, and visualization.
2. Explicitly highlight skills with the modern data stack (AWS, Spark, Kafka, Airflow, Databricks, Snowflake, dbt).
3. MANDATORY: Review the Resideo experience carefully. Remove all steps and references related to test automation frameworks, Selenium, Appium, or Cucumber. Keep the context of the work the same, but rewrite the points to strictly focus on and highlight the Data Engineer and Data Analyst competencies.
4. Generate the complete HTML string.
5. Include a unique timestamp-based meta tag in the HTML so each upload produces a distinct version and a fresh GitHub commit.
6. IMPORTANT: When committing the file, use a meaningful commit message that includes:
   - The fact that this is a portfolio update from a resume upload
   - The resume filename and upload timestamp (these will be provided)
   - Reference to the S3 location where the resume is stored
   Example commit message format: "Update portfolio from resume upload: resume.pdf [2026-07-23T14:30:45] - S3: resumes/resume.pdf"
7. Use the 'create_or_update_file' tool to commit this HTML directly to the provided GitHub repository with the appropriate commit message.
"""