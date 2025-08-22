import os
import io
from PIL import Image
import google.generativeai as genai
import mimetypes
import streamlit as st
import base64

# =========================================================================
# 1. CONFIG
# =========================================================================
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    st.error("Error: GEMINI_API_KEY environment variable not set.")
    st.error("Please set it in your Streamlit Cloud secrets or as an environment variable locally.")
    st.stop() # Stop the app if API key is missing

# Optional API key for external screenshot service (if you decide to use it)
# Note: For security and simplicity, this example relies on user-uploaded images or text descriptions.
# Direct web scraping/screenshot APIs often have rate limits or require billing setup.
SCREENSHOT_API_KEY = os.environ.get("SCREENSHOT_API_KEY") 

# =========================================================================
# 2. CORE FUNCTIONS
# =========================================================================
def browse_page(url):
    """Fetch webpage and extract components with BeautifulSoup (requests-based)."""
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
        st.error(f"Error fetching page: {e}. Ensure the URL is accessible and valid.")
        return []


def capture_screenshot(url):
    """Capture screenshot using ScreenshotMachine API (optional, requires API key)."""
    if not SCREENSHOT_API_KEY:
        st.info("No Screenshot API key provided. Skipping automatic screenshot capture. Please upload an image mockup if available.")
        return None

    endpoint = f"https://api.screenshotmachine.com/?key={SCREENSHOT_API_KEY}&url={url}&dimension=1024xfull"

    try:
        response = requests.get(endpoint)
        response.raise_for_status() # Raise an exception for HTTP errors
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.warning(f"Screenshot capture failed (ScreenshotMachine API error): {e}. Proceeding without screenshot.")
        return None


