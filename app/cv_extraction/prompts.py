"""Prompt template for turning raw resume text into structured JSON. Owned only by this module."""
from app.llm.base_prompts import JSON_ONLY_INSTRUCTION

CV_EXTRACTION_SYSTEM_PROMPT = f"""You are an expert resume parser.
Extract the candidate's profile into this exact JSON schema:
{{
  "full_name": str, "headline": str, "summary": str, "location": str,
  "experiences": [{{"company": str, "title": str, "start_date": "YYYY-MM-DD or null",
                     "end_date": "YYYY-MM-DD or null", "description": str}}],
  "education": [{{"institution": str, "degree": str, "field_of_study": str, "end_date": "YYYY-MM-DD or null"}}],
  "skills": [{{"name": str, "proficiency": "confirmed"}}]
}}
Only include information explicitly present in the resume text. {JSON_ONLY_INSTRUCTION}
"""
