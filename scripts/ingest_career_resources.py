"""
Batch job for Phase 5: reads a list of source URLs and ingests them into the
career-resources vector store. Run manually or on a schedule (cron/Airflow later).
Run: python -m scripts.ingest_career_resources
"""
from app.career_rag.ingestion import ingest_url

SOURCES = [
    # --- Tech ---
    ("https://medium.com/@iammanolov98/mastering-sql-joins-coding-interview-preparation-innerjoin-e96bef58afc2", "sql-fundamentals"),
    ("https://designgurus.io/blog/system-design-interview-guide-for-beginners", "system-design"),
    ("https://www.datacamp.com/tutorial/docker-tutorial", "docker"),
    ("https://algocademy.com/blog/?p=609", "data-structures-algorithms"),
    ("https://www.techtarget.com/it-infrastructure/tip/16-REST-API-design-best-practices-and-guidelines", "api-design"),
    ("https://www.coursera.org/resources/data-analysis-interview-prep-guide", "data-analyst"),
    ("https://www.coursera.org/articles/product-manager-interview-questions", "product-management"),

    # --- General / cross-field ---
    ("https://guarinigrad.dartmouth.edu/resources/using-the-star-method-for-your-next-behavioral-interview/", "behavioral-interviews"),

    # --- Business ---
    ("https://www.coursera.org/gb/articles/marketing-interview-questions", "marketing"),
    ("https://www.intuit.com/blog/life-at-intuit/intuit-experts/accounting-job-interview-questions/", "finance-accounting"),
    ("https://www.michaelpage.co.uk/advice/career-advice/job-interview-tips/how-prepare-sales-job-interviews", "sales"),
    ("https://project-management.com/project-manager-interview-questions/", "project-management"),
    ("https://pagepersonnel.co.uk/our-expertise/human-resources/how-to-prepare-for-your-hr-interview", "human-resources"),
    ("https://rolecatcher.com/en/interviews/skills/knowledge/business-administration-and-law/business-and-administration/supply-chain-management/", "supply-chain-logistics"),
    ("https://www.roberthalf.com/au/en/insights/landing-job/administrative-assistant-interview-questions", "administrative-assistant"),

    # --- Healthcare & social services ---
    ("https://son.rochester.edu/career-planning/nursing-interview-questions.html", "nursing-healthcare"),
    ("https://online.yu.edu/wurzweiler/blog/social-work-job-interview-tips", "social-work-counseling"),

    # --- Education, design & service roles ---
    ("https://www.coursera.org/in/articles/teacher-interview-questions", "teaching-education"),
    ("https://design.careers360.com/articles/how-to-prepare-for-graphic-design-interviews", "graphic-design"),
    ("https://www.randstad.co.uk/career-advice/interview-tips/customer-service-job-interview-questions-tips/", "customer-service"),
    ("https://www.hcareers.com/article/career-advice/tips-for-nailing-each-phase-of-a-job-interview", "hospitality-retail"),

    # --- Legal ---
    ("https://www.clio.com/blog/paralegal-interview-questions/", "legal-paralegal"),
]


def main():
    for url, topic in SOURCES:
        count = ingest_url(url, topic)
        print(f"Ingested {count} chunks from {url} [{topic}]")


if __name__ == "__main__":
    main()
