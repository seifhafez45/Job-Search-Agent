"""
Batch job for Phase 5: reads a list of source URLs and ingests them into the
career-resources vector store. Run manually or on a schedule (cron/Airflow later).
Run: python -m scripts.ingest_career_resources
"""
from app.career_rag.ingestion import ingest_url

SOURCES = [
    # (url, topic_tag) — team fills this in with real course/doc URLs per target role
    # ("https://example.com/system-design-basics", "system-design"),
]


def main():
    for url, topic in SOURCES:
        count = ingest_url(url, topic)
        print(f"Ingested {count} chunks from {url} [{topic}]")


if __name__ == "__main__":
    main()
