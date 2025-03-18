# Create a new file: backend/services/chat_service.py

import json
import logging
from datetime import datetime
from contextlib import contextmanager
from backend.database import get_snowflake_connection

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling LLM-powered chat interactions."""
    
    MAX_RETRIES = 3
    
    def __init__(self):
        """Initialize Snowflake connection for chat service."""
        self.conn = None
        self._connect()
    
    def _connect(self, retry_count=0):
        """Establish connection to Snowflake with retry logic."""
        try:
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass

            self.conn = get_snowflake_connection()
            if self.conn:
                logger.info("✅ Successfully connected to Snowflake for Chat Service")
            else:
                raise Exception("❌ Failed to connect to Snowflake for Chat Service")
        except Exception as e:
            logger.error(f"❌ Error connecting to Snowflake: {e}")
            if retry_count < self.MAX_RETRIES:
                logger.info(f"🔄 Retrying connection (attempt {retry_count + 1}/{self.MAX_RETRIES})")
                self._connect(retry_count + 1)
            else:
                raise
    
    @contextmanager
    def get_cursor(self):
        """Provide a context manager for Snowflake cursors."""
        cursor = None
        try:
            cursor = self.conn.cursor()
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
    
    def _ensure_connection(self):
        """Ensure the Snowflake connection is active."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();")
                cursor.fetchone()
        except Exception:
            logger.info("🔄 Reconnecting to Snowflake...")
            self._connect()
    
    def get_llm_response(self, prompt, context=None, max_retries=2):
        """
        Get a response from an LLM using Snowflake Cortex.
        
        Args:
            prompt (str): The prompt to send to the LLM
            context (str, optional): Additional context for the LLM
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: The LLM response or a fallback message
        """
        self._ensure_connection()
        
        # Combine prompt with context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n{prompt}"
        
        # Available models to try
        models = [
            'llama3.1-70b',
            'llama3.1-8b',
            'snowflake-llama-3.1-405b'
        ]
        
        # Try each model
        for model in models:
            for attempt in range(max_retries):
                try:
                    with self.get_cursor() as cursor:
                        query = f"""
                        SELECT SNOWFLAKE.CORTEX.COMPLETE(
                            '{model}',
                            '{full_prompt}'
                        ) AS response;
                        """
                        cursor.execute(query)
                        response = cursor.fetchone()[0]
                        return response
                        
                except Exception as e:
                    logger.warning(f"❌ Error with model {model} (attempt {attempt+1}): {str(e)}")
                    if attempt == max_retries - 1:
                        continue  # Try next model
        
        # Fallback response if all models fail
        logger.error("❌ All LLM models failed to generate a response")
        return "I'm sorry, I'm having trouble analyzing that right now. Let me provide a general response based on best practices."
    
    def extract_skills(self, resume_text):
        """
        Use LLM to extract skills from resume text.
        
        Args:
            resume_text (str): The resume text to analyze
            
        Returns:
            list: Extracted skills 
        """
        prompt = (
            "Extract all technical skills, soft skills, and domain knowledge from the following resume. "
            "Return the result as a JSON list of strings containing only the skill names. "
            "Do not include explanations, categories, or any other text. Just the JSON list.\n\n"
            f"Resume text: {resume_text[:4000]}..."  # Truncate for token limits
        )
        
        try:
            response = self.get_llm_response(prompt)
            
            # Extract JSON list from response 
            # (handles cases where model might add explanatory text)
            import re
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            
            if json_match:
                skills_json = f"[{json_match.group(1)}]"
                skills = json.loads(skills_json)
                return skills
            else:
                # Fallback extraction if JSON parsing fails
                skills = []
                for line in response.split('\n'):
                    line = line.strip().strip('"-,')
                    if line and not line.startswith('[') and not line.startswith(']'):
                        skills.append(line)
                return skills
                
        except Exception as e:
            logger.error(f"❌ Error extracting skills with LLM: {str(e)}")
            # Fallback to keyword matching
            common_skills = ["Python", "Java", "JavaScript", "HTML", "CSS", "SQL", 
                            "Machine Learning", "Data Analysis", "Project Management",
                            "AWS", "Azure", "Docker", "Kubernetes", "React", "Angular",
                            "Leadership", "Communication", "Problem Solving"]
            
            extracted_skills = []
            for skill in common_skills:
                if skill.lower() in resume_text.lower():
                    extracted_skills.append(skill)
            
            return extracted_skills
    
    def generate_career_advice(self, current_skills, target_role):
        """
        Generate personalized career advice for transitioning to a target role.
        
        Args:
            current_skills (list): List of current skills from resume
            target_role (str): Target role for career transition
            
        Returns:
            str: Career advice in markdown format
        """
        prompt = (
            f"You are a career coach helping someone transition to a {target_role} role. "
            f"Their current skills are: {', '.join(current_skills)}. "
            "Provide detailed, personalized advice with the following sections:\n"
            "1. Skills Assessment: Evaluate their current skills relevant to the target role\n"
            "2. Skills Gap: Identify key skills they need to develop\n"
            "3. Learning Path: Recommend specific courses, resources, or training\n"
            "4. Project Ideas: Suggest portfolio projects to demonstrate new skills\n"
            "5. Networking: Tips for connecting with professionals in the target field\n\n"
            "Format your response in Markdown with clear headings and bullet points."
        )
        
        try:
            return self.get_llm_response(prompt)
        except Exception as e:
            logger.error(f"❌ Error generating career advice: {str(e)}")
            
            # Fallback template
            return (
                f"# Career Transition Plan: {target_role}\n\n"
                f"## Skills Assessment\n"
                f"You have some valuable skills that can help in your transition: {', '.join(current_skills[:5])}\n\n"
                f"## Recommended Next Steps\n"
                f"1. Consider taking courses in key technologies for {target_role}\n"
                f"2. Build a portfolio of projects showing your abilities\n"
                f"3. Network with professionals in this field\n"
                f"4. Update your resume to highlight relevant experience\n"
            )
    
    def answer_career_question(self, question, user_context):
        """
        Answer a follow-up career question using LLM.
        
        Args:
            question (str): The user's question
            user_context (dict): Context about the user, including skills and target role
            
        Returns:
            str: Response to the question
        """
        context = (
            f"You are a career coach helping someone transition to a {user_context.get('target_role')} role. "
            f"Their current skills include: {', '.join(user_context.get('skills', [])[:7])}. "
            "Provide helpful, specific advice based on this context."
        )
        
        try:
            return self.get_llm_response(question, context=context)
        except Exception as e:
            logger.error(f"❌ Error answering career question: {str(e)}")
            
            # Fallback response
            return (
                f"That's a great question about transitioning to a {user_context.get('target_role')} role. "
                f"Based on your background, I recommend focusing on developing relevant technical skills, "
                f"building a portfolio of projects, and networking with professionals in the field. "
                f"This combination of skill development and professional connections will maximize your "
                f"chances of a successful transition."
            )