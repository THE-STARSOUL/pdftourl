import os
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import streamlit as st

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
Base = declarative_base()

class QuizSession(Base):
    """Store quiz session information"""
    __tablename__ = 'quiz_sessions'
    
    id = Column(Integer, primary_key=True)
    pdf_filename = Column(String(255), nullable=False)
    difficulty = Column(String(50), nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class Question(Base):
    """Store individual questions and answers"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(10), nullable=False)
    user_answer = Column(String(10))
    is_correct = Column(Boolean)
    explanation = Column(Text)

class DatabaseManager:
    """Manage database operations for the quiz application"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.setup_database()
    
    def setup_database(self):
        """Initialize database connection and create tables"""
        try:
            if not DATABASE_URL:
                st.error("Database URL not found. Please check your database configuration.")
                return
            
            self.engine = create_engine(DATABASE_URL)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            
        except Exception as e:
            st.error(f"Database setup failed: {str(e)}")
    
    def save_quiz_session(self, pdf_filename, difficulty, questions, user_answers):
        """Save a completed quiz session to the database"""
        if not self.Session:
            return None
            
        session = None
        try:
            session = self.Session()
            
            # Calculate score
            correct_count = sum(1 for i, q in enumerate(questions) 
                              if i < len(user_answers) and user_answers[i] == q['correct_answer'])
            score_percentage = (correct_count / len(questions)) * 100 if questions else 0
            
            # Create quiz session record
            quiz_session = QuizSession(
                pdf_filename=pdf_filename,
                difficulty=difficulty,
                total_questions=len(questions),
                correct_answers=correct_count,
                score_percentage=score_percentage,
                completed_at=datetime.utcnow()
            )
            
            session.add(quiz_session)
            session.flush()  # Get the session ID
            
            # Save individual questions
            for i, question_data in enumerate(questions):
                user_answer = user_answers[i] if i < len(user_answers) else None
                is_correct = user_answer == question_data['correct_answer'] if user_answer else False
                
                # Extract options from the question
                options = question_data['options']
                option_a = options[0] if len(options) > 0 else ""
                option_b = options[1] if len(options) > 1 else ""
                option_c = options[2] if len(options) > 2 else ""
                option_d = options[3] if len(options) > 3 else ""
                
                question = Question(
                    session_id=quiz_session.id,
                    question_text=question_data['question'],
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=question_data['correct_answer'],
                    user_answer=user_answer,
                    is_correct=is_correct,
                    explanation=question_data.get('explanation', '')
                )
                
                session.add(question)
            
            session.commit()
            session_id = quiz_session.id
            session.close()
            
            return session_id
            
        except Exception as e:
            print(f"Database error: {str(e)}")  # Use print instead of st.error for debugging
            if session:
                session.rollback()
                session.close()
            return None
    
    def get_quiz_history(self, limit=10):
        """Get recent quiz history"""
        if not self.Session:
            return []
            
        session = None
        try:
            session = self.Session()
            
            quiz_sessions = session.query(QuizSession)\
                                 .order_by(QuizSession.completed_at.desc())\
                                 .limit(limit)\
                                 .all()
            
            history = []
            for quiz in quiz_sessions:
                history.append({
                    'id': quiz.id,
                    'pdf_filename': quiz.pdf_filename,
                    'difficulty': quiz.difficulty,
                    'total_questions': quiz.total_questions,
                    'correct_answers': quiz.correct_answers,
                    'score_percentage': quiz.score_percentage,
                    'completed_at': quiz.completed_at
                })
            
            session.close()
            return history
            
        except Exception as e:
            print(f"Failed to retrieve quiz history: {str(e)}")
            if session:
                session.close()
            return []
    
    def get_performance_stats(self):
        """Get overall performance statistics"""
        if not self.Session:
            return {
                'total_quizzes': 0,
                'average_score': 0,
                'total_questions_answered': 0,
                'best_score': 0,
                'favorite_difficulty': 'N/A'
            }
            
        session = None
        try:
            session = self.Session()
            
            # Get total quizzes taken
            total_quizzes = session.query(QuizSession).count()
            
            if total_quizzes == 0:
                session.close()
                return {
                    'total_quizzes': 0,
                    'average_score': 0,
                    'total_questions_answered': 0,
                    'best_score': 0,
                    'favorite_difficulty': 'N/A'
                }
            
            # Calculate average score
            avg_score = session.query(sqlalchemy.func.avg(QuizSession.score_percentage)).scalar()
            
            # Get best score
            best_score = session.query(sqlalchemy.func.max(QuizSession.score_percentage)).scalar()
            
            # Get total questions answered
            total_questions = session.query(sqlalchemy.func.sum(QuizSession.total_questions)).scalar()
            
            # Get most common difficulty
            difficulty_count = session.query(QuizSession.difficulty, 
                                           sqlalchemy.func.count(QuizSession.difficulty))\
                                    .group_by(QuizSession.difficulty)\
                                    .order_by(sqlalchemy.func.count(QuizSession.difficulty).desc())\
                                    .first()
            
            favorite_difficulty = difficulty_count[0] if difficulty_count else 'N/A'
            
            session.close()
            
            return {
                'total_quizzes': total_quizzes,
                'average_score': round(avg_score, 1) if avg_score else 0,
                'total_questions_answered': total_questions or 0,
                'best_score': round(best_score, 1) if best_score else 0,
                'favorite_difficulty': favorite_difficulty
            }
            
        except Exception as e:
            print(f"Failed to retrieve performance stats: {str(e)}")
            if session:
                session.close()
            return {
                'total_quizzes': 0,
                'average_score': 0,
                'total_questions_answered': 0,
                'best_score': 0,
                'favorite_difficulty': 'N/A'
            }
    
    def get_quiz_details(self, session_id):
        """Get detailed information about a specific quiz session"""
        if not self.Session:
            return None
            
        session = None
        try:
            session = self.Session()
            
            # Get quiz session
            quiz_session = session.query(QuizSession).filter_by(id=session_id).first()
            
            if not quiz_session:
                session.close()
                return None
            
            # Get questions for this session
            questions = session.query(Question).filter_by(session_id=session_id).all()
            
            quiz_details = {
                'session_info': {
                    'id': quiz_session.id,
                    'pdf_filename': quiz_session.pdf_filename,
                    'difficulty': quiz_session.difficulty,
                    'total_questions': quiz_session.total_questions,
                    'correct_answers': quiz_session.correct_answers,
                    'score_percentage': quiz_session.score_percentage,
                    'completed_at': quiz_session.completed_at
                },
                'questions': []
            }
            
            for q in questions:
                quiz_details['questions'].append({
                    'question_text': q.question_text,
                    'options': [q.option_a, q.option_b, q.option_c, q.option_d],
                    'correct_answer': q.correct_answer,
                    'user_answer': q.user_answer,
                    'is_correct': q.is_correct,
                    'explanation': q.explanation
                })
            
            session.close()
            return quiz_details
            
        except Exception as e:
            print(f"Failed to retrieve quiz details: {str(e)}")
            if session:
                session.close()
            return None

# Global database manager instance
db_manager = DatabaseManager()