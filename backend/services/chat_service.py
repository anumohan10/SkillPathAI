# Create a new file: backend/services/chat_service.py

import json
import logging
import re
from datetime import datetime
from contextlib import contextmanager
from backend.database import get_snowflake_connection
from backend.services.connection_pool import ConnectionPool

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling LLM-powered chat interactions."""
    
    MAX_RETRIES = 3
    
    def __init__(self):
        """Initialize Snowflake connection for chat service."""
        self.conn = None
        self.pool = ConnectionPool()
        self._connect()
    
    def _connect(self, retry_count=0):
        """Establish connection to Snowflake with retry logic."""
        try:
            if self.conn:
                try:
                    # Release the connection back to the pool instead of closing
                    self.pool.release_connection(self.conn)
                except Exception:
                    pass

            # Get a connection from the pool
            self.conn = self.pool.get_connection()
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
            
    def __del__(self):
        """Properly release connection when the object is deleted."""
        if hasattr(self, 'conn') and self.conn:
            try:
                if hasattr(self, 'pool'):
                    self.pool.release_connection(self.conn)
                else:
                    self.conn.close()
            except Exception:
                pass
    
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
        # More specific prompt for comprehensive skill extraction
        prompt = (
            "You are an expert resume analyst in 2025 specializing in skill extraction. "
            "Extract ALL technical skills, programming languages, tools, platforms, frameworks, "
            "soft skills, and domain knowledge from the following resume text. "
            "Be VERY COMPREHENSIVE and thorough - identify EVERY POSSIBLE skill mentioned. "
            "Include both technical skills (like programming languages, tools, frameworks) "
            "AND soft skills (like leadership, communication, problem-solving). "
            "Return the result as a JSON list of strings containing ONLY the skill names. "
            "Do not miss any skills, be extremely thorough. Format as a JSON array ONLY with no explanations or text. "
            "\n\n"
            f"Resume text: {resume_text[:5000]}..."  # Include more text for better analysis
        )
        
        try:
            response = self.get_llm_response(prompt, max_retries=3)  # Increase retries for reliability
            
            # Extract JSON list from response 
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            
            if json_match:
                skills_json = f"[{json_match.group(1)}]"
                try:
                    skills = json.loads(skills_json)
                    if skills and len(skills) >= 5:  # Ensure we have a reasonable number of skills
                        return skills
                except:
                    pass  # If JSON parsing fails, fall through to backup methods
            
            # First backup: Extract skills line by line if JSON parsing fails
            skills = []
            for line in response.split('\n'):
                line = line.strip().strip('"-,')
                if line and not line.startswith('[') and not line.startswith(']'):
                    # Clean up any quotes or list formatting
                    cleaned_skill = re.sub(r'^[\s"\'•*-]*|[\s"\']*$', '', line)
                    if cleaned_skill and len(cleaned_skill) > 2:
                        skills.append(cleaned_skill)
            
            if skills and len(skills) >= 5:  # Ensure we have a reasonable number of skills
                return skills
            
            # Second attempt with a simpler prompt if the first failed
            simple_prompt = (
                "List ALL skills mentioned in this resume. "
                "Include technical skills, soft skills, and domain knowledge. "
                "Format as a simple bullet list with one skill per line. Be comprehensive. "
                f"\n\nResume: {resume_text[:5000]}..."
            )
            
            response = self.get_llm_response(simple_prompt, max_retries=2)
            skills = []
            
            # Process each line, looking for bullet points or numbered items
            for line in response.split('\n'):
                # Clean up bullet points and other formatting
                cleaned_line = re.sub(r'^[\s•\-*0-9.]+|\s*:.*$', '', line).strip()
                if cleaned_line and len(cleaned_line) > 2 and not cleaned_line.lower().startswith(('skill', 'here', 'these')):
                    skills.append(cleaned_line)
            
            if skills and len(skills) >= 5:
                return skills
                
        except Exception as e:
            logger.error(f"❌ Error extracting skills with LLM: {str(e)}")
        
        # Fallback: Extract skills from text using patterns
        extracted_skills = []
        
        # Look for skill sections with broader pattern matching
        skill_sections = re.findall(r'(?i)(?:skill|technolog|competenc|proficienc|tool|language|framework|platform)(?:[^\n.]*):([^\n]+(?:\n[^\n•*]+)*)', resume_text)
        
        for section in skill_sections:
            # Extract individual skills by splitting on common delimiters
            skills = re.findall(r'(?:[\s,;:|•]+)([A-Za-z0-9+#/\-._& ]{2,50}?)(?:[\s,;:|•]|$)', section)
            extracted_skills.extend([s.strip() for s in skills if len(s.strip()) > 2])
        
        # List of common technical skills to look for
        tech_skills = [
            # Programming languages
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 
            'Kotlin', 'Scala', 'R', 'MATLAB', 'Bash', 'Shell', 'SQL', 'PL/SQL', 'Assembly',
            
            # Web technologies
            'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Express.js', 'jQuery', 'Bootstrap',
            'REST API', 'GraphQL', 'JSON', 'XML', 'AJAX', 'WebSockets',
            
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'SQL Server', 'DynamoDB', 
            'Cassandra', 'Elasticsearch', 'Neo4j', 'Firebase',
            
            # Cloud & DevOps
            'AWS', 'Azure', 'Google Cloud', 'Kubernetes', 'Docker', 'Terraform', 'Jenkins', 'GitHub Actions',
            'CI/CD', 'Ansible', 'Puppet', 'Chef', 'Prometheus', 'Grafana', 'ELK Stack',
            
            # Data Science & ML
            'Machine Learning', 'TensorFlow', 'PyTorch', 'Keras', 'scikit-learn', 'Pandas', 'NumPy',
            'SciPy', 'Data Analysis', 'Data Visualization', 'Tableau', 'Power BI', 'Big Data',
            'Natural Language Processing', 'Computer Vision',
            
            # Version Control
            'Git', 'GitHub', 'GitLab', 'Bitbucket', 'Subversion',
            
            # Operating Systems
            'Linux', 'Windows', 'macOS', 'UNIX', 'iOS', 'Android',
            
            # Finance
            'Financial Analysis', 'Financial Modeling', 'Excel', 'Financial Statements', 'Accounting',
            'Budgeting', 'Forecasting', 'Risk Management', 'Bloomberg Terminal', 'Capital Markets',
            'Investment Banking', 'Corporate Finance', 'Financial Reporting', 'Valuation',
            
            # Soft Skills
            'Leadership', 'Communication', 'Team Management', 'Problem-Solving', 'Critical Thinking',
            'Project Management', 'Time Management', 'Collaboration', 'Adaptability', 'Analytical Thinking',
            'Creativity', 'Decision Making', 'Conflict Resolution', 'Negotiation', 'Customer Service',
            'Presentation', 'Research', 'Writing', 'Attention to Detail', 'Mentoring'
        ]
        
        # Create a pattern that matches any of these skills (with word boundaries)
        skills_pattern = r'\b(' + '|'.join(re.escape(skill) for skill in tech_skills) + r')\b'
        found_tech_skills = set(re.findall(skills_pattern, resume_text, re.IGNORECASE))
        
        # Add extracted skills with proper casing from the original list
        for skill in tech_skills:
            if skill.lower() in (s.lower() for s in found_tech_skills):
                extracted_skills.append(skill)
        
        # Add additional skills by looking for patterns in the text
        # Look for specialized formats like "X years of experience with Y" or "Proficient in Z"
        experience_patterns = [
            r'(?:[\d+]+ years?(?:[^.]*?)(?:experience|expertise) (?:in|with) )([A-Za-z0-9+#/\-._& ]{2,30})',
            r'(?:proficient in )([A-Za-z0-9+#/\-._& ]{2,30})',
            r'(?:expertise in )([A-Za-z0-9+#/\-._& ]{2,30})',
            r'(?:knowledge of )([A-Za-z0-9+#/\-._& ]{2,30})',
            r'(?:familiar with )([A-Za-z0-9+#/\-._& ]{2,30})',
            r'(?:experience (?:in|with) )([A-Za-z0-9+#/\-._& ]{2,30})',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            extracted_skills.extend([m.strip() for m in matches if len(m.strip()) > 2])
        
        # Extract skills that appear in sentence form in bullet points
        bullet_points = re.findall(r'(?:^|\n)[•\-*]\s*([^\n]+)', resume_text)
        for point in bullet_points:
            potential_skills = re.findall(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b', point)
            for skill in potential_skills:
                if len(skill) > 3 and not skill.lower() in ('and', 'the', 'with', 'for', 'this', 'that'):
                    extracted_skills.append(skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = [skill for skill in extracted_skills if not (skill.lower() in seen or seen.add(skill.lower()))]
        
        # Clean up skills - remove any that are just common words or filler text
        common_words = {'skills', 'experience', 'knowledge', 'years', 'proficient', 'expertise', 'with', 'and', 'the', 'for'}
        filtered_skills = [skill for skill in unique_skills if skill.lower() not in common_words and len(skill) > 2]
        
        return filtered_skills
    
    def identify_missing_skills(self, current_skills, target_role):
        """
        Dynamically identify missing skills for a target role without using hardcoded lists.
        
        Args:
            current_skills (list): List of current skills from resume
            target_role (str): Target role for career transition
            
        Returns:
            list: Missing skills needed for the target role
        """
        prompt = (
            f"You are a career coach with expertise in the {target_role} field in 2025. "
            f"Given the candidate's current skills: {', '.join(current_skills)}, "
            f"identify the specific top skills that are MISSING to be successful as a {target_role} in 2025. "
            f"Focus on the most important skills that would have the highest impact on their career transition. "
            f"Consider technical skills, tools, frameworks, and domain knowledge essential for this role. "
            f"Return ONLY a JSON array of the missing skills, with no additional text or explanation. "
            f"Include 5-10 specific, actionable skills that they need to learn."
        )
        
        try:
            response = self.get_llm_response(prompt)
            
            # Extract JSON list from response
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            
            if json_match:
                skills_json = f"[{json_match.group(1)}]"
                missing_skills = json.loads(skills_json)
                return missing_skills
            else:
                # Fallback extraction if JSON parsing fails
                missing_skills = []
                lines = response.split('\n')
                for line in lines:
                    # Look for skills in bullet points, numbered lists, or plain text
                    if re.search(r'^[-•*\d.)\s]*([A-Za-z0-9+#/\-._& ]{2,30})', line):
                        skill = re.sub(r'^[-•*\d.)\s]*', '', line).strip()
                        if skill and not any(s in skill.lower() for s in ['following', 'missing', 'skills', 'learn']):
                            missing_skills.append(skill)
                
                # Return unique skills
                return list(set(missing_skills))
        
        except Exception as e:
            logger.error(f"❌ Error identifying missing skills: {str(e)}")
            # Generate a basic set of skills based on the target role name
            role_words = target_role.lower().split()
            
            # Create contextual missing skills based on role name
            missing_skills = []
            
            if any(word in role_words for word in ['data', 'scientist', 'analyst']):
                missing_skills = ["Statistical Analysis", "Data Visualization", "Machine Learning"]
            elif any(word in role_words for word in ['finance', 'financial', 'analyst']):
                missing_skills = ["Financial Modeling", "Financial Analysis", "Excel", "Financial Statements", "Bloomberg Terminal"]
            elif any(word in role_words for word in ['software', 'developer', 'engineer']):
                missing_skills = ["System Design", "Code Optimization", "Testing Frameworks"]
            elif any(word in role_words for word in ['embedded', 'hardware']):
                missing_skills = ["Microcontroller Programming", "Firmware Development", "Real-time Systems"]
            else:
                missing_skills = ["Advanced Problem Solving", "Industry Knowledge", "Technical Communication"]
                
            return missing_skills
    
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