import json
import uuid
import logging
import re
from datetime import datetime
from contextlib import contextmanager
from backend.database import get_snowflake_connection, create_resumes_table

logger = logging.getLogger(__name__)

class ResumeSearchService:
    MAX_RETRIES = 3

    def __init__(self):
        """Initialize the Snowflake connection and ensure the resumes table exists."""
        self.conn = None
        self._connect()
        self._initialize_search()

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
                logger.info("✅ Successfully connected to Snowflake")
            else:
                raise Exception("❌ Failed to connect to Snowflake")
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
        """Ensure the Snowflake connection is active before executing any query."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();")  # Check active DB
                db_info = cursor.fetchone()
                print(f"🔹 Connected to Snowflake DB: {db_info}")  # DEBUG Log
        except Exception:
            logger.info("🔄 Reconnecting to Snowflake...")
            self._connect()

    def _initialize_search(self):
        """Create the database and table for Cortex Search."""
        with self.get_cursor() as cursor:
            try:
                logger.info("🔄 Ensuring resumes table exists...")
                create_resumes_table()

                logger.info("🔄 Creating Cortex Search Service for resumes...")
                cursor.execute("""
                CREATE OR REPLACE CORTEX SEARCH SERVICE RESUME_SEARCH_SERVICE
                ON resume_text
                ATTRIBUTES user_name, target_role, extracted_skills
                WAREHOUSE = SKILLPATH_WH
                TARGET_LAG = '1 minute'
                AS (
                    SELECT 
                        resume_text,
                        user_name,
                        target_role,
                        extracted_skills
                    FROM resumes
                )
                """)
                self.conn.commit()
                logger.info("✅ Resume Search Service initialized successfully")
            except Exception as e:
                self.conn.rollback()
                logger.error(f"❌ Error initializing resume search: {e}")
                raise

    def clean_resume_text(self, resume_text: str):
        """Cleans resume text by removing personal details and unnecessary characters."""
        # Remove email addresses
        resume_text = re.sub(r'\S+@\S+', '', resume_text)
        # Remove phone numbers (formats like 123-456-7890, (123) 456-7890, 123 456 7890)
        resume_text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', resume_text)
        # Remove common address patterns
        resume_text = re.sub(r'\d{1,5}\s\w+(\s\w+)*,\s?\w+\s?\w*', '', resume_text)
        # Remove special characters except useful ones
        resume_text = re.sub(r'[^a-zA-Z0-9.,!?;:\'\-\s]', '', resume_text)
        # Normalize spaces
        resume_text = re.sub(r'\s+', ' ', resume_text).strip()
        return resume_text
    def _calculate_missing_skills(self, extracted_skills, target_role):
        """Calculate missing skills for a target role."""
        # Define required skills for common roles
        skill_requirements = {
        "Data Scientist": ["Python", "SQL", "Machine Learning", "Statistics", "Data Visualization"],
        "Software Engineer": ["Python", "Java", "JavaScript", "Git", "Docker"],
        "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js"],
        "Data Analyst": ["SQL", "Excel", "Data Visualization", "Python", "Statistics"],
        "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD"],
        "Product Manager": ["Agile", "User Research", "Strategy", "Communication"],
        "UX Designer": ["User Research", "Wireframing", "Prototyping", "UI Design"],
        "AI Engineer": ["Python", "TensorFlow", "PyTorch", "Machine Learning"]
    }
    
    # Get required skills for the target role (or empty list if not found)
        required_skills = skill_requirements.get(target_role, [])
    
    # Find missing skills
        missing_skills = [skill for skill in required_skills if skill not in extracted_skills]
    
        return missing_skills
    
    def store_resume(self, user_name: str, resume_text: str, extracted_skills: list, target_role: str):
        """Store resume details in the Snowflake table with proper array formatting."""
        self._ensure_connection()
        with self.get_cursor() as cursor:
            try:
                resume_id = str(uuid.uuid4())
                missing_skills = self._calculate_missing_skills(extracted_skills, target_role)
            
            # Format arrays properly for Snowflake
                extracted_skills_str = "ARRAY_CONSTRUCT(" + ", ".join([f"'{skill}'" for skill in extracted_skills]) + ")"
                missing_skills_str = "ARRAY_CONSTRUCT(" + ", ".join([f"'{skill}'" for skill in missing_skills]) + ")"
            
            # Clean resume text for SQL insertion (single quotes need to be escaped)
                cleaned_resume_text = resume_text.replace("'", "''")
            
                insert_query = f"""
            INSERT INTO SKILLPATH_DB.PUBLIC.RESUMES 
            (id, user_name, resume_text, extracted_skills, target_role, missing_skills)
            VALUES (
                '{resume_id}', 
                '{user_name}', 
                '{cleaned_resume_text}', 
                {extracted_skills_str}, 
                '{target_role}', 
                {missing_skills_str}
            )
            """
            
                cursor.execute(insert_query)
                self.conn.commit()
            
                logger.info(f"✅ Successfully stored resume for {user_name} in Snowflake.")
        
            except Exception as e:
                logger.error(f"❌ Error storing resume: {e}")
                raise

    def search_resumes(self, resume_text: str, target_role: str = None, limit: int = 5):
        """Search resumes using Cortex Search with cleaned text."""
        self._ensure_connection()
        with self.get_cursor() as cursor:
            try:
                cleaned_text = self.clean_resume_text(resume_text)
                filter_json = (
                    f', "filter": {{"@eq": {{"target_role": "{target_role}"}}}}' 
                    if target_role else ''
                )
                search_query = f"""
                SELECT PARSE_JSON(
                    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                        'RESUME_SEARCH_SERVICE',
                        '{{
                            "query": "{cleaned_text}",
                            "columns": ["resume_text", "user_name", "target_role", "extracted_skills"],
                            "limit": {limit}{filter_json}
                        }}'
                    )
                )['results'] as results;
                """
                cursor.execute(search_query)
                results = cursor.fetchone()[0]
                return results if results else []
            except Exception as e:
                logger.error(f"❌ Error searching resumes: {e}")
                return []

    def generate_career_path(self, search_results, target_role):
        """Use Snowflake Cortex LLMs to generate career transition recommendations."""
        self._ensure_connection()
        with self.get_cursor() as cursor:
            try:
            # Create a detailed prompt for the LLM
                completion_prompt = (
                f"You are a career transition coach helping someone move into a {target_role} role.\n\n"
                f"Based on their current skills: {json.dumps(search_results)},\n"
                f"Please provide a personalized learning path with:\n"
                f"1. Assessment of their current skills relevant to {target_role}\n"
                f"2. Key skills they need to develop\n"
                f"3. Recommended courses or learning resources\n"
                f"4. Suggested projects to demonstrate new skills\n"
                f"5. Timeline for transition (3-6 months)"
            )
            
            # Try available models in order of preference based on Snowflake documentation
                models = [
                'llama3.1-70b',  # Widely available in most regions
                'llama3.1-8b',   # Backup smaller model
                'snowflake-llama-3.1-405b'  # Try Snowflake's model if available
            ]
            
                for model in models:
                    try:
                        logger.info(f"🔄 Attempting to use model: {model}")
                    
                        query = f"""
                    SELECT SNOWFLAKE.CORTEX.COMPLETE(
                        '{model}',
                        '{completion_prompt}'
                    ) AS response;
                    """
                    
                        cursor.execute(query)
                        response = cursor.fetchone()[0]
                    
                        logger.info(f"✅ Successfully generated response with model: {model}")
                        return response
                    
                    except Exception as model_error:
                        logger.warning(f"❌ Error with model {model}: {str(model_error)}")
                        continue
            
            # If we get here, all models failed
                raise Exception("All available LLM models failed to generate a response")
            
            except Exception as e:
                logger.error(f"❌ Error generating career path with LLM: {str(e)}")
            
            # Return a fallback response instead of None for better UX
                fallback_response = (
                f"# Career Transition Plan: {target_role}\n\n"
                f"## Current Skills Assessment\n"
                f"Based on your resume, you have experience with: {', '.join(search_results)}\n\n"
                f"## Recommended Learning Path\n"
                f"1. Start with foundational courses in key technologies for {target_role}\n"
                f"2. Build 2-3 portfolio projects demonstrating these skills\n"
                f"3. Join professional communities related to this field\n"
                f"4. Update your resume to highlight transferable skills\n\n"
                f"## Timeline\n"
                f"With consistent effort, you could transition within 3-6 months."
             )
            
                return fallback_response