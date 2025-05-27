import streamlit as st
import os
from pdf_processor import extract_text_from_pdf
from mcq_generator import generate_mcqs
from quiz_manager import QuizManager

def main():
    st.set_page_config(
        page_title="PDF to MCQ Generator",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 PDF to MCQ Generator")
    st.markdown("Upload your study notes PDF and generate customizable multiple choice questions!")
    
    # Initialize session state
    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = None
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'pdf_processed' not in st.session_state:
        st.session_state.pdf_processed = False
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = ""
    
    # Main application flow
    if not st.session_state.quiz_started:
        setup_phase()
    else:
        quiz_phase()

def setup_phase():
    """Handle PDF upload and quiz configuration"""
    
    # PDF Upload Section
    st.header("1. Upload Your PDF")
    uploaded_file = st.file_uploader(
        "Choose a PDF file containing your study notes",
        type="pdf",
        help="Upload a PDF file with text content. Images and scanned documents may not work properly."
    )
    
    if uploaded_file is not None:
        if not st.session_state.pdf_processed:
            with st.spinner("Extracting text from PDF..."):
                try:
                    pdf_text = extract_text_from_pdf(uploaded_file)
                    if not pdf_text.strip():
                        st.error("❌ Could not extract text from the PDF. Please ensure the PDF contains readable text.")
                        return
                    
                    st.session_state.pdf_text = pdf_text
                    st.session_state.pdf_processed = True
                    st.success("✅ PDF text extracted successfully!")
                    
                    # Show text preview
                    with st.expander("📄 Preview extracted text (first 500 characters)"):
                        st.text(pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text)
                        
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {str(e)}")
                    return
        
        if st.session_state.pdf_processed:
            # Configuration Section
            st.header("2. Configure Your Quiz")
            
            col1, col2 = st.columns(2)
            
            with col1:
                difficulty = st.selectbox(
                    "Select Difficulty Level",
                    ["Easy", "Medium", "Hard"],
                    help="Easy: Basic concepts and definitions\nMedium: Application and understanding\nHard: Complex analysis and synthesis"
                )
            
            with col2:
                num_questions = st.number_input(
                    "Number of Questions",
                    min_value=1,
                    max_value=20,
                    value=5,
                    help="Choose how many MCQ questions you want to generate (1-20)"
                )
            
            # Generate Quiz Button
            st.header("3. Generate Questions")
            if st.button("🎯 Generate MCQ Quiz", type="primary", use_container_width=True):
                if len(st.session_state.pdf_text.strip()) < 100:
                    st.error("❌ The extracted text is too short to generate meaningful questions. Please upload a more detailed PDF.")
                    return
                
                with st.spinner(f"Generating {num_questions} {difficulty.lower()} level questions from your PDF..."):
                    try:
                        questions = generate_mcqs(st.session_state.pdf_text, difficulty, num_questions)
                        
                        if not questions:
                            st.error("❌ Failed to generate questions. Please try again or upload a different PDF.")
                            return
                        
                        # Initialize quiz manager
                        st.session_state.quiz_manager = QuizManager(questions)
                        st.session_state.quiz_started = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error generating questions: {str(e)}")

def quiz_phase():
    """Handle the quiz taking phase"""
    quiz_manager = st.session_state.quiz_manager
    
    if quiz_manager.is_completed():
        show_results()
    else:
        show_current_question()

def show_current_question():
    """Display the current question and handle answer submission"""
    quiz_manager = st.session_state.quiz_manager
    current_question = quiz_manager.get_current_question()
    
    # Progress indicator
    progress = (quiz_manager.current_question_index) / len(quiz_manager.questions)
    st.progress(progress)
    
    st.header(f"Question {quiz_manager.current_question_index + 1} of {len(quiz_manager.questions)}")
    
    # Question text
    st.subheader(current_question['question'])
    
    # Answer options
    answer_key = f"answer_{quiz_manager.current_question_index}"
    selected_answer = st.radio(
        "Select your answer:",
        current_question['options'],
        key=answer_key,
        index=None
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⏮️ Start Over", help="Restart the entire quiz"):
            # Reset everything
            st.session_state.quiz_started = False
            st.session_state.pdf_processed = False
            st.session_state.quiz_manager = None
            st.session_state.pdf_text = ""
            st.rerun()
    
    with col3:
        if st.button("➡️ Next Question", type="primary", disabled=selected_answer is None):
            if selected_answer is not None:
                quiz_manager.submit_answer(selected_answer)
                st.rerun()
    
    # Show question source hint
    with st.expander("💡 Need help? View relevant text from your PDF"):
        # Find relevant text snippet (simple keyword matching)
        question_words = current_question['question'].lower().split()
        pdf_sentences = st.session_state.pdf_text.split('.')
        
        relevant_sentences = []
        for sentence in pdf_sentences:
            if any(word in sentence.lower() for word in question_words if len(word) > 3):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            st.text("\n".join(relevant_sentences[:3]))  # Show up to 3 relevant sentences
        else:
            st.text("Review your uploaded PDF content for context.")

def show_results():
    """Display final quiz results"""
    quiz_manager = st.session_state.quiz_manager
    score, total = quiz_manager.get_score()
    percentage = (score / total) * 100
    
    st.balloons()
    st.header("🎉 Quiz Completed!")
    
    # Score display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{score}/{total}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        if percentage >= 80:
            st.metric("Grade", "🏆 Excellent")
        elif percentage >= 60:
            st.metric("Grade", "👍 Good")
        else:
            st.metric("Grade", "📚 Keep Studying")
    
    # Detailed results
    st.header("📊 Detailed Results")
    
    for i, (question_data, user_answer) in enumerate(zip(quiz_manager.questions, quiz_manager.user_answers)):
        is_correct = user_answer == question_data['correct_answer']
        
        with st.expander(f"Question {i+1} {'✅' if is_correct else '❌'}"):
            st.write(f"**Question:** {question_data['question']}")
            st.write(f"**Your Answer:** {user_answer}")
            st.write(f"**Correct Answer:** {question_data['correct_answer']}")
            
            if not is_correct:
                st.error("Incorrect")
            else:
                st.success("Correct!")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Generate New Quiz", type="primary", use_container_width=True):
            st.session_state.quiz_started = False
            st.session_state.quiz_manager = None
            st.rerun()
    
    with col2:
        if st.button("📚 Upload New PDF", use_container_width=True):
            # Reset everything
            st.session_state.quiz_started = False
            st.session_state.pdf_processed = False
            st.session_state.quiz_manager = None
            st.session_state.pdf_text = ""
            st.rerun()

if __name__ == "__main__":
    main()
