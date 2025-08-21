# app.py

# =========================================================================
# 1. CORE LIBRARIES & API CONFIGURATION
# =========================================================================
import requests
from bs4 import BeautifulSoup
import os
import io
import time
from PIL import Image
import streamlit as st
import google.generativeai as genai
import subprocess
from playwright.sync_api import sync_playwright

# Your Gemini API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Use a one-time command to install the browsers for Playwright
# This is a robust way to ensure the browser is available
try:
    # Check if the browser is already installed
    subprocess.run(["playwright", "install", "--with-deps", "chromium"], check=True)
except subprocess.CalledProcessError as e:
    st.error(f"Failed to install Playwright browsers: {e}")

# =========================================================================
# 2. CORE LOGIC FUNCTIONS
# =========================================================================
def browse_page(url, page):
    page.goto(url)
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
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

def capture_full_screenshot(page, image_path):
    page.screenshot(path=image_path, full_page=True)
    return image_path

# Function to generate test cases with both text and image input
def generate_test_cases(components, url, image_path):
    prompt = f"""
    You are a professional QA engineer. Your task is to analyze a website and a screenshot to generate all possible regression test cases.
    The website URL is: {url}
    
    Here is a list of its key components and their attributes:
    {components}
    
    Based on the provided HTML components and the visual information from the screenshot, perform the following tasks:
    
    1.  **Generate a complete set of manual regression test cases.** These test cases must be exhaustive, covering all functional, visual, and performance aspects of the page.
        
        **CRITICAL INSTRUCTION FOR OUTPUT FORMAT:**
        - Do not use any HTML tags like <br> or <div>.
        - Use plain text only.
        - Each test case must start with a new line and follow this structure precisely:
        
        **Test Case Title:** <A clear and concise title>
        **Preconditions:** <Any conditions needed to start the test>
        **Steps:**
        1. <First step>
        2. <Second step>
        ...
        **Expected Result:** <The expected outcome>
        
    2.  **Generate a complete set of automated test cases.** Write these in Playwright Python code. Ensure the code is robust and covers all key functionalities, using reliable element locators.
    
    3.  Format the output clearly with headings for "Manual Regression Test Cases" and "Automated Regression Test Cases".
    """
    
    try:
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"An error occurred while generating test cases: {e}"

# =========================================================================
# 3. STREAMLIT APP LOGIC
# =========================================================================
st.title("AI Test Case Generator")

url = st.text_input("Enter the webpage URL:")

if st.button("Generate Test Cases"):
    if not url:
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Extracting components and capturing screenshot..."):
            
            # This is the new Playwright block
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                image_path = "full_page_screenshot.png"
                output_filename = "test_cases.txt"

                try:
                    components = browse_page(url, page)
                    image_path = capture_full_screenshot(page, image_path)

                    st.info(f"Extracted components and captured screenshot. Generating test cases...")
                    
                    test_cases = generate_test_cases(components, url, image_path)
                    
                    if test_cases:
                        st.success("Test cases generated successfully! 🎉")
                        st.markdown("### Generated Test Cases")
                        st.text_area("Test Cases", test_cases, height=500)
                        
                        # Write the output to a text file
                        with open(output_filename, "w", encoding="utf-8") as file:
                            file.write(test_cases)
                        
                        # Add a download button
                        with open(output_filename, "rb") as file:
                            st.download_button(
                                label="Download Test Cases as TXT",
                                data=file,
                                file_name=output_filename,
                                mime="text/plain"
                            )
                    else:
                        st.error("Failed to generate test cases.")
                        
                except Exception as e:
                    st.error(f"An error occurred during generation: {e}")
                    
                finally:
                    browser.close()
                    if os.path.exists(image_path):
                        os.remove(image_path)
