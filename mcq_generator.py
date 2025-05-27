import json
import os
import anthropic
from anthropic import Anthropic
import streamlit as st

# the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def generate_mcqs(pdf_text, difficulty, num_questions):
    """
    Generate multiple choice questions from PDF text using Anthropic Claude
    
    Args:
        pdf_text (str): Extracted text from PDF
        difficulty (str): Difficulty level - "Easy", "Medium", or "Hard"
        num_questions (int): Number of questions to generate
        
    Returns:
        list: List of MCQ dictionaries with question, options, and correct answer
    """
    if not ANTHROPIC_API_KEY:
        raise Exception("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Create the prompt based on difficulty level
        system_prompt = create_system_prompt(difficulty)
        user_prompt = create_user_prompt(pdf_text, num_questions, difficulty)
        
        # Call Anthropic API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Parse the response
        response_text = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
        
        # Extract JSON from response (Claude might wrap it in markdown)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        result = json.loads(response_text)
        
        # Validate and format the questions
        questions = validate_and_format_questions(result.get('questions', []))
        
        if len(questions) < num_questions:
            st.warning(f"Only {len(questions)} out of {num_questions} questions could be generated from the PDF content.")
        
        return questions
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to generate questions: {str(e)}")

def create_system_prompt(difficulty):
    """Create system prompt based on difficulty level"""
    
    base_prompt = """You are an expert educational content creator specializing in generating high-quality multiple choice questions from academic text. Your task is to create MCQs that test comprehension and knowledge based ONLY on the provided content.

IMPORTANT RULES:
1. Generate questions ONLY from the provided text content
2. Do not use any external knowledge beyond what's in the text
3. Each question must have exactly 4 options (A, B, C, D)
4. Only one option should be correct
5. Incorrect options should be plausible but clearly wrong
6. Questions should be clear, unambiguous, and grammatically correct
7. Avoid overly obvious answers or trick questions"""

    difficulty_specific = {
        "Easy": """
DIFFICULTY: EASY
- Focus on basic facts, definitions, and simple recall
- Test direct information stated in the text
- Use straightforward language
- Avoid complex reasoning or analysis
- Questions should test "what" and "who" type information""",
        
        "Medium": """
DIFFICULTY: MEDIUM  
- Focus on understanding, application, and connections
- Test comprehension of concepts and relationships
- Require some interpretation of the text
- Include "how" and "why" type questions
- Test ability to connect different parts of the content""",
        
        "Hard": """
DIFFICULTY: HARD
- Focus on analysis, synthesis, and evaluation
- Test deep understanding and critical thinking
- Require inference and interpretation
- Include complex relationships and implications
- Test ability to analyze and draw conclusions from the content"""
    }
    
    return base_prompt + "\n\n" + difficulty_specific.get(difficulty, difficulty_specific["Medium"])

def create_user_prompt(pdf_text, num_questions, difficulty):
    """Create user prompt with PDF content and requirements"""
    
    # Truncate text if too long (to avoid token limits)
    max_text_length = 8000  # Adjust based on model limits
    if len(pdf_text) > max_text_length:
        pdf_text = pdf_text[:max_text_length] + "..."
    
    prompt = f"""Based on the following text content, generate exactly {num_questions} multiple choice questions at {difficulty} difficulty level.

TEXT CONTENT:
{pdf_text}

REQUIREMENTS:
- Generate exactly {num_questions} questions
- Each question must be based on information present in the above text
- Provide 4 options for each question (A, B, C, D)
- Clearly indicate the correct answer
- Ensure questions test {difficulty.lower()} level understanding

RESPONSE FORMAT (JSON):
{{
    "questions": [
        {{
            "question": "Your question text here?",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A) Option 1",
            "explanation": "Brief explanation of why this answer is correct"
        }}
    ]
}}

Generate the MCQ questions now:"""
    
    return prompt

def validate_and_format_questions(questions):
    """
    Validate and format the generated questions
    
    Args:
        questions (list): Raw questions from AI response
        
    Returns:
        list: Validated and formatted questions
    """
    validated_questions = []
    
    for i, q in enumerate(questions):
        try:
            # Check required fields
            if not all(key in q for key in ['question', 'options', 'correct_answer']):
                continue
            
            # Validate question text
            question_text = q['question'].strip()
            if not question_text:
                continue
            
            # Validate options
            options = q['options']
            if not isinstance(options, list) or len(options) != 4:
                continue
            
            # Clean and validate options
            clean_options = []
            for option in options:
                if isinstance(option, str):
                    clean_option = option.strip()
                    if clean_option:
                        clean_options.append(clean_option)
            
            if len(clean_options) != 4:
                continue
            
            # Validate correct answer
            correct_answer = q['correct_answer'].strip()
            if correct_answer not in clean_options:
                continue
            
            # Format the question
            formatted_question = {
                'question': question_text,
                'options': clean_options,
                'correct_answer': correct_answer,
                'explanation': q.get('explanation', '').strip()
            }
            
            validated_questions.append(formatted_question)
            
        except Exception as e:
            # Skip invalid questions
            continue
    
    return validated_questions

def test_anthropic_connection():
    """Test if Anthropic API is accessible"""
    try:
        if not ANTHROPIC_API_KEY:
            return False, "Anthropic API key not found"
        
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Simple test call
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        return True, "Anthropic API connection successful"
        
    except Exception as e:
        return False, f"Anthropic API connection failed: {str(e)}"

def estimate_question_generation_time(text_length, num_questions):
    """
    Estimate time needed for question generation
    
    Args:
        text_length (int): Length of the PDF text
        num_questions (int): Number of questions to generate
        
    Returns:
        int: Estimated time in seconds
    """
    # Base time per question (in seconds)
    base_time_per_question = 3
    
    # Additional time based on text length
    text_factor = min(text_length / 1000, 5)  # Cap at 5 seconds additional
    
    total_time = (base_time_per_question + text_factor) * num_questions
    
    return max(10, min(total_time, 120))  # Between 10 seconds and 2 minutes
