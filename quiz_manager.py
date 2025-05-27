class QuizManager:
    """
    Manages the quiz state, progress, and scoring
    """
    
    def __init__(self, questions):
        """
        Initialize quiz manager with questions
        
        Args:
            questions (list): List of MCQ dictionaries
        """
        self.questions = questions
        self.current_question_index = 0
        self.user_answers = []
        self.completed = False
    
    def get_current_question(self):
        """
        Get the current question
        
        Returns:
            dict: Current question data
        """
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def submit_answer(self, answer):
        """
        Submit answer for current question and move to next
        
        Args:
            answer (str): Selected answer option
        """
        if self.current_question_index < len(self.questions):
            self.user_answers.append(answer)
            self.current_question_index += 1
            
            # Check if quiz is completed
            if self.current_question_index >= len(self.questions):
                self.completed = True
    
    def get_progress(self):
        """
        Get current progress information
        
        Returns:
            dict: Progress information
        """
        return {
            'current_question': self.current_question_index + 1,
            'total_questions': len(self.questions),
            'progress_percentage': (self.current_question_index / len(self.questions)) * 100,
            'completed': self.completed
        }
    
    def is_completed(self):
        """
        Check if quiz is completed
        
        Returns:
            bool: True if quiz is completed
        """
        return self.completed
    
    def get_score(self):
        """
        Calculate and return the quiz score
        
        Returns:
            tuple: (correct_answers, total_questions)
        """
        if not self.completed:
            return 0, len(self.questions)
        
        correct_count = 0
        for i, user_answer in enumerate(self.user_answers):
            if i < len(self.questions):
                correct_answer = self.questions[i]['correct_answer']
                if user_answer == correct_answer:
                    correct_count += 1
        
        return correct_count, len(self.questions)
    
    def get_detailed_results(self):
        """
        Get detailed results for each question
        
        Returns:
            list: List of result dictionaries for each question
        """
        results = []
        
        for i, question in enumerate(self.questions):
            if i < len(self.user_answers):
                user_answer = self.user_answers[i]
                correct_answer = question['correct_answer']
                is_correct = user_answer == correct_answer
                
                result = {
                    'question_number': i + 1,
                    'question': question['question'],
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'explanation': question.get('explanation', ''),
                    'options': question['options']
                }
                
                results.append(result)
        
        return results
    
    def reset_quiz(self):
        """
        Reset the quiz to start over
        """
        self.current_question_index = 0
        self.user_answers = []
        self.completed = False
    
    def get_question_by_index(self, index):
        """
        Get question by specific index
        
        Args:
            index (int): Question index
            
        Returns:
            dict: Question data or None if index is invalid
        """
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None
    
    def has_previous_question(self):
        """
        Check if there's a previous question
        
        Returns:
            bool: True if previous question exists
        """
        return self.current_question_index > 0
    
    def has_next_question(self):
        """
        Check if there's a next question
        
        Returns:
            bool: True if next question exists
        """
        return self.current_question_index < len(self.questions) - 1
    
    def get_performance_summary(self):
        """
        Get performance summary statistics
        
        Returns:
            dict: Performance statistics
        """
        if not self.completed:
            return None
        
        correct_count, total_count = self.get_score()
        percentage = (correct_count / total_count) * 100 if total_count > 0 else 0
        
        # Determine performance level
        if percentage >= 90:
            performance_level = "Excellent"
            performance_emoji = "🏆"
        elif percentage >= 80:
            performance_level = "Very Good"
            performance_emoji = "🥇"
        elif percentage >= 70:
            performance_level = "Good"
            performance_emoji = "👍"
        elif percentage >= 60:
            performance_level = "Fair"
            performance_emoji = "👌"
        else:
            performance_level = "Needs Improvement"
            performance_emoji = "📚"
        
        return {
            'score': correct_count,
            'total': total_count,
            'percentage': percentage,
            'performance_level': performance_level,
            'performance_emoji': performance_emoji,
            'questions_correct': correct_count,
            'questions_incorrect': total_count - correct_count
        }
