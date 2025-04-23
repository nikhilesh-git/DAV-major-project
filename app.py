import gradio as gr
import subprocess
import re
import PyPDF2
from PIL import Image
import shlex
import sys

# Text cleaner functions
def clean_text(text):
    """Cleans extracted text from PDF"""
    if not text:
        return ""
    
    # Remove non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    
    # Remove common PDF artifacts
    text = re.sub(r'-\n', '', text)  # Handle hyphenated line breaks
    text = re.sub(r'\f', '', text)   # Remove form feeds
    text = re.sub(r'Page \d+', '', text)  # Remove page numbers
    
    return text.strip()

# PDF extractor functions
def extract_text_from_pdf(pdf_path):
    """Extracts text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")
    return text

def run_ollama_command(prompt_text):
    """Runs Ollama command with proper encoding handling"""
    try:
        # Properly format the command with prompt
        command = f'ollama run gemma3 "{prompt_text}"'
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',  # Explicitly set encoding
            errors='replace'   # Replace undecodable characters
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except Exception as e:
        return f"Error running model: {str(e)}"

# Global variable to hold extracted/cleaned text
global_cleaned_text = ""

def process_pdf(file):
    global global_cleaned_text
    try:
        raw_text = extract_text_from_pdf(file.name)
        cleaned_text = clean_text(raw_text)
        global_cleaned_text = cleaned_text
        return cleaned_text
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def summarize_text(text):
    prompt_text = (
        "Summarize the following educational text in clear, concise, and structured bullet points or numbered sections. "
        "Note : Just give the summary without any commentary messages."
        f"{text}"
    )
    return run_ollama_command(prompt_text)

def summarize_handler():
    if not global_cleaned_text:
        return "Please upload and extract text first."
    return summarize_text(global_cleaned_text)

def qa_handler(question):
    if not global_cleaned_text:
        return "Please upload and extract text first."
    prompt_text = f"Context: {global_cleaned_text}\n\nQuestion: {question}\nAnswer:"
    return run_ollama_command(prompt_text)


custom_css = """
body {
    background-color: #f7f9fc;
    font-family: 'Segoe UI', sans-serif;
}
.gr-button {
    background-color: #0052cc !important;
    color: white !important;
    border-radius: 5px !important;
    padding: 10px !important;
    border: none !important;
}
.gr-button:hover {
    background-color: #0041a8 !important;
}
.gr-box {
    border: 1px solid #d3d3d3;
    border-radius: 8px;
    padding: 20px;
    background-color: white;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
}
"""


# Create the Gradio interface
with gr.Blocks(css=custom_css) as demo:

    gr.Markdown("<h1 style='text-align: center;'>📄 PDF Summarizer & Q&A Chatbot</h1>")
    gr.Markdown("<p style='text-align: center; font-size: 16px;'>Upload educational PDFs, get detailed summaries, and ask intelligent questions!</p>")

    # Optional logo
    try:
        logo_img = Image.open("8943377.png")
        with gr.Row():
            gr.Image(logo_img, label="Logo", width=120)
    except:
        pass

    with gr.Tabs():
        with gr.TabItem("📂 Upload PDF"):
            with gr.Column(variant="panel"):
                file_input = gr.File(label="Upload a PDF file", file_types=[".pdf"])
                extract_button = gr.Button("📥 Extract Text", elem_classes=["gr-button"])
                extracted_text = gr.Textbox(label="📄 Extracted Text", lines=20, interactive=False, elem_classes=["gr-box"])

        with gr.TabItem("📝 Summarize"):
            with gr.Column(variant="panel"):
                summarize_button = gr.Button("📌 Generate Summary", elem_classes=["gr-button"])
                summary_output = gr.Textbox(label="🧾 Summary", lines=20, interactive=False, elem_classes=["gr-box"])

        with gr.TabItem("❓ Ask a Question"):
            with gr.Column(variant="panel"):
                question_input = gr.Textbox(label="🤔 Your Question", placeholder="Type a question about the PDF here...")
                ask_button = gr.Button("🔍 Get Answer", elem_classes=["gr-button"])
                answer_output = gr.Textbox(label="💬 Answer", lines=6, interactive=False, elem_classes=["gr-box"])

    # Button bindings
    extract_button.click(fn=process_pdf, inputs=file_input, outputs=extracted_text)
    summarize_button.click(fn=summarize_handler, inputs=None, outputs=summary_output)
    ask_button.click(fn=qa_handler, inputs=question_input, outputs=answer_output)


# Launch the app
if __name__ == "__main__":
    demo.launch(share=True)  # Added share=True for public link