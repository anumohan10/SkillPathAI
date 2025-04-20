# # Create a new file: backend/services/chat_service.py

# import json
# import logging
# from datetime import datetime
# from contextlib import contextmanager
# from backend.database import get_snowflake_connection

# logger = logging.getLogger(__name__)

# class ChatService:
#     """Service for handling LLM-powered chat interactions."""
    
#     MAX_RETRIES = 3
    
#     def __init__(self):
#         """Initialize Snowflake connection for chat service."""
#         self.conn = None
#         self._connect()
    
#     def _connect(self, retry_count=0):
#         """Establish connection to Snowflake with retry logic."""
#         try:
#             if self.conn:
#                 try:
#                     self.conn.close()
#                 except Exception:
#                     pass

#             self.conn = get_snowflake_connection()
#             if self.conn:
#                 logger.info("✅ Successfully connected to Snowflake for Chat Service")
#             else:
#                 raise Exception("❌ Failed to connect to Snowflake for Chat Service")
#         except Exception as e:
#             logger.error(f"❌ Error connecting to Snowflake: {e}")
#             if retry_count < self.MAX_RETRIES:
#                 logger.info(f"🔄 Retrying connection (attempt {retry_count + 1}/{self.MAX_RETRIES})")
#                 self._connect(retry_count + 1)
#             else:
#                 raise
    
#     @contextmanager
#     def get_cursor(self):
#         """Provide a context manager for Snowflake cursors."""
#         cursor = None
#         try:
#             cursor = self.conn.cursor()
#             yield cursor
#             self.conn.commit()
#         except Exception as e:
#             self.conn.rollback()
#             raise e
#         finally:
#             if cursor:
#                 cursor.close()
    
#     def _ensure_connection(self):
#         """Ensure the Snowflake connection is active."""
#         try:
#             with self.get_cursor() as cursor:
#                 cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();")
#                 cursor.fetchone()
#         except Exception:
#             logger.info("🔄 Reconnecting to Snowflake...")
#             self._connect()
    
#     def get_llm_response(self, prompt, context=None, max_retries=2):
#         """
#         Get a response from an LLM using Snowflake Cortex.
        
#         Args:
#             prompt (str): The prompt to send to the LLM
#             context (str, optional): Additional context for the LLM
#             max_retries (int): Maximum number of retry attempts
            
#         Returns:
#             str: The LLM response or a fallback message
#         """
#         self._ensure_connection()
        
#         # Combine prompt with context if provided
#         full_prompt = prompt
#         if context:
#             full_prompt = f"{context}\n\n{prompt}"
        
#         # Available models to try
#         models = [
#             'llama3.1-70b',
#             'llama3.1-8b',
#             'snowflake-llama-3.1-405b'
#         ]
        
#         # Try each model
#         for model in models:
#             for attempt in range(max_retries):
#                 try:
#                     with self.get_cursor() as cursor:
#                         query = f"""
#                         SELECT SNOWFLAKE.CORTEX.COMPLETE(
#                             '{model}',
#                             '{full_prompt}'
#                         ) AS response;
#                         """
#                         cursor.execute(query)
#                         response = cursor.fetchone()[0]
#                         return response
                        
#                 except Exception as e:
#                     logger.warning(f"❌ Error with model {model} (attempt {attempt+1}): {str(e)}")
#                     if attempt == max_retries - 1:
#                         continue  # Try next model
        
#         # Fallback response if all models fail
#         logger.error("❌ All LLM models failed to generate a response")
#         return "I'm sorry, I'm having trouble analyzing that right now. Let me provide a general response based on best practices."
    
#     def extract_skills(self, resume_text):
#         """
#         Use LLM to extract skills from resume text.
        
#         Args:
#             resume_text (str): The resume text to analyze
            
#         Returns:
#             list: Extracted skills 
#         """
#         prompt = (
#             "Extract all technical skills, soft skills, and domain knowledge from the following resume. "
#             "Return the result as a JSON list of strings containing only the skill names. "
#             "Be comprehensive and include all identifiable skills. "
#             "Do not include explanations, categories, or any other text. Just the JSON list.\n\n"
#             f"Resume text: {resume_text[:4000]}..."  # Truncate for token limits
#         )
        
#         try:
#             response = self.get_llm_response(prompt)
            
#             # Extract JSON list from response 
#             # (handles cases where model might add explanatory text)
#             import re
#             json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            
#             if json_match:
#                 skills_json = f"[{json_match.group(1)}]"
#                 skills = json.loads(skills_json)
#                 return skills
#             else:
#                 # Fallback extraction if JSON parsing fails
#                 skills = []
#                 for line in response.split('\n'):
#                     line = line.strip().strip('"-,')
#                     if line and not line.startswith('[') and not line.startswith(']'):
#                         skills.append(line)
#                 return skills
                
#         except Exception as e:
#             logger.error(f"❌ Error extracting skills with LLM: {str(e)}")
#             # Extract skills dynamically from resume text using contextual patterns
#             extracted_skills = []
            
#             # Look for skill sections
#             skill_sections = re.findall(r'(?i)(?:skills|technologies|competencies|proficiencies|tools)(?:[^\n.]*):([^\n]+(?:\n[^\n•*]+)*)', resume_text)
            
#             for section in skill_sections:
#                 # Extract individual skills by splitting on common delimiters
#                 skills = re.findall(r'(?:[\s,;:|•]+)([A-Za-z0-9+#/\-._& ]{2,30}?)(?:[\s,;:|•]|$)', section)
#                 extracted_skills.extend([s.strip() for s in skills if len(s.strip()) > 2])
            
#             # Extract programming languages and technologies 
#             tech_pattern = r'\b(?:Python|Java|JavaScript|C\+\+|SQL|HTML|CSS|AWS|Azure|Docker|Kubernetes|Git|React|Angular|Vue|Node\.js|PHP|Ruby|Swift|Go|Rust|MongoDB|MySQL|PostgreSQL|TensorFlow|PyTorch|Pandas|NumPy)\b'
#             tech_skills = re.findall(tech_pattern, resume_text)
#             extracted_skills.extend(tech_skills)
            
#             # Remove duplicates while preserving order
#             seen = set()
#             unique_skills = [skill for skill in extracted_skills if not (skill in seen or seen.add(skill))]
            
#             return unique_skills
    
#     def identify_missing_skills(self, current_skills, target_role):
#         """
#         Dynamically identify missing skills for a target role without using hardcoded lists.
        
#         Args:
#             current_skills (list): List of current skills from resume
#             target_role (str): Target role for career transition
            
#         Returns:
#             list: Missing skills needed for the target role
#         """
#         prompt = (
#             f"You are a career coach with expertise in the {target_role} field in 2025. "
#             f"Given the candidate's current skills: {', '.join(current_skills)}, "
#             f"identify the specific top skills that are MISSING to be successful as a {target_role} in 2025. "
#             f"Focus on the most important skills that would have the highest impact on their career transition. "
#             f"Consider technical skills, tools, frameworks, and domain knowledge essential for this role. "
#             f"Return ONLY a JSON array of the missing skills, with no additional text or explanation. "
#             f"Include 5-10 specific, actionable skills that they need to learn."
#         )
        
#         try:
#             response = self.get_llm_response(prompt)
            
#             # Extract JSON list from response
#             import re
#             json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            
#             if json_match:
#                 skills_json = f"[{json_match.group(1)}]"
#                 missing_skills = json.loads(skills_json)
#                 return missing_skills
#             else:
#                 # Fallback extraction if JSON parsing fails
#                 missing_skills = []
#                 lines = response.split('\n')
#                 for line in lines:
#                     # Look for skills in bullet points, numbered lists, or plain text
#                     if re.search(r'^[-•*\d.)\s]*([A-Za-z0-9+#/\-._& ]{2,30})', line):
#                         skill = re.sub(r'^[-•*\d.)\s]*', '', line).strip()
#                         if skill and not any(s in skill.lower() for s in ['following', 'missing', 'skills', 'learn']):
#                             missing_skills.append(skill)
                
#                 # Return unique skills
#                 return list(set(missing_skills))
        
#         except Exception as e:
#             logger.error(f"❌ Error identifying missing skills: {str(e)}")
#             # Generate a basic set of skills based on the target role name
#             role_words = target_role.lower().split()
            
#             # Create contextual missing skills based on role name
#             missing_skills = []
            
#             if any(word in role_words for word in ['data', 'scientist', 'analyst']):
#                 missing_skills = ["Statistical Analysis", "Data Visualization", "Machine Learning"]
#             elif any(word in role_words for word in ['software', 'developer', 'engineer']):
#                 missing_skills = ["System Design", "Code Optimization", "Testing Frameworks"]
#             elif any(word in role_words for word in ['embedded', 'hardware']):
#                 missing_skills = ["Microcontroller Programming", "Firmware Development", "Real-time Systems"]
#             else:
#                 missing_skills = ["Advanced Problem Solving", "Industry Knowledge", "Technical Communication"]
                
#             return missing_skills
    
