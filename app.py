import os
import google.generativeai as genai
import fitz  # PyMuPDF
import streamlit as st
import json
import re
import traceback

# Set page configuration (title and favicon)
st.set_page_config(page_title="Interview Prep AI", page_icon="🤖", layout="wide")

# Configure the Google Generative AI API
genai.configure(api_key='AIzaSyAfBnFjJ-80s7iy71wLVGNh2q3NccSjVo0')  # Replace with your actual API key

# Set generation configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}
def extract_text_from_pdf(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

def clear_uploads_directory(upload_dir="uploads/"):
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)  # Remove file
        except Exception as e:
            st.error(f"Error removing {file_path}: {str(e)}")
            
# Initialize the generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Function to generate interview questions (previous implementation)
def generate_interview_questions(job_role, job_experience, job_description):
    prompt = f"""Generate 5 tailored interview questions for a {job_role} with {job_experience} years of experience.
    
Job Description and Tech Stack: {job_description}

Format your response EXACTLY like this:
1. [Specific Question about {job_role}] - Difficulty: [easy/medium/hard], Focus: [technical/behavioral/scenario-based]
2. [Another Specific Question] - Difficulty: [easy/medium/hard], Focus: [technical/behavioral/scenario-based]
3. [Third Specific Question] - Difficulty: [easy/medium/hard], Focus: [technical/behavioral/scenario-based]
4. [Fourth Specific Question] - Difficulty: [easy/medium/hard], Focus: [technical/behavioral/scenario-based]
5. [Fifth Specific Question] - Difficulty: [easy/medium/hard], Focus: [technical/behavioral/scenario-based]

Ensure questions are precise, relevant to the job role, and demonstrate deep understanding of the role's requirements."""

    try:
        # Generate the response
        response = model.generate_content(prompt)
        
        # Parse the text response manually
        questions = []
        for line in response.text.split('\n'):
            line = line.strip()
            if line:
                # More flexible regex to capture the full question
                match = re.match(r'(\d+\.\s*)(.*?)\s*-\s*Difficulty:\s*(\w+),\s*Focus:\s*(\w+)', line)
                if match:
                    full_question = match.group(2).strip()
                    difficulty = match.group(3)
                    focus = match.group(4)
                    questions.append({
                        "question": full_question,
                        "difficulty": difficulty,
                        "focus": focus
                    })
        
        return questions
    except Exception as e:
        # Comprehensive error logging
        st.error("Error generating questions:")
        st.error(str(e))
        st.error(traceback.format_exc())
        return []

# Function to evaluate interview answers
def evaluate_interview_answers(job_role, questions, answers):
    # Construct a detailed prompt for evaluation
    evaluation_prompt = f"""You are an experienced interviewer evaluating interview answers for a {job_role} position.

Please evaluate the following interview answers with a comprehensive and constructive approach:

{json.dumps(list(zip(questions, answers)), indent=2)}

Provide a detailed evaluation in this JSON format:
{{
    "overall_rating": x,  // Rating out of 10
    "overall_feedback": "Comprehensive summary of performance",
    "detailed_feedback": [
        {{
            "question": "Original interview question",
            "answer_rating": x,  // Rating out of 10
            "strengths": "Positive aspects of the answer",
            "areas_for_improvement": "Specific suggestions for improvement",
            "suggested_answer_framework": "How an ideal answer might be structured"
        }},
        // ... feedback for other questions
    ]
}}"""

    try:
        # Generate evaluation
        response = model.generate_content(evaluation_prompt)
        
        # Try to parse the JSON response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group(0))
            return evaluation
        else:
            # Fallback if JSON parsing fails
            return {
                "overall_rating": 5,
                "overall_feedback": "Unable to generate detailed evaluation.",
                "detailed_feedback": []
            }
    
    except Exception as e:
        st.error(f"Error evaluating answers: {str(e)}")
        return None

# Main Streamlit App
def main():
    # Clear the uploads directory when the app is refreshed
    clear_uploads_directory()

    st.title("🚀 Interview Prep AI")
    st.markdown("Your AI companion for interview preparation")

    # Sidebar for Resume Upload
    st.sidebar.header("📄 Upload Resume")
    resume_file = st.sidebar.file_uploader("Upload your resume (PDF)", type=["pdf"])
    
    # Initialize resume_text in session state if not present
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    
    if resume_file:
        try:
            # Save the uploaded resume
            resume_path = os.path.join("uploads", resume_file.name)
            with open(resume_path, "wb") as f:
                f.write(resume_file.getbuffer())

            # Extract text from the resume
            st.session_state.resume_text = extract_text_from_pdf(resume_path)
            st.sidebar.success("✅ Resume uploaded successfully!")
            
            # Show a preview of the extracted text
            with st.sidebar.expander("Resume Content Preview"):
                st.write(st.session_state.resume_text[:500] + "...")
                
        except Exception as e:
            st.sidebar.error(f"Error processing resume: {str(e)}")

    # Main content area
    tab1, tab2 = st.tabs(["Interview Prep", "Normal Chat"])

    with tab1:
        st.header("Interview Preparation")
        
        # Input fields in a single column
        job_role = st.text_input("Job Role", placeholder="e.g., Data Scientist")
        job_experience = st.number_input("Years of Experience", min_value=0, max_value=30, step=1)
        job_description = st.text_area("Job Description/Tech Stack", placeholder="List technologies, frameworks, etc.")

        # Generate Interview Questions
        if st.button("Generate Interview Questions"):
            # Validate inputs
            if not job_role:
                st.warning("Please enter a job role")
                return
            if not job_description:
                st.warning("Please enter job description or tech stack")
                return
            
            # Include resume context if available
            context = ""
            if st.session_state.resume_text:
                context = f"\nCandidate's Resume Context: {st.session_state.resume_text}"
            
            # Generate questions with resume context if available
            st.session_state.job_role = job_role
            st.session_state.interview_questions = generate_interview_questions(
                job_role, 
                job_experience, 
                job_description + context
            )
            
            # Ensure questions were generated
            if not st.session_state.interview_questions:
                st.error("Failed to generate questions. Please try again.")
                return
            
            # Display questions
            st.subheader("Interview Questions")
            for i, q in enumerate(st.session_state.interview_questions, 1):
                st.write(f"**Q{i}:** {q['question']}")
                st.write(f"*Difficulty:* {q['difficulty']} | *Focus:* {q['focus']}")

        # Answer and evaluation section (previous implementation remains the same)
        if hasattr(st.session_state, 'interview_questions'):
            st.subheader("Your Answers")
            
            # Prepare to store answers
            st.session_state.interview_answers = []
            
            # Input fields for each question
            for i, q in enumerate(st.session_state.interview_questions, 1):
                answer = st.text_area(f"Q{i}: {q['question']}", key=f"answer_{i}")
                st.session_state.interview_answers.append(answer)
            
            # Evaluate Answers Button
            if st.button("Evaluate My Answers"):
                # Validate all answers are filled
                if not all(st.session_state.interview_answers):
                    st.warning("Please provide answers to all questions before evaluation.")
                    return
                
                # Extract questions text
                questions_text = [q['question'] for q in st.session_state.interview_questions]
                
                # Include resume context in evaluation if available
                context = ""
                if st.session_state.resume_text:
                    context = f"\nCandidate's Resume Context: {st.session_state.resume_text}"
                
                # Get evaluation
                evaluation = evaluate_interview_answers(
                    st.session_state.job_role + context, 
                    questions_text, 
                    st.session_state.interview_answers
                )
                
                # Display evaluation results (previous implementation remains the same)
                if evaluation:
                    st.subheader("🎯 Interview Performance")
                    st.metric("Overall Rating", f"{evaluation.get('overall_rating', 'N/A')}/10")
                    
                    st.write("**Overall Feedback:**")
                    st.write(evaluation.get('overall_feedback', 'No overall feedback available.'))
                    
                    st.subheader("Detailed Question Feedback")
                    
                    for i, feedback in enumerate(evaluation.get('detailed_feedback', []), 1):
                        with st.expander(f"Q{i} Detailed Analysis"):
                            st.write(f"**Original Question:** {st.session_state.interview_questions[i-1]['question']}")
                            st.write(f"**Your Answer:** {st.session_state.interview_answers[i-1]}")
                            
                            st.write(f"**Answer Rating:** {feedback.get('answer_rating', 'N/A')}/10")
                            st.write("**Strengths:**")
                            st.write(feedback.get('strengths', 'No specific strengths noted.'))
                            
                            st.write("**Areas for Improvement:**")
                            st.write(feedback.get('areas_for_improvement', 'No specific improvements suggested.'))
                            
                            st.write("**Suggested Answer Framework:**")
                            st.write(feedback.get('suggested_answer_framework', 'No specific framework provided.'))

    # Normal Chat Tab (remains the same)
    with tab2:
        st.header("Normal Chat")
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'chat_session' not in st.session_state:
            st.session_state.chat_session = model.start_chat(history=[])

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("What would you like to chat about?"):
            st.chat_message("user").markdown(prompt)

            try:
                # Include resume context in chat if available
                context = prompt
                if st.session_state.resume_text:
                    context = f"Context from resume: {st.session_state.resume_text}\n\nUser question: {prompt}"
                
                response = st.session_state.chat_session.send_message(context)
                st.chat_message("assistant").markdown(response.text)

                st.session_state.chat_history.append({
                    "role": "user", 
                    "content": prompt
                })
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": response.text
                })

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
