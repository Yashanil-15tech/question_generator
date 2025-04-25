import streamlit as st
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
from coding import coding_tools
from theory import theory_tools
from evaluate import output_tool
from llama_index.llms.openai import OpenAI
from streamlit_monaco import st_monaco # type: ignore
import requests
import re

# Initialize session state
if 'all_questions' not in st.session_state:
    st.session_state.all_questions = []
if 'question_types' not in st.session_state:
    st.session_state.question_types = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'questions_generated' not in st.session_state:
    st.session_state.questions_generated = False

# Combine all tools
all_tools = coding_tools + theory_tools + output_tool

# Initialize the Orchestrator Agent
llm = OpenAI(model="gpt-4o-mini")
orchestrator_worker = FunctionCallingAgentWorker.from_tools(all_tools, llm=llm, verbose=True)
orchestrator_agent = AgentRunner(orchestrator_worker)

# Default code snippet for different languages
default_code = {
    "python": """# Write your solution here
def solution():
    # Your code
    pass
""",
    "java": "public class Solution {\n    public static void main(String[] args) {\n        // Your code here\n    }\n}",
    "c": '#include <stdio.h>\nint main() {\n    // Your code here\n    return 0;\n}',
    "c++": '#include <iostream>\nint main() {\n    // Your code here\n    return 0;\n}',
    "javascript": '// Write your solution here\nfunction solution() {\n    // Your code\n}'
}

# Function to extract questions from text
def extract_questions(text, num_expected):
    questions = []
    question_pattern = r'(?:Question\s+\d+\s*:.*?)(?=Question\s+\d+\s*:|$)'
    matches = re.finditer(question_pattern, text, re.DOTALL)
    
    for match in matches:
        questions.append(match.group(0).strip())
    
    # If we didn't get enough questions or regex failed, split manually
    if len(questions) < num_expected:
        # Try another approach - split by "Question X:"
        parts = re.split(r'Question\s+\d+\s*:', text)
        if len(parts) > 1:
            questions = []
            for i in range(1, len(parts)):
                questions.append(f"Question {i}: {parts[i].strip()}")
    
    return questions

# Streamlit UI
st.title("🤖 AI-Powered Question Generator")

# Only show course selection if questions haven't been generated yet
if not st.session_state.questions_generated:
    # Select Paper
    selected_paper = st.selectbox(
        "Select Course Material",
        ["CSE", "ICT"],
        format_func=lambda x: "CSE" if x == "CSE" else "ICT"
    )

    # Generate button
    if st.button("Generate Questions"):
        with st.spinner("Generating questions using AI agent... 🤖"):
            # Generate 5 coding questions
            coding_prompt = f"Generate 8 coding questions combined from only the papers of {selected_paper}. Format each question as 'Question X: [Title]' followed by the description, specifications as bullet points, and constraints."
            
            coding_response = orchestrator_agent.query(coding_prompt)
            coding_text = coding_response.response if hasattr(coding_response, "response") else str(coding_response)
            
            # Extract coding questions
            coding_questions = extract_questions(coding_text, 5)
            '''
            # Generate 3 theory questions
            theory_prompt = f"Generate 3 medium-level theory questions for {selected_paper}. Format each question as 'Question X: [Title]' followed by the description."
            
            theory_response = orchestrator_agent.query(theory_prompt)
            theory_text = theory_response.response if hasattr(theory_response, "response") else str(theory_response)
            
            # Extract theory questions
            theory_questions = extract_questions(theory_text, 3)'
            '''
            
            # Combine questions and mark their types
            all_questions = []
            question_types = []
            
            for question in coding_questions:
                all_questions.append(question)
                question_types.append("coding")
                
            #for question in theory_questions:
                #all_questions.append(question)
                #question_types.append("theory")
            
            # Store in session state
            st.session_state.all_questions = all_questions
            st.session_state.question_types = question_types
            st.session_state.current_question_index = 0
            st.session_state.questions_generated = True
            
            st.success(f"✅ Generated 8 Questions (5 Coding, 3 Theory)!")
            st.rerun()

# Display current question and navigation buttons
if st.session_state.questions_generated:
    current_index = st.session_state.current_question_index
    
    # Get current question and its type
    questions = st.session_state.all_questions
    question_types = st.session_state.question_types
    
    if questions:
        current_type = question_types[current_index]
        total_questions = len(questions)
        
        # Display question number and content
        st.subheader(f"Question {current_index + 1} of {total_questions}")
        st.markdown(questions[current_index])
        
        # Display appropriate input method based on question type
        if current_type == "coding":
            st.write("### Code Editor")
            language = st.selectbox("Select Language", ["Python", "Java", "C", "C++", "JavaScript"])
            
            user_code = st_monaco(
                language=language.lower().replace("+", "p"),
                theme="vs-dark",
                value=default_code[language.lower()],
                height=300,
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Run Code"):
                    url = "http://127.0.0.1:5000/run_code"
                    data = {
                        "language": language.lower().replace("+", "p"),
                        "code": user_code
                    }
                    
                    try:
                        response = requests.post(url, json=data)
                        if response.status_code == 200:
                            result = response.json().get('output', 'No output returned.')
                            st.write("### Output")
                            st.text_area("Result", value=result, height=150, key="code_output")
                        else:
                            st.error("Error: Unable to execute the code.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            with col2:
                if st.button("Submit Solution"):
                    evaluate_prompt = f"Evaluate this code solution for the given question: {questions[current_index]}\n\nCode:\n{user_code}"
    
                    evaluation_response = orchestrator_agent.query(evaluate_prompt)
                    evaluation_text = evaluation_response.response if hasattr(evaluation_response, "response") else str(evaluation_response)
    
                    st.write("### Evaluation")
                    st.markdown(evaluation_text)            
        else:  # Theory question
            st.write("### Your Answer")
            user_answer = st.text_area("Type your answer here", height=300, key="theory_answer")
            
            if st.button("Submit Answer"):
                st.success("Answer submitted!")
        
        # Navigation buttons in columns
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Previous button
            if current_index > 0:
                if st.button("Previous"):
                    st.session_state.current_question_index -= 1
                    st.rerun()
        
        with col2:
            # Question type indicator
            question_type_display = "Coding" if current_type == "coding" else "Theory"
            st.info(f"Current: {question_type_display} Question")
        
        with col3:
            # Next button
            if current_index < len(questions) - 1:
                if st.button("Next"):
                    st.session_state.current_question_index += 1
                    st.rerun()
        
        # Reset button
        if st.button("Generate New Questions"):
            st.session_state.questions_generated = False
            st.session_state.all_questions = []
            st.session_state.question_types = []
            st.rerun()
    else:
        st.error("No questions were generated. Please try again.")
        if st.button("Back"):
            st.session_state.questions_generated = False
            st.rerun()