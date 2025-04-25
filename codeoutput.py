from pathlib import Path
import pdfplumber
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI

import openai
openai.api_key="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"

# Extract PDF content function
def extract_pdf_content(pdf_path):
    content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                content += text + "\n"
    return content

# Define papers
papers = [
    "Data Structures & Applications (CSE_2152).pdf",
    "Data Structures (ICT 2121).pdf",
]

# Extract content from all papers
paper_to_content_dict = {paper: extract_pdf_content(paper) for paper in papers}

# Code output question generator
def generate_code_output_questions(pdf_content: str, pdf_name: str, num_questions: int = 5, difficulty: str = "medium") -> str:
    prompt = f""" 
    The following are course materials from "{pdf_name}" related to data structures.
    
    Generate **{num_questions} questions** that show code snippets and ask students to determine the output.
    
    Difficulty level: {difficulty}
    
    Each question should:
    - Include a complete, runnable code snippet implementing data structures or algorithms from the course
    - Ask students what the output of the code will be
    - Include code that demonstrates core concepts from the materials
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in generating code tracing and output prediction questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

# Create function tools for code output questions
paper_aliases = {
    "Data Structures & Applications (CSE_2152).pdf": "CSE2152",
    "Data Structures (ICT 2121).pdf": "ICT2121",
}

output_tools = []
for paper in papers:
    pdf_name = Path(paper).stem
    alias = paper_aliases[paper]
    content = paper_to_content_dict[paper]
    
    def output_tool_fn(num_questions: int = 5, difficulty: str = "medium", content=content, pdf_name=pdf_name):
        return generate_code_output_questions(content, pdf_name, num_questions, difficulty)
    
    output_tool = FunctionTool.from_defaults(
        fn=output_tool_fn, 
        name=f"output_{alias}"
    )
    output_tools.append(output_tool)

# Initialize the LLM
llm = OpenAI(model="gpt-4o-mini")

# Initialize the agent
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
agent_worker = FunctionCallingAgentWorker.from_tools(output_tools, llm=llm, verbose=True)
agent = AgentRunner(agent_worker)