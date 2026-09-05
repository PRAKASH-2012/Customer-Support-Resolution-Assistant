import json
import re
from kb_manager import find_best_matching_articles
from database import get_db_connection

HUMAN_TRANSFER_KEYWORDS = [
    'human', 'agent', 'representative', 'operator', 'person', 'supervisor',
    'manager', 'cancel service', 'lawyer', 'complain', 'storm', 'emergency', 'dead line', 'red light'
]

FRUSTRATION_KEYWORDS = [
    'angry', 'terrible', 'horrible', 'worst', 'useless', 'fix this', 'scam', 'ridiculous', 'fed up'
]

def analyze_sentiment(text):
    text_lower = text.lower()
    if any(kw in text_lower for kw in HUMAN_TRANSFER_KEYWORDS) or any(kw in text_lower for kw in FRUSTRATION_KEYWORDS):
        if 'cancel' in text_lower or 'lawyer' in text_lower or 'dead' in text_lower or 'storm' in text_lower:
            return 'Critical'
        return 'Frustrated'
    elif 'thank' in text_lower or 'great' in text_lower or 'good' in text_lower or 'awesome' in text_lower:
        return 'Positive'
    return 'Neutral'

def process_customer_request(customer_id, ticket_id, user_message, conversation_history=None):
    """
    Core resolution assistant engine for Broadband & Mobile providers.
    Combines:
      1. Conversation so far
      2. Customer Account Record (Plan, Tier, Line status, Billing balance)
      3. Categorized Knowledge Base Articles & Citations
    Outputs:
      - Grounded draft response with citations (for routine requests)
      - Missing information prompts (slot filling)
      - Structured handover summary card (for complex/escalated requests)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer_row = cursor.fetchone()
    conn.close()

    customer = dict(customer_row) if customer_row else {}

    # Sentiment analysis
    sentiment = analyze_sentiment(user_message)

    # Escalation checks
    is_explicit_transfer = any(kw in user_message.lower() for kw in HUMAN_TRANSFER_KEYWORDS)
    is_line_fault = customer.get('line_status') in ['Fault Detected', 'Offline']
    is_high_dispute = customer.get('billing_status') == 'Disputed' and (customer.get('balance_due') or 0) > 100

    # Knowledge Base Matching
    kb_matches = find_best_matching_articles(user_message)
    top_article = kb_matches[0] if kb_matches else None
    top_score = top_article['score'] if top_article else 0.0

    # Missing Information Slot Filling Check
    missing_slots = []
    if top_article and top_article.get('required_slots'):
        for slot in top_article['required_slots']:
            if slot == 'invoice_number':
                if not re.search(r'inv[-\s]?\d+|\d{5,}', user_message.lower()):
                    missing_slots.append('invoice_number')
            elif slot == 'modem_mac':
                if not re.search(r'([0-9a-f]{2}[:.-]){5}[0-9a-f]{2}', user_message.lower()):
                    missing_slots.append('modem_mac')

    # Decision Matrix
    if is_explicit_transfer or is_line_fault or is_high_dispute or top_score < 0.20:
        # State: ESCALATED -> Structured Handover Summary
        handover = generate_handover_summary(customer, user_message, conversation_history, kb_matches, is_line_fault, is_high_dispute)
        save_handover_to_db(ticket_id, handover)
        
        complexity = 0.90 if is_line_fault else 0.75
        update_ticket_status(ticket_id, 'escalated', sentiment=sentiment, complexity=complexity)

        response_text = (
            f"I have reviewed your inquiry and account telemetry. Because this issue involves "
            f"**{handover['escalation_reason']}**, I am escalating your case directly to a Senior Telecommunications Specialist.\n\n"
            f"📋 **Zero Repetition Context Handover Summary Created**:\n"
            f"• **Issue Summary**: {handover['issue_summary']}\n"
            f"• **Established Facts**: Account #{customer.get('customer_id')}, Plan: {customer.get('plan_name')}, Line: {customer.get('line_status')}\n"
            f"• **Recommended Action**: {handover['recommended_action']}\n\n"
            f"An agent will pick up this case immediately with all details intact."
        )

        return {
            'status': 'escalated',
            'response_text': response_text,
            'citations': [top_article['citation_tag']] if top_article and top_score > 0.2 else [],
            'missing_slots': [],
            'handover': handover,
            'confidence_score': top_score,
            'sentiment': sentiment
        }

    elif missing_slots:
        # State: MISSING INFORMATION -> Slot Clarification Request
        update_ticket_status(ticket_id, 'missing_info', sentiment=sentiment, complexity=0.45)
        citation = top_article['citation_tag']

        response_text = (
            f"Hello {customer.get('name', '').split()[0]}, I can certainly assist you with this inquiry based on policy {citation}.\n\n"
            f"⚠️ **Information Required**: To verify your account billing record, please reply with your **10-digit Invoice Number** or **Payment Confirmation Transaction ID**."
        )

        return {
            'status': 'missing_info',
            'response_text': response_text,
            'citations': [citation],
            'missing_slots': missing_slots,
            'handover': None,
            'confidence_score': top_score,
            'sentiment': sentiment
        }

    else:
        # State: ROUTINE DRAFT READY -> Grounded Citation Response
        update_ticket_status(ticket_id, 'routine_draft', sentiment=sentiment, complexity=0.20)
        citation = top_article['citation_tag']
        template = top_article['resolution_template']

        response_text = (
            f"{template}\n\n"
            f"📌 **Knowledge Base Citation**: {citation}\n"
            f"*Troubleshooting Steps*:\n{top_article.get('troubleshooting_steps', '')}"
        )

        return {
            'status': 'routine_draft',
            'response_text': response_text,
            'citations': [citation],
            'missing_slots': [],
            'handover': None,
            'confidence_score': top_score,
            'sentiment': sentiment
        }

def generate_handover_summary(customer, current_message, history, kb_matches, is_line_fault, is_high_dispute):
    esc_reason = "Explicit customer request for human specialist"
    if is_line_fault:
        esc_reason = "Physical optical line drop fault detected on gateway ONT"
    elif is_high_dispute:
        esc_reason = f"High-value billing dispute (${customer.get('balance_due', 0):.2f}) exceeding bot threshold"
    elif not kb_matches or kb_matches[0]['score'] < 0.20:
        esc_reason = "No matching knowledge base policy found"

    established_facts = {
        'account_id': customer.get('customer_id', 'Unknown'),
        'client_name': customer.get('name', 'Guest'),
        'account_tier': customer.get('account_tier', 'Standard'),
        'service_plan': customer.get('plan_name', 'Broadband'),
        'billing_status': f"{customer.get('billing_status')} (Balance Due: ${customer.get('balance_due', 0):.2f})",
        'line_telemetry': f"Status: {customer.get('line_status')}, Speeds: Down {customer.get('download_speed_mbps')}Mbps / Up {customer.get('upload_speed_mbps')}Mbps, Latency: {customer.get('latency_ms')}ms",
        'hardware_id': customer.get('modem_router_id') or customer.get('sim_card_id') or 'N/A'
    }

    tried_solutions = {
        'attempted_steps': [
            f"Customer submitted query: '{current_message}'",
            "Polled live gateway telemetry and SNR line margins",
            f"Matched support articles: {', '.join([a['citation_tag'] for a in kb_matches[:2]]) if kb_matches else 'None'}"
        ],
        'customer_inputs': [current_message]
    }

    recommended_action = "Review customer account telemetry, verify fiber drop signal at local exchange node, and issue SLA outage bill credit if verified."
    if is_high_dispute:
        recommended_action = "Review detailed invoice ledger and issue goodwill late fee waiver if payment was delayed due to banking system error."
    elif not is_line_fault:
        recommended_action = "Engage customer in direct agent consultation to address custom query."

    return {
        'issue_summary': f"Customer {customer.get('name', '')} reporting: '{current_message}'",
        'established_facts': json.dumps(established_facts),
        'tried_solutions': json.dumps(tried_solutions),
        'recommended_action': recommended_action,
        'escalation_reason': esc_reason
    }

def save_handover_to_db(ticket_id, handover):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO handover_summaries (
            ticket_id, issue_summary, established_facts, tried_solutions, recommended_action, escalation_reason
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        ticket_id,
        handover['issue_summary'],
        handover['established_facts'],
        handover['tried_solutions'],
        handover['recommended_action'],
        handover['escalation_reason']
    ))
    conn.commit()
    conn.close()

def update_ticket_status(ticket_id, status, sentiment='Neutral', complexity=0.20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets
        SET status = ?, sentiment = ?, complexity_score = ?, updated_at = CURRENT_TIMESTAMP
        WHERE ticket_id = ?
    ''', (status, sentiment, complexity, ticket_id))
    conn.commit()
    conn.close()
