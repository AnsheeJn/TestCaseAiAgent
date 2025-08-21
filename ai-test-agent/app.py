# app.py

import requests
from bs4 import BeautifulSoup
import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# =========================================================================
# 1. CONFIG
# =========================================================================
genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # Add in Streamlit secrets
SCREENSHOT_API_KEY = os.environ.get("SCREENSHOT_API_KEY")  # Optional API key

# =========================================================================
# 2. CORE FUNCTIONS
# =========================================================================
def browse_page(url):
    """Fetch webpage and extract components with BeautifulSoup."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        components = []
        for tag in soup.find_all(['button', 'input', 'a', 'form', 'select', 'textarea']):
            component_details = {
                'tag': tag.name,
                'text': tag.text.strip(),
                'id': tag.get('id'),
                'class': tag.get('class'),
                'attributes': dict(tag.attrs),
            }
            components.append(component_details)
        return components
    except Exception as e:
        st.error(f"Error fetching page: {e}")
        return []


def capture_screenshot(url):
    """Capture screenshot using ScreenshotMachine API (or skip if no API key)."""
    if not SCREENSHOT_API_KEY:
        return None

    endpoint = f"https://api.screenshotmachine.com/?key={SCREENSHOT_API_KEY}&url={url}&dimension=1024xfull"

    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.warning(f"Screenshot capture failed: {e}")
        return None


def generate_test_cases(components, url, img=None):
    """Generate manual + automated regression test cases with Gemini."""
    prompt = f"""
    You are a professional QA engineer. Your task is to analyze a webpage based on extracted HTML components
    and optionally a screenshot, and then generate comprehensive regression test cases.

    IMPORTANT:
    - Do NOT try to access the website live.
    - Use only the provided components and screenshot (if available).
    - Produce well-structured test cases.

    Website URL (reference only): {url}

    Extracted components:
    {components}

    =========================================================================
    OUTPUT REQUIREMENTS
    =========================================================================

    1. **Manual Regression Test Cases**
       - Present as a Markdown table with these columns:
         | Test Case ID | Title | Preconditions | Steps | Expected Result |
       - Use IDs like M1, M2, etc.
       - Ensure steps are written as numbered lists inside the table.

    2. **Automated Regression Test Cases**
       - Write Playwright Python tests.
       - Use reliable locators (id, name, placeholder, etc.) based on given components.
       - Cover main flows: page load, valid/invalid inputs, button clicks, form submissions, links.
       - Provide a full Python test file with multiple `def test_*` functions.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        if img:
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        return f"An error occurred while generating test cases: {e}"

# =========================================================================
# 3. STREAMLIT APP
# =========================================================================
st.title("🧪 AI Test Case Generator")

url = st.text_input("Enter the webpage URL:")

if st.button("Generate Test Cases"):
    if not url:
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Extracting components and capturing screenshot..."):
            components = browse_page(url)
            screenshot_img = capture_screenshot(url)

            if not components:
                st.error("No components extracted from page.")
            else:
                st.info("Generating test cases with Gemini...")

                test_cases = generate_test_cases(components, url, screenshot_img)

                if test_cases:
                    st.success("✅ Test cases generated successfully!")
                    st.markdown("### Generated Test Cases")
                    st.text_area("Test Cases Output", test_cases, height=500)

                    if screenshot_img:
                        st.image(screenshot_img, caption="Captured Screenshot", use_column_width=True)

                    # Save to file
                    output_filename = "test_cases.txt"
                    with open(output_filename, "w", encoding="utf-8") as file:
                        file.write(test_cases)
                    with open(output_filename, "rb") as file:
                        st.download_button(
                            label="📥 Download Test Cases as TXT",
                            data=file,
                            file_name=output_filename,
                            mime="text/plain"
                        )
                else:
                    st.error("Failed to generate test cases.")
