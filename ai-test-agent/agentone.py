import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import io
import time
from PIL import Image

import google.generativeai as genai

# Step 1: Add your Gemini API key here
genai.configure(api_key="AIzaSyB-IaElsGPXcw4PzMHTs8aSlSKycI6VAds")

# Function to browse and extract components
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

# Function to take a full-page screenshot
def capture_full_screenshot(driver, image_path):
    # Get the total height of the webpage
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    
    images = []
    current_scroll = 0
    while current_scroll < total_height:
        images.append(Image.open(io.BytesIO(driver.get_screenshot_as_png())))
        
        current_scroll += viewport_height
        driver.execute_script(f"window.scrollTo(0, {current_scroll})")
        time.sleep(1) # Pause to let content load
    
    # Stitch the images together
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
    
    1.  **Generate a complete set of manual regression test cases.** These test cases must be exhaustive, covering all functional, visual, and performance aspects of the page. Each test case must be well-structured with a clear Title, Preconditions, Steps, and Expected Results.
    
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

# Main function
if __name__ == "__main__":
    url = input("Enter the webpage URL: ")
    
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    
    # Define the output file name
    output_filename = "test_cases.txt"
    
    try:
        print("Extracting components and capturing screenshot...")
        components = browse_page(url, driver)
        image_path = capture_full_screenshot(driver, "full_page_screenshot.png")
        print("Extracted Components:", components)
        print(f"Full page screenshot saved to: {image_path}")
        
        print("Generating test cases with visual context...")
        test_cases = generate_test_cases(components, url, image_path)
        
        if test_cases:
            print("\n" + "="*50)
            print("Generated Test Cases:")
            print("="*50)
            print(test_cases)
            
            # Write the output to a text file
            with open(output_filename, "w", encoding="utf-8") as file:
                file.write(test_cases)
            
            print(f"\n✅ Test cases have been successfully saved to {output_filename}")
        else:
            print("Failed to generate test cases.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        driver.quit()
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Cleaned up {image_path}")