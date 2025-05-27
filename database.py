import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
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
    pdf_filename = Column(String)
    difficulty = Column(String)
    score_percentage = Column(Float)
    correct_answers = Column(Integer)
    total_questions = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    """Store individual questions and answers"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)
    question_text = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    user_answer = Column(String)
    is_correct = Column(Boolean)
    explanation = Column(String)

class UsedQuestion(Base):
    """Track questions that have been asked to avoid repetition"""
    __tablename__ = 'used_questions'
    
    id = Column(Integer, primary_key=True)
    pdf_filename = Column(String)
    question_text = Column(String)
    used_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Manage database operations for the quiz application"""
    
    def __init__(self):
        # Use SQLite as default database
        self.engine = create_engine('sqlite:///quiz_database.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def save_quiz_session(self, pdf_filename, difficulty, questions, user_answers):
        """Save a completed quiz session to the database"""
        try:
            correct_answers = sum(1 for q, a in zip(questions, user_answers) if q['correct_answer'] == a)
            total_questions = len(questions)
            score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            quiz_session = QuizSession(
                pdf_filename=pdf_filename,
                difficulty=difficulty,
                score_percentage=score_percentage,
                correct_answers=correct_answers,
                total_questions=total_questions
            )
            
            self.session.add(quiz_session)
            self.session.commit()
            return quiz_session.id
        except Exception as e:
            self.session.rollback()
            print(f"Error saving quiz session: {str(e)}")
            return None
    
    def get_quiz_history(self, limit=20):
        """Get recent quiz history"""
        try:
            return self.session.query(QuizSession).order_by(QuizSession.completed_at.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error getting quiz history: {str(e)}")
            return []
    
    def get_performance_stats(self):
        """Get overall performance statistics"""
        try:
            sessions = self.session.query(QuizSession).all()
            if not sessions:
                return {
                    'total_quizzes': 0,
                    'average_score': 0,
                    'best_score': 0,
                    'total_questions_answered': 0,
                    'favorite_difficulty': 'N/A'
                }
            
            total_quizzes = len(sessions)
            average_score = sum(s.score_percentage for s in sessions) / total_quizzes
            best_score = max(s.score_percentage for s in sessions)
            total_questions = sum(s.total_questions for s in sessions)
            
            # Get most common difficulty
            difficulties = [s.difficulty for s in sessions]
            favorite_difficulty = max(set(difficulties), key=difficulties.count)
            
            return {
                'total_quizzes': total_quizzes,
                'average_score': average_score,
                'best_score': best_score,
                'total_questions_answered': total_questions,
                'favorite_difficulty': favorite_difficulty
            }
        except Exception as e:
            print(f"Error getting performance stats: {str(e)}")
            return {
                'total_quizzes': 0,
                'average_score': 0,
                'best_score': 0,
                'total_questions_answered': 0,
                'favorite_difficulty': 'N/A'
            }
    
    def get_quiz_details(self, session_id):
        """Get detailed information about a specific quiz session"""
        if not self.session:
            return None
            
        session = None
        try:
            session = self.session
            
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
    
    def mark_questions_as_used(self, pdf_filename, questions):
        """Mark questions as used to avoid repetition"""
        try:
            for question in questions:
                used_question = UsedQuestion(
                    pdf_filename=pdf_filename,
                    question_text=question['question']
                )
                self.session.add(used_question)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Error marking questions as used: {str(e)}")
    
    def get_used_question_hashes(self, pdf_filename):
        """Get list of question hashes that have been used for this PDF"""
        if not self.session:
            return []
            
        session = None
        try:
            session = self.session
            
            used_questions = session.query(UsedQuestion.question_text)\
                                  .filter_by(pdf_filename=pdf_filename)\
                                  .all()
            
            hashes = [q.question_text for q in used_questions]
            session.close()
            return hashes
            
        except Exception as e:
            print(f"Failed to get used questions: {str(e)}")
            if session:
                session.close()
            return []

# Global database manager instance
db_manager = DatabaseManager()