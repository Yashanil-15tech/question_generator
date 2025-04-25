from pdfscanner import extract_pdf_content, scan_for_pdfs
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
import openai
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
from pathlib import Path

openai.api_key = "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"

papers= scan_for_pdfs()

paper_to_content_dict = {alias: extract_pdf_content(pdf) for alias, pdf in papers.items()}
  

def generate_coding_questions(pdf_content: str, pdf_name: str, num_questions: int, difficulty: str) -> str:
    prompt = f""" 
        The following are course materials from "{pdf_name}" related to data structures.
        
        Generate **{num_questions} coding implementation questions** some already generated before and some new of the same topics as in {pdf_content} related to the content below.
        Questions should require students to write complete functions or classes in a programming language.
        
        For EACH question:
                1. Start with "Question X: [Title]" on its own line
                2. Include a clear description of the problem
                3. Add "Specifications:" section with bullet points
                4. Add "Constraints:" section if needed
        Make sure each question is clearly separated from others.
        there's a clear delineation like "1.", "2.", etc.
        🚫 **DO NOT** generate questions unrelated to the extracted content.
        🚫 **DO NOT** include the solutions to the questions.
        🚫 **DO NOT** generate questions from any other topic other than the ones in the {pdf_content}
        
        Content: {pdf_content}
        """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in generating programming and data structures questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content


coding_tools = []
for alias, pdf_path in papers.items():
    pdf_name = Path(pdf_path).stem
    content = paper_to_content_dict[alias]

    def coding_tool_fn(num_questions: int = 5, difficulty: str = "medium", content=content, pdf_name=pdf_name):
        return generate_coding_questions(content, pdf_name, num_questions, difficulty)

    coding_tool = FunctionTool.from_defaults(
        fn=coding_tool_fn, 
        name=f"coding_{alias}",
        description=f"Generates coding questions for {alias}."
    )
    coding_tools.append(coding_tool)


llm = OpenAI(model="gpt-4o-mini")


agent_worker = FunctionCallingAgentWorker.from_tools(coding_tools, llm=llm, verbose=True)
agent = AgentRunner(agent_worker)


def get_questions_from_agent(paper: str, num_questions: int, difficulty: str) -> str:
    response=agent.query(f"Generate {num_questions} {difficulty}-level coding questions for {paper}.")
    return response.response if hasattr(response, "response") else str(response)
##response=agent.query("Generate 3 questions combined from all CSE papers")