import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# -------------------------
# Configure Gemini API
# -------------------------
genai.configure(api_key="YOUR_GEMINI_API_KEY")

st.set_page_config(page_title="AI Test Case Generator", layout="wide")
st.title("🧪 AI Test Case Generator")
st.write("Generate Manual + Automated Regression Test Cases for any website or feature using **Gemini**.")

# -------------------------
# User Input
# -------------------------
feature_description = st.text_area("Enter website URL or feature description:")

# -------------------------
# Generate Button
# -------------------------
if st.button("Generate Test Cases"):
    if not feature_description.strip():
        st.error("⚠️ Please enter a feature description or URL first.")
    else:
        with st.spinner("⚡ Generating test cases..."):
            # Prompt for Gemini
            prompt = f"""
You are a QA Test Specialist. 
Generate **manual regression test cases** for the following feature/website:

{feature_description}

The output must follow this exact format so it can be copy-pasted into Test Management tools (like Testmo, qTest, Zephyr):  

# 1. Manual Regression Test Cases

| Test Case ID | Title | Preconditions | Steps | Expected Result |
|--------------|-------|---------------|-------|-----------------|
| M1 | <Title> | <Preconditions> | 1. Step one <br> 2. Step two <br> ... | <Expected outcome> |

# 2. Automated Regression Test Cases (Playwright Python)

Provide **Playwright Python test scripts** for the above manual test cases.  
Each script should be independent, use `pytest`, and include meaningful assertions.  

Make sure the response is:
- Well-structured
- Readable
- Easy to copy and paste into tools
- Uses `<br>` for line breaks inside table cells
"""

            # Call Gemini
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

            # Get text output
            output_text = response.text

            # -------------------------
            # Display raw Markdown output
            # -------------------------
            st.markdown("### 📋 Generated Test Cases")
            st.markdown(output_text, unsafe_allow_html=True)

            # -------------------------
            # Try extracting the manual test case table
            # -------------------------
            st.markdown("---")
            st.subheader("⬇️ Download Manual Test Cases as CSV")

            # Extract Markdown table (Manual Regression Test Cases)
            table_match = re.search(r"\| Test Case ID.*?\n((?:\|.*?\n)+)", output_text, re.DOTALL)
            if table_match:
                table_md = "| Test Case ID | Title | Preconditions | Steps | Expected Result |\n" + table_match.group(1)

                # Convert Markdown table to DataFrame
                df = pd.read_csv(pd.compat.StringIO(table_md), sep="|", engine="python").dropna(axis=1, how="all")
                df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

                # Download button
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name="manual_test_cases.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Could not parse the manual test cases table automatically. Please copy from the output above.")