def generate_test_cases(components, url, img=None, manual_format="Text", auto_language="Python", auto_framework="Playwright"):
    """
    Generate manual + automated regression test cases with Gemini, customized by user preferences.
    """
    
    # Constructing the prompt based on user selections
    prompt_manual_format_details = {
        "Jira": "Format manual test cases suitable for Jira, including Summary, Preconditions, Steps (with Expected Result), and a separate Expected Result field for the entire test case.",
        "Azure": "Format manual test cases suitable for Azure DevOps Test Plans, with clear Test Case Title, Steps (with Action and Expected Result columns), and Tags.",
        "Qtest": "Format manual test cases for QTest Manager, providing Test Case Name, Pre-conditions, Test Steps (with Description, Expected Result, and Test Data columns).",
        "Excel": "Format manual test cases in a clear, tabular layout suitable for an Excel spreadsheet, using columns like Test ID, Test Case Name, Preconditions, Step #, Action, Expected Result, Test Data.",
        "Text": "Format manual test cases as plain text, with clear headings: Test Case Title, Preconditions, Steps, and Expected Result."
    }

    prompt_auto_language_framework_details = {
        "Python": {
            "Selenium": "Selenium Python code. Ensure robust element locators and standard Selenium assertions.",
            "Playwright": "Playwright Python code. Ensure robust element locators and Playwright assertions (e.g., `expect(locator).to_have_text()`).",
            "Cucumber": "Behavior-driven development (BDD) features using Gherkin syntax (Feature, Scenario, Given, When, Then). Do NOT generate Python step definitions, only the Gherkin feature file content."
        },
        "Java": {
            "Selenium": "Selenium Java code (using JUnit/TestNG). Ensure robust element locators and standard Selenium assertions.",
            "Playwright": "Playwright Java code. Ensure robust element locators and Playwright assertions.",
            "Cucumber": "Behavior-driven development (BDD) features using Gherkin syntax (Feature, Scenario, Given, When, Then). Do NOT generate Java step definitions, only the Gherkin feature file content."
        },
        "JavaScript": {
            "Selenium": "Selenium JavaScript code (using Mocha/Jest). Ensure robust element locators and standard Selenium assertions.",
            "Playwright": "Playwright JavaScript code. Ensure robust element locators and Playwright assertions.",
            "Cucumber": "Behavior-driven development (BDD) features using Gherkin syntax (Feature, Scenario, Given, When, Then). Do NOT generate JavaScript step definitions, only the Gherkin feature file content."
        },
        "TypeScript": {
            "Selenium": "Selenium TypeScript code (using Mocha/Jest/Playwright Test). Ensure robust element locators and standard Selenium assertions.",
            "Playwright": "Playwright TypeScript code. Ensure robust element locators and Playwright assertions.",
            "Cucumber": "Behavior-driven development (BDD) features using Gherkin syntax (Feature, Scenario, Given, When, Then). Do NOT generate TypeScript step definitions, only the Gherkin feature file content."
        }
    }

    # Base prompt
    prompt = f"""
    You are a professional QA engineer. Your task is to analyze a website and a screenshot (if provided) to generate comprehensive regression test cases.
    The website URL is: {url}
    
    Here is a list of its key components and their attributes:
    {components}
    
    Based on the provided HTML components and the visual information from the screenshot, perform the following tasks:
    
    1.  **Generate a complete set of manual regression test cases.** {prompt_manual_format_details[manual_format]}
        
        **CRITICAL INSTRUCTION FOR OUTPUT FORMAT (MANUAL):**
        - Do not use any HTML tags like <br> or <div>.
        - Use plain text only.
        - Each manual test case must follow the specific structure for the selected format: {manual_format}.
        
    2.  **Generate a complete set of automated test cases.** Write these in {prompt_auto_language_framework_details[auto_language][auto_framework]}
        
        **CRITICAL INSTRUCTION FOR OUTPUT FORMAT (AUTOMATED):**
        - The automated test cases should be valid code for the selected language and framework, within a single markdown code block (\`\`\`{auto_language.lower()} ... \`\`\`).
        - Use clear and descriptive variable names.
        - Include comments for complex logic.
        - Focus on test logic, not full setup/project structure.
        - For Cucumber, provide only the Gherkin feature file content.
        
    3.  Format the output clearly with markdown headings for "Manual Regression Test Cases" and "Automated Regression Test Cases".
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        content_parts = [{"text": prompt}]
        if img:
            # Prepare image for Gemini API, ensuring correct mime_type and data format
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=img.format if img.format else 'PNG') # Save to BytesIO object
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            content_parts.append({
                "inline_data": {
                    "mime_type": f"image/{img.format.lower()}" if img.format else "image/png",
                    "data": img_base64
                }
            })
        
        response = model.generate_content(content_parts)
        return response.text
    except Exception as e:
        return f"An error occurred while generating test cases: {e}"

# =========================================================================
# 3. STREAMLIT APP
# =========================================================================
st.set_page_config(page_title="AI Test Case Generator", layout="wide")

st.title("🧪 AI Test Case Generator")

st.markdown(
    """
    Generate comprehensive manual and automated test cases by providing a webpage URL. 
    Customize the output format for your specific needs.
    """
)

url = st.text_input("1. Enter the webpage URL:", placeholder="e.g., https://www.example.com")

st.markdown("---")
st.subheader("2. Customize Test Case Output")

col1, col2 = st.columns(2)

with col1:
    manual_format_option = st.selectbox(
        "Manual Test Case Format:",
        options=["Text", "Jira", "Azure", "Qtest", "Excel"],
        help="Select the desired format for your manual test cases."
    )

with col2:
    auto_language_option = st.selectbox(
        "Automated Test Case Language:",
        options=["Python", "Java", "JavaScript", "TypeScript"],
        help="Select the programming language for your automated test cases."
    )

auto_framework_option = st.selectbox(
    "Automated Test Case Framework:",
    options=["Playwright", "Selenium", "Cucumber"],
    help="Select the automation framework for your automated test cases. For Cucumber, only Gherkin features will be generated."
)

if st.button("Generate Test Cases", help="Click to analyze the URL and generate test cases based on your selections."):
    if not url:
        st.error("Please enter a valid webpage URL to generate test cases.")
    else:
        with st.spinner("Analyzing webpage, capturing screenshot, and generating test cases... This may take a moment."):
            components = browse_page(url)
            screenshot_img = capture_screenshot(url) # This will print info/warning about API key

            if not components:
                st.error("Could not extract any meaningful components from the provided URL. Please check the URL or try a different one.")
            else:
                st.info("Generating test cases with Gemini AI...")

                test_cases = generate_test_cases(
                    components=components,
                    url=url,
                    img=screenshot_img,
                    manual_format=manual_format_option,
                    auto_language=auto_language_option,
                    auto_framework=auto_framework_option
                )

                if test_cases:
                    st.success("✅ Test cases generated successfully!")
                    st.markdown("---")
                    st.markdown("### Generated Test Cases")
                    st.markdown(test_cases) # Display as markdown to render headings and code blocks

                    if screenshot_img:
                        st.markdown("---")
                        st.subheader("Captured Webpage Screenshot")
                        st.image(screenshot_img, caption=f"Screenshot of {url}", use_column_width=True)

                    # Add download button for the generated text
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Test Cases as Markdown",
                        data=test_cases.encode("utf-8"),
                        file_name="generated_test_cases.md",
                        mime="text/markdown",
                        help="Click to download the generated test cases as a Markdown file."
                    )
                else:
                    st.error("Failed to generate test cases. Please try again or refine your input.")

st.markdown("---")
st.caption("Powered by Google Gemini AI")