#     def generate_career_advice(self, current_skills, target_role, missing_skills=None):
#         """
#         Generate personalized career advice for transitioning to a target role.
        
#         Args:
#             current_skills (list): List of current skills from resume
#             target_role (str): Target role for career transition
#             missing_skills (list, optional): List of missing skills if already identified
            
#         Returns:
#             str: Career advice in markdown format
#         """
#         # If missing skills not provided, identify them
#         if not missing_skills:
#             missing_skills = self.identify_missing_skills(current_skills, target_role)
        
#         prompt = (
#             f"You are a career coach helping someone transition to a {target_role} role. "
#             f"Their current skills are: {', '.join(current_skills[:10])}. "
#             f"They need to develop these skills: {', '.join(missing_skills)}. "
#             "Provide detailed, personalized advice with the following sections:\n"
#             "1. Skills Assessment: Evaluate their current skills relevant to the target role\n"
#             "2. Skills Gap: Explain the importance of the missing skills for this role\n"
#             "3. Learning Path: Recommend specific courses, resources, or training\n"
#             "4. Project Ideas: Suggest portfolio projects to demonstrate new skills\n"
#             "5. Networking: Tips for connecting with professionals in the target field\n\n"
#             "Format your response in Markdown with clear headings and bullet points."
#         )
        
#         try:
#             return self.get_llm_response(prompt)
#         except Exception as e:
#             logger.error(f"❌ Error generating career advice: {str(e)}")
            
#             # Fallback template
#             return (
#                 f"# Career Transition Plan: {target_role}\n\n"
#                 f"## Skills Assessment\n"
#                 f"You have some valuable skills that can help in your transition: {', '.join(current_skills[:5])}\n\n"
#                 f"## Skills Gap\n"
#                 f"You should focus on developing: {', '.join(missing_skills)}\n\n"
#                 f"## Recommended Next Steps\n"
#                 f"1. Consider taking courses on {', '.join(missing_skills[:3])}\n"
#                 f"2. Build a portfolio of projects showing your abilities\n"
#                 f"3. Network with professionals in this field\n"
#                 f"4. Update your resume to highlight relevant experience\n"
#             )
    
#     def answer_career_question(self, question, user_context):
#         """
#         Answer a follow-up career question using LLM.
        
#         Args:
#             question (str): The user's question
#             user_context (dict): Context about the user, including skills and target role
            
#         Returns:
#             str: Response to the question
#         """
#         context = (
#             f"You are a career coach helping someone transition to a {user_context.get('target_role')} role. "
#             f"Their current skills include: {', '.join(user_context.get('skills', [])[:7])}. "
#             "Provide helpful, specific advice based on this context."
#         )
        
#         try:
#             return self.get_llm_response(question, context=context)
#         except Exception as e:
#             logger.error(f"❌ Error answering career question: {str(e)}")
            
