# app.py

import requests
from bs4 import BeautifulSoup
import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# =========================================================================
# FUNCTIONS
# =========================================================================
def browse_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        components = []
        for tag in soup.find_all(['button', 'input', 'a', 'form']):
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
    # Replace with your ScreenshotMachine API key
    API_KEY = os.environ.get("SCREENSHOT_API_KEY")
    endpoint = f"https://api.screenshotmachine.com/?key={API_KEY}&url={url}&dimension=1024xfull"
    
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.warning(f"Screenshot capture failed: {e}")
        return None

def generate_test_cases(components, url, img=None):
    prompt = f"""
    You are a professional QA engineer. Your task is to analyze a website and generate regression test cases.
    The website URL is: {url}

    Here is a list of its key components and their attributes:
    {components}

    Tasks:
    1. Generate manual regression test cases.
    2. Generate automated regression test cases in Playwright Python.

    Format:
    - Manual Regression Test Cases
    - Automated Regression Test Cases
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        if img:
            response = model.generate_content([prompt, img])
        else:
            response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        return f"An error occurred while generating test cases: {e}"

# =========================================================================
# STREAMLIT UI
# =========================================================================
st.title("AI Test Case Generator with Screenshot")

url = st.text_input("Enter the webpage URL:")

if st.button("Generate Test Cases"):
    if not url:
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Extracting components and capturing screenshot..."):
            components = browse_page(url)
            screenshot_img = capture_screenshot(url)

            if not components:
                st.error("No components extracted.")
            else:
                st.info("Generating test cases...")
                test_cases = generate_test_cases(components, url, screenshot_img)

                if test_cases:
                    st.success("Test cases generated successfully! 🎉")
                    st.text_area("Test Cases", test_cases, height=500)

                    if screenshot_img:
                        st.image(screenshot_img, caption="Captured Screenshot", use_column_width=True)

                    # Save results
                    output_filename = "test_cases.txt"
                    with open(output_filename, "w", encoding="utf-8") as file:
                        file.write(test_cases)
                    with open(output_filename, "rb") as file:
                        st.download_button(
                            label="Download Test Cases as TXT",
                            data=file,
                            file_name=output_filename,
                            mime="text/plain"
                        )
                else:
                    st.error("Failed to generate test cases.")
