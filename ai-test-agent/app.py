# app.py

# =========================================================================
# 1. CORE LIBRARIES & API CONFIGURATION
# Copy these import statements from your original script
# =========================================================================
import requests
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import io
import time
from PIL import Image

# Import Streamlit and Google's Generative AI library
import streamlit as st
import google.generativeai as genai

# Your Gemini API key
import os
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# =========================================================================
# 2. CORE LOGIC FUNCTIONS
# Copy these entire functions from your original script
# =========================================================================
def browse_page(url, driver):
    driver.get(url)
    html = driver.page_source
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

def capture_full_screenshot(driver, image_path):
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    
    images = []
    current_scroll = 0
    while current_scroll < total_height:
        images.append(Image.open(io.BytesIO(driver.get_screenshot_as_png())))
        current_scroll += viewport_height
        driver.execute_script(f"window.scrollTo(0, {current_scroll})")
        time.sleep(1)
    
    stitched_image = Image.new('RGB', (images[0].width, total_height))
    y_offset = 0
    for img in images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.height
    
    stitched_image.save(image_path)
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
        
    2.  **Generate a complete set of automated test cases.** Write these in Selenium Python code. Ensure the code is robust and covers all key functionalities, using reliable element locators.
    
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
# This replaces the entire "if __name__ == '__main__'" block
# =========================================================================
st.title("AI Test Case Generator")

url = st.text_input("Enter the webpage URL:")

if st.button("Generate Test Cases"):
    if not url:
        st.error("Please enter a valid URL.")
    else:
        # Use Streamlit's spinner for a better user experience
        with st.spinner("Extracting components and capturing screenshot..."):
            
            # Initialize Selenium driver with explicit paths
            options = Options()
            options.headless = True
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Tell Selenium where to find the browser and driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            
            image_path = "full_page_screenshot.png"
            output_filename = "test_cases.txt"
            
            try:
                components = browse_page(url, driver)
                image_path = capture_full_screenshot(driver, image_path)

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
                driver.quit()
                if os.path.exists(image_path):
                    os.remove(image_path)