#             # Fallback response
#             return (
#                 f"That's a great question about transitioning to a {user_context.get('target_role')} role. "
#                 f"Based on your background, I recommend focusing on developing relevant technical skills, "
#                 f"building a portfolio of projects, and networking with professionals in the field. "
#                 f"This combination of skill development and professional connections will maximize your "
#                 f"chances of a successful transition."
#             )





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
     # Instruction to restrict scope
    SYSTEM_INSTRUCTION = (
        "You are an assistant confined to the provided conversation history. "
        "Only answer questions directly related to this career-transition-path or learning-path context. "
        "If a user asks anything outside this scope, respond with: "
        "I'm sorry, but I can only answer questions about your personalized learning path based on the conversation history."
    )
    # Hardcoded conversation history
    CONVERSATION_HISTORY = []
    # CONVERSATION_HISTORY = [
    #     {"role": "assistant", "content": "👋 Hello! I'll help you create a personalized learning path. What's your name?"},
    #     {"role": "user", "content": "Ram"},
    #     {"role": "assistant", "content": "Nice to meet you, Ram! What career would you like to pursue? (e.g., Data Engineer, Data Scientist, Software Engineer)"},
    #     {"role": "user", "content": "Data Scientist"},
    #     {"role": "assistant", "content": "Great! For a **Data Scientist** role, these are the top skills you'll need:\n\n- Python\n- SQL\n- Machine Learning\n- Cloud Computing\n- Data Visualization\n\nLet's assess your current skill level in each area."},
    #     {"role": "assistant", "content": "How would you rate your proficiency in **Python** on a scale of 1-5?\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert"},
    #     {"role": "user", "content": "3"},
    #     {"role": "assistant", "content": "How would you rate your proficiency in **SQL** on a scale of 1-5?\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert"},
    #     {"role": "user", "content": "3"},
    #     {"role": "assistant", "content": "How would you rate your proficiency in **Machine Learning** on a scale of 1-5?\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert"},
    #     {"role": "user", "content": "1"},
    #     {"role": "assistant", "content": "How would you rate your proficiency in **Cloud Computing** on a scale of 1-5?\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert"},
    #     {"role": "user", "content": "2"},
    #     {"role": "assistant", "content": "How would you rate your proficiency in **Data Visualization** on a scale of 1-5?\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert"},
    #     {"role": "user", "content": "4"},
    #     {"role": "assistant", "content": "Thanks for the ratings! Now generating your personalized learning path..."},
    #     {"role": "assistant", "content": "### Your Current Skills Assessment\n\n- **Python**: ★★★☆☆ (3/5)\n- **SQL**: ★★★☆☆ (3/5)\n- **Machine Learning**: ★☆☆☆☆ (1/5)\n- **Cloud Computing**: ★★☆☆☆ (2/5)\n- **Data Visualization**: ★★★★☆ (4/5)\n"},
    #     {"role": "assistant", "content": "# 🚀 Your Personalized Data Engineering Learning Path\n\nBased on your current skill assessment, I've curated courses that will help you advance your career as a **Data Scientist**. These recommendations focus on strengthening your skills in:\n\n- **Python** ⭐⭐ (Focus area)\n- **SQL** ⭐⭐ (Focus area)\n- **Machine Learning** ⭐ (Prioritize)\n- **Cloud Computing** ⭐ (Prioritize)\n\nThe learning path is organized from beginner to advanced courses, designed for completion within 6 months. Each course is chosen to address specific skill gaps and help you build a comprehensive foundation in data engineering.\n"},
    #     {"role": "assistant", "content": "# Data Engineer Learning Path\n\n1. **Intro to Data Science: Your Step-by-Step Guide To Starting** (Udemy - Beginner)\n   - *What you'll learn*: Entire Data Science process, Cloud concepts, Database fundamentals\n   - *Skills*: Data Science, Cloud Computing, Databases\n   - [Enroll](https://www.udemy.com/course/intro-to-data-science/)\n2. **Complete Python for data science and cloud computing** (Udemy - All Levels)\n   - *What you'll learn*: Predictive modeling, ML algorithms, result presentation\n   - *Skills*: Python, Machine Learning, Cloud Computing, Data Analysis\n   - [Enroll](https://www.udemy.com/course/complete-python-for-data-science-and-cloud-computing/)\n3. **Data Science Beginner's Course 2020** (Udemy - All Levels)\n   - *What you'll learn*: Basics to advanced methods, step-by-step instruction\n   - *Skills*: Data Analysis, Statistics, Programming, Visualization\n   - [Enroll](https://www.udemy.com/course/complete-data-science-course-go-from-zero-to-hero-a/)\n4. **Data Science 2022: Complete Data Science & Machine Learning** (Udemy - All Levels)\n   - *What you'll learn*: Advanced concepts in Python, Linear Algebra, ML math\n   - *Skills*: Python, ML theory, Calculus, Vectors, Matrices\n   - [Enroll](https://www.udemy.com/course/complete-data-science-and-machine-learning-using-python/)\n5. **The Data Science Course 2022: Complete Data Science Bootcamp** (Udemy - All Levels)\n   - *What you'll learn*: Stats analysis, Python libraries, ML & deep learning, Tableau\n   - *Skills*: NumPy, pandas, matplotlib, scikit-learn, TensorFlow\n   - [Enroll](https://www.udemy.com/course/the-data-science-course-complete-data-science-bootcamp/)\n6. **Most Effective Tips to Get Your Dream Data Science Job** (Udemy - All Levels)\n   - *What you'll learn*: Job market skillset, portfolio tips, career strategies\n   - *Skills*: Python, R, SQL, Visualization, Big Data, Data Mining\n   - [Enroll](https://www.udemy.com/course/most-effective-tips-to-get-your-dream-data-science-job/)\n"},
    #     {"role": "assistant", "content": "# 💼 Next Steps After Completing Your Learning Path\n\nOnce you've completed these courses, consider:\n1. **Building a portfolio**: 2-3 projects with cloud data pipelines and big data tech.\n2. **Certifications**: Google Cloud Professional Data Engineer, AWS Data Analytics Specialty.\n3. **Community**: Engage on Stack Overflow, Reddit's r/dataengineering, Meetup groups.\n4. **Open source**: Contribute to data engineering repos for visibility.\n\nAny questions about your learning path or next steps?"}
    # ]

    def __init__(self):
        self.conn = None
        self._connect()

    def _connect(self, retry_count=0):
        try:
            if self.conn:
                self.conn.close()
        except:
            pass
        self.conn = get_snowflake_connection()
        logger.info("Connected to Snowflake for Chat Service")

    @contextmanager
    def get_cursor(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def _ensure_connection(self):
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
        except:
            self._connect()

    def _sanitize(self, text: str) -> str:
        return (text or "").replace("'", "''")

    def get_llm_response(self, prompt: str, context: str = None):
        self._ensure_connection()
        full = prompt
        if context:
            ctx = self._sanitize(context)
            full = f"{ctx}\n\n{prompt}"

        for model in ['llama3.1-70b','llama3.1-8b','snowflake-llama-3.1-405b']:
            try:
                with self.get_cursor() as cur:
                    query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', $${full}$$) AS response;"
                    cur.execute(query)
                    resp = cur.fetchone()[0]
                    if resp and resp.strip():
                        return True, resp
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
        return False, "Sorry, I'm having trouble generating a response right now."

    def _build_prompt(self, question: str) -> str:
        # Insert system instruction first
        prompt_lines = [f"system: {self.SYSTEM_INSTRUCTION}"]
        # Add conversation history
        for m in self.CONVERSATION_HISTORY:
            line = m['content'].replace("\n", " ")
            prompt_lines.append(f"{m['role']}: {line}")
        # Append user question
        prompt_lines.append(f"user: {question}")
        prompt_lines.append("assistant:")
        return "\n".join(prompt_lines)

    def answer_career_question(self, question: str, user_context=None):
        self.CONVERSATION_HISTORY = user_context.get('chat_history', [])
        prompt = self._build_prompt(question)
        return self.get_llm_response(prompt)
    
    def generate_career_advice(self, current_skills, target_role, missing_skills=None):
        """
        Generate personalized career advice for transitioning to a target role.
        
        Args:
            current_skills (list): List of current skills from resume
            target_role (str): Target role for career transition
            missing_skills (list, optional): List of missing skills if already identified
            
        Returns:
            str: Career advice in markdown format
        """
        # If missing skills not provided, identify them
        if not missing_skills:
            missing_skills = self.identify_missing_skills(current_skills, target_role)
        
        prompt = (
            f"You are a career coach helping someone transition to a {target_role} role. "
            f"Their current skills are: {', '.join(current_skills[:10])}. "
            f"They need to develop these skills: {', '.join(missing_skills)}. "
            "Provide detailed, personalized advice with the following sections:\n"
            "1. Skills Assessment: Evaluate their current skills relevant to the target role\n"
            "2. Skills Gap: Explain the importance of the missing skills for this role\n"
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
                f"## Skills Gap\n"
                f"You should focus on developing: {', '.join(missing_skills)}\n\n"
                f"## Recommended Next Steps\n"
                f"1. Consider taking courses on {', '.join(missing_skills[:3])}\n"
                f"2. Build a portfolio of projects showing your abilities\n"
                f"3. Network with professionals in this field\n"
                f"4. Update your resume to highlight relevant experience\n"
            )
        
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
            "Be comprehensive and include all identifiable skills. "
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
            # Extract skills dynamically from resume text using contextual patterns
            extracted_skills = []
            
            # Look for skill sections
            skill_sections = re.findall(r'(?i)(?:skills|technologies|competencies|proficiencies|tools)(?:[^\n.]*):([^\n]+(?:\n[^\n•*]+)*)', resume_text)
            
            for section in skill_sections:
                # Extract individual skills by splitting on common delimiters
                skills = re.findall(r'(?:[\s,;:|•]+)([A-Za-z0-9+#/\-._& ]{2,30}?)(?:[\s,;:|•]|$)', section)
                extracted_skills.extend([s.strip() for s in skills if len(s.strip()) > 2])
            
            # Extract programming languages and technologies 
            tech_pattern = r'\b(?:Python|Java|JavaScript|C\+\+|SQL|HTML|CSS|AWS|Azure|Docker|Kubernetes|Git|React|Angular|Vue|Node\.js|PHP|Ruby|Swift|Go|Rust|MongoDB|MySQL|PostgreSQL|TensorFlow|PyTorch|Pandas|NumPy)\b'
            tech_skills = re.findall(tech_pattern, resume_text)
            extracted_skills.extend(tech_skills)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_skills = [skill for skill in extracted_skills if not (skill in seen or seen.add(skill))]
            
            return unique_skills