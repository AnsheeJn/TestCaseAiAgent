# Updated agent.py script for Google's Gemini API

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Import the Google Generative AI library
import google.generativeai as genai

# Step 1: Add your Gemini API key here
# For security, you should use environment variables, but for simplicity, you can put it here for now.
genai.configure(api_key="AIzaSyB-IaElsGPXcw4PzMHTs8aSlSKycI6VAds")

# Function to browse and extract components (no change needed here)
def browse_page(url):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
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
            # Note: We are not generating XPaths here, the model will infer them.
        }
        components.append(component_details)
        
    driver.quit()
    return components

# Step 2: Rewrite the test case generation function to use Gemini's API
def generate_test_cases(components, url):
    prompt = f"""
    You are a professional QA engineer. Your task is to analyze a website's components and generate detailed test cases.
    The website URL is: {url}
    
    Here is a list of its key components and their attributes:
    {components}
    
    Based on this information, perform the following tasks:
    
    1.  **Generate 15 manual regression test cases.** Each test case must be well-structured with a clear Title, Preconditions, Steps, and Expected Results.
    
    2.  **Generate 15 automated test cases.** Write these in Selenium Python code. For each test case, include clear comments and use reliable element locators like IDs, class names, or XPath. Ensure the code is ready to be executed.
    
    3.  Format the output clearly with headings for "Manual Test Cases" and "Automated Test Cases".
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or 'gemini-1.5-flash-latest' for a faster, cheaper model
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"An error occurred while generating test cases: {e}"

# Main function
if __name__ == "__main__":
    url = input("Enter the webpage URL: ")
    components = browse_page(url)
    print("Extracted Components:", components)
    
    test_cases = generate_test_cases(components, url)
    
    if test_cases:
        print("\n" + "="*50)
        print("Generated Test Cases:")
        print("="*50)
        print(test_cases)
    else:
        print("Failed to generate test cases.")