import streamlit as st
import requests
from streamlit_monaco import st_monaco # type: ignore
import traceback

def main():
    st.title("Multi-Language Code Editor with Debug Visualizer")
    
    # Dropdown to select the language
    language = st.selectbox("Select Language", ["Python", "Java", "C", "C++", "JavaScript"])
    
    # Default code snippet for selected language
    default_code = {
        "python": """# Try this example:
        numbers = [1, 2, 3, 4, 5]
        squared = [x**2 for x in numbers]
        total = sum(squared)
        result = {'numbers': numbers, 'squared': squared, 'total': total}""",
        "java": "public class TempCode{\n public static void main(String[] args) {\n System.out.println('Hello, World!'); \n}\n}",
        "c": '#include <stdio.h>\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
        "c++": '#include <iostream>\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}',
        "javascript": 'console.log("Hello, World!");'
    }
    
    st.write("### Code Editor")
    user_code = st_monaco(
        language=language.lower().replace("+", "p"),
        theme="vs-dark",
        value=default_code[language.lower()],
        height=500,
    )

    # Add a button to "Run Code" and send the code to the backend
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
                st.text_area("Result", value=result, height=200)
            else:
                st.error("Error: Unable to execute the code.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    if st.button("Submit Code"):
        print()

if __name__ == "__main__":
    main()
