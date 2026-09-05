import json
import re
from database import get_db_connection

def find_best_matching_articles(query_text, category=None):
    """
    Search KB articles in SQLite database, score them using token frequency & keyword matching,
    and return ranked matching articles with match scores.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("SELECT * FROM kb_articles WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM kb_articles")

    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()

    query_tokens = set(re.findall(r'\w+', query_text.lower()))

    scored_articles = []
    for art in articles:
        kw_list = [k.strip().lower() for k in art['keywords'].split(',')]
        title_tokens = set(re.findall(r'\w+', art['title'].lower()))
        content_tokens = set(re.findall(r'\w+', art['content'].lower()))

        score = 0.0

        # Exact keyword matches count highest
        for kw in kw_list:
            if kw in query_text.lower():
                score += 0.35
            else:
                kw_sub_tokens = set(re.findall(r'\w+', kw))
                overlap = query_tokens.intersection(kw_sub_tokens)
                if overlap:
                    score += 0.15 * (len(overlap) / len(kw_sub_tokens))

        # Title token overlap
        title_overlap = query_tokens.intersection(title_tokens)
        if title_overlap:
            score += 0.25 * (len(title_overlap) / max(1, len(title_tokens)))

        # Content token overlap
        content_overlap = query_tokens.intersection(content_tokens)
        if content_overlap:
            score += 0.15 * (len(content_overlap) / max(1, len(query_tokens)))

        art['score'] = min(1.0, round(score, 2))
        art['required_slots'] = json.loads(art['required_slots']) if art['required_slots'] else []
        scored_articles.append(art)

    scored_articles.sort(key=lambda x: x['score'], reverse=True)
    return scored_articles

def get_article_by_id(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kb_articles WHERE article_id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        art = dict(row)
        art['required_slots'] = json.loads(art['required_slots']) if art['required_slots'] else []
        return art
    return None
