import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key="YOUR_API_KEY")

st.title("AI Test Case Generator")
st.write("Generate Manual + Automated Regression Test Cases for any website/app feature")

# User input
feature_description = st.text_area("Enter website URL or feature description:")

if st.button("Generate Test Cases"):
    with st.spinner("Generating..."):
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

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or gpt-4o, gpt-5 if available
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        output = response.choices[0].message.content
        st.markdown(output, unsafe_allow_html=True)
