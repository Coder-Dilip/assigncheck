import json
import openai
from typing import List, Dict, Any
from ..core.config import settings
from ..schemas.viva import AIQuestionRequest, AIQuestionResponse


class AIService:
    def __init__(self):
        # Configure Azure OpenAI
        openai.api_type = "azure"
        openai.api_base = settings.AZURE_OPENAI_ENDPOINT
        openai.api_version = settings.AZURE_OPENAI_API_VERSION
        openai.api_key = settings.AZURE_OPENAI_API_KEY

    async def generate_viva_question(self, request: AIQuestionRequest) -> AIQuestionResponse:
        """Generate an adaptive viva question based on assignment context and student responses"""
        
        system_prompt = """You are an AI interviewer for an educational viva (oral examination). 
        Your role is to generate thoughtful, adaptive questions that test student understanding.
        
        Guidelines:
        - Ask questions that build on the assignment context and student's written answers
        - Adapt difficulty based on previous responses
        - Focus on conceptual understanding, not just memorization
        - Generate follow-up questions for deeper exploration
        - Provide clear scoring criteria
        
        Return your response as a JSON object with the following structure:
        {
            "question": "The main question to ask",
            "expected_keywords": ["keyword1", "keyword2", "keyword3"],
            "follow_up_questions": ["follow-up 1", "follow-up 2"],
            "scoring_criteria": {
                "excellent": "Criteria for excellent response (90-100%)",
                "good": "Criteria for good response (70-89%)",
                "satisfactory": "Criteria for satisfactory response (50-69%)",
                "needs_improvement": "Criteria for needs improvement (0-49%)"
            }
        }"""

        user_prompt = f"""
        Assignment Context: {request.assignment_context}
        
        Student's Written Answers: {request.student_answers}
        
        Previous Viva Responses: {request.previous_responses if request.previous_responses else "None"}
        
        Difficulty Level: {request.difficulty_level}
        Question Type: {request.question_type}
        
        Generate an appropriate viva question that tests the student's understanding of the concepts.
        """

        try:
            response = openai.ChatCompletion.create(
                engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            question_data = json.loads(content)
            
            return AIQuestionResponse(
                question=question_data["question"],
                expected_keywords=question_data["expected_keywords"],
                follow_up_questions=question_data["follow_up_questions"],
                scoring_criteria=question_data["scoring_criteria"]
            )
            
        except Exception as e:
            # Fallback question if AI fails
            return AIQuestionResponse(
                question="Can you explain the main concepts from your assignment in your own words?",
                expected_keywords=["concept", "understanding", "explanation"],
                follow_up_questions=["Can you provide an example?", "How would you apply this?"],
                scoring_criteria={
                    "excellent": "Clear explanation with examples and applications",
                    "good": "Good understanding with minor gaps",
                    "satisfactory": "Basic understanding demonstrated",
                    "needs_improvement": "Limited understanding shown"
                }
            )

    async def evaluate_viva_response(
        self, 
        question: str, 
        response: str, 
        expected_keywords: List[str],
        scoring_criteria: Dict[str, str]
    ) -> Dict[str, Any]:
        """Evaluate a student's viva response and provide scoring and feedback"""
        
        system_prompt = """You are an AI evaluator for educational viva responses. 
        Analyze the student's response and provide objective scoring and constructive feedback.
        
        Return your evaluation as a JSON object with:
        {
            "accuracy_score": 0.85,  // 0-1 scale for technical accuracy
            "completeness_score": 0.75,  // 0-1 scale for completeness
            "confidence_score": 0.80,  // 0-1 scale for apparent confidence
            "keywords_matched": ["keyword1", "keyword2"],  // matched keywords
            "overall_score": 0.80,  // 0-1 scale overall
            "feedback": "Detailed constructive feedback",
            "strengths": ["strength1", "strength2"],
            "areas_for_improvement": ["area1", "area2"]
        }"""

        user_prompt = f"""
        Question Asked: {question}
        
        Student Response: {response}
        
        Expected Keywords: {expected_keywords}
        
        Scoring Criteria: {json.dumps(scoring_criteria, indent=2)}
        
        Evaluate this response and provide detailed feedback.
        """

        try:
            response_obj = openai.ChatCompletion.create(
                engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response_obj.choices[0].message.content
            evaluation = json.loads(content)
            
            return evaluation
            
        except Exception as e:
            # Fallback evaluation
            return {
                "accuracy_score": 0.7,
                "completeness_score": 0.7,
                "confidence_score": 0.7,
                "keywords_matched": [],
                "overall_score": 0.7,
                "feedback": "Response received and recorded. Manual review recommended.",
                "strengths": ["Attempted to answer the question"],
                "areas_for_improvement": ["Could provide more detail"]
            }

    async def generate_mock_questions(
        self, 
        assignment_context: str, 
        difficulty_preference: str = "similar",
        question_count: int = 5
    ) -> List[AIQuestionResponse]:
        """Generate mock viva questions for practice"""
        
        difficulty_map = {
            "easier": "beginner",
            "similar": "intermediate", 
            "harder": "advanced"
        }
        
        difficulty = difficulty_map.get(difficulty_preference, "intermediate")
        
        system_prompt = f"""Generate {question_count} mock viva questions for practice.
        These should be conceptually similar to the assignment but NOT identical to avoid cheating.
        
        Difficulty level: {difficulty}
        
        Return as a JSON array of question objects with the same structure as before."""

        user_prompt = f"""
        Assignment Context: {assignment_context}
        
        Generate {question_count} practice questions that help students prepare for their viva.
        Focus on testing understanding rather than memorization.
        """

        try:
            response = openai.ChatCompletion.create(
                engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            questions_data = json.loads(content)
            
            return [
                AIQuestionResponse(
                    question=q["question"],
                    expected_keywords=q["expected_keywords"],
                    follow_up_questions=q["follow_up_questions"],
                    scoring_criteria=q["scoring_criteria"]
                )
                for q in questions_data
            ]
            
        except Exception as e:
            # Fallback questions
            return [
                AIQuestionResponse(
                    question=f"Practice question {i+1}: Explain a key concept from the assignment.",
                    expected_keywords=["concept", "explanation"],
                    follow_up_questions=["Can you elaborate?"],
                    scoring_criteria={
                        "excellent": "Clear and detailed explanation",
                        "good": "Good understanding shown",
                        "satisfactory": "Basic explanation provided",
                        "needs_improvement": "Unclear or incomplete"
                    }
                )
                for i in range(question_count)
            ]

    async def generate_session_summary(
        self, 
        questions_and_responses: List[Dict[str, str]],
        overall_performance: Dict[str, float]
    ) -> str:
        """Generate a comprehensive summary of the viva session"""
        
        system_prompt = """Generate a comprehensive summary of a viva session.
        Provide constructive feedback highlighting strengths and areas for improvement.
        Be encouraging while being honest about performance."""

        user_prompt = f"""
        Viva Session Data:
        Questions and Responses: {json.dumps(questions_and_responses, indent=2)}
        
        Overall Performance Metrics: {json.dumps(overall_performance, indent=2)}
        
        Generate a summary that includes:
        1. Overall performance assessment
        2. Key strengths demonstrated
        3. Areas for improvement
        4. Specific recommendations for further learning
        """

        try:
            response = openai.ChatCompletion.create(
                engine=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return "Viva session completed. Manual review recommended for detailed feedback."


# Global AI service instance
ai_service = AIService()
