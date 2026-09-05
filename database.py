import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'support_desk.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Customer Accounts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service_type TEXT NOT NULL, -- Broadband, Mobile, Bundle
            plan_name TEXT NOT NULL,
            account_tier TEXT DEFAULT 'Standard', -- VIP, Standard, Business
            billing_status TEXT NOT NULL, -- Current, Overdue, Disputed
            balance_due REAL DEFAULT 0.0,
            payment_due_date TEXT,
            modem_router_id TEXT,
            line_status TEXT, -- Online, Degraded, Offline, Fault Detected
            download_speed_mbps REAL,
            upload_speed_mbps REAL,
            latency_ms INTEGER,
            sim_card_id TEXT,
            data_usage_gb REAL,
            data_limit_gb REAL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Knowledge Base Articles Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kb_articles (
            article_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL, -- Broadband, Billing, Mobile, Hardware, Roaming
            keywords TEXT NOT NULL, -- Comma separated
            content TEXT NOT NULL,
            troubleshooting_steps TEXT,
            resolution_template TEXT NOT NULL,
            citation_tag TEXT NOT NULL, -- e.g. [KB-101: Fiber Restart]
            required_slots TEXT -- JSON array of missing info keys, e.g. ["modem_mac", "error_code"]
        )
    ''')

    # Tickets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL, -- routine_draft, missing_info, escalated, resolved
            sentiment TEXT DEFAULT 'Neutral', -- Positive, Neutral, Frustrated, Critical
            complexity_score REAL DEFAULT 0.2, -- 0.0 to 1.0
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')

    # Ticket Messages Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            sender TEXT NOT NULL, -- customer, assistant, agent
            content TEXT NOT NULL,
            citations TEXT, -- JSON array of citations
            missing_slots_asked TEXT, -- JSON array of slots
            approved_by_agent INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
        )
    ''')

    # Structured Handover Summaries Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS handover_summaries (
            handover_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            issue_summary TEXT NOT NULL,
            established_facts TEXT NOT NULL, -- JSON string
            tried_solutions TEXT NOT NULL, -- JSON string
            recommended_action TEXT NOT NULL,
            escalation_reason TEXT NOT NULL,
            transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
        )
    ''')

    conn.commit()
    conn.close()
    seed_initial_data()

def seed_initial_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if customers already seeded
    cursor.execute("SELECT COUNT(*) as count FROM customers")
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return

    # Seed Customers
    customers = [
        (
            'CUST-1001', 'Sarah Jenkins', 'sarah.j@example.com', '+1-555-0143',
            'Broadband Fiber', 'Gigabit Ultra Fiber (1000Mbps)', 'VIP',
            'Current', 0.00, '2026-09-20', 'MODEM-FB-9921',
            'Online', 940.5, 880.2, 8, None, None, None,
            '452 Maple Ave, Suite 3B, Austin, TX'
        ),
        (
            'CUST-1002', 'Marcus Vance', 'marcus.v@example.com', '+1-555-0188',
            'Mobile 5G', 'Unlimited 5G Max Mobile', 'Standard',
            'Overdue', 64.50, '2026-08-28', None,
            'Degraded', None, None, None, 'SIM-5G-88102', 42.4, 50.0,
            '1208 Pine Ridge Rd, Austin, TX'
        ),
        (
            'CUST-1003', 'Elena Rostova', 'elena.biz@example.com', '+1-555-0199',
            'Bundle (Broadband + Mobile)', 'Business Connect Pro (500Mbps)', 'Business',
            'Disputed', 185.00, '2026-09-15', 'MODEM-BIZ-4412',
            'Fault Detected', 12.4, 1.1, 145, 'SIM-BIZ-0091', 110.0, 500.0,
            '88 Enterprise Way, Building A, Austin, TX'
        ),
        (
            'CUST-1004', 'David Kim', 'david.kim@example.com', '+1-555-0211',
            'Broadband Fiber', 'Home Starter Fiber (100Mbps)', 'Standard',
            'Current', 0.00, '2026-09-25', 'MODEM-HS-3310',
            'Online', 98.2, 95.0, 12, None, None, None,
            '304 Oak Street, Austin, TX'
        )
    ]

    cursor.executemany('''
        INSERT INTO customers (
            customer_id, name, email, phone, service_type, plan_name, account_tier,
            billing_status, balance_due, payment_due_date, modem_router_id,
            line_status, download_speed_mbps, upload_speed_mbps, latency_ms,
            sim_card_id, data_usage_gb, data_limit_gb, address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', customers)

    # Seed Support KB Articles
    kb_articles = [
        (
            'KB-101',
            'Fiber Modem Power Cycle & Red Optical Light Troubleshooting',
            'Broadband',
            'red light, optical, PON light, reboot modem, power cycle, no internet, fiber cable',
            'When the Optical or PON LED light on the fiber terminal (ONT) flashes RED or turns solid RED, it indicates a physical optical signal degradation or loss of fiber connectivity. Standard routine troubleshooting involves checking the green optical connector for tightness, ensuring the fiber patch cord is not bent at sharp angles (<90 degrees), and conducting a 60-second cold restart.',
            'Step 1: Inspect the white/green optical cable running into the ONT/Modem.\nStep 2: Unplug power adapter for 60 full seconds.\nStep 3: Plug back in and wait 3 minutes for optical alignment.\nStep 4: Check if Optical LED turns solid GREEN.',
            'Based on [KB-101: Fiber Modem Power Cycle], please verify that your fiber cable connector is securely fastened and perform a 60-second power cycle on your modem (unplug power cable, wait 60s, reconnect). If the Optical light remains solid red after 3 minutes, our diagnostics indicate a line signal issue requiring technician deployment.',
            '[KB-101: Fiber Optical Troubleshooting]',
            json.dumps([])
        ),
        (
            'KB-102',
            'WiFi Password Change and Router SSID Configuration',
            'Hardware',
            'wifi password, change password, ssid, router settings, admin login, 192.168.1.1',
            'Customers can customize their WiFi Network Name (SSID) and Password either via the ApexConnect Mobile App or through the local web portal at http://192.168.1.1. Default admin login credentials are printed on the barcode sticker located on the bottom of the gateway device.',
            'Step 1: Open ApexConnect App or go to http://192.168.1.1 in your browser.\nStep 2: Log in using the Admin Key printed under your router.\nStep 3: Navigate to Network Settings -> Wireless.\nStep 4: Update WPA2/WPA3 key and click Save Changes.',
            'According to [KB-102: WiFi Password Change], you can easily update your WiFi password in the ApexConnect App under My Router > Wireless Settings. Alternatively, connect to your router local portal at http://192.168.1.1 using the Admin Key printed on your router sticker.',
            '[KB-102: WiFi & SSID Configuration]',
            json.dumps([])
        ),
        (
            'KB-201',
            'Understanding Monthly Billing Statements, Pro-Rated Charges & Late Fees',
            'Billing',
            'bill higher, unusual charge, late fee, pro-rated, payment due, dispute bill, balance, invoice',
            'Monthly bills reflect plan recurring subscription, equipment rentals, and optional add-ons. If a customer upgrades or changes their plan mid-cycle, pro-rated charges appear on the subsequent billing cycle. Late payment fees of $15.00 are automatically assessed if balance is unpaid 5 days past due date.',
            'Step 1: Check bill breakdown for itemized charges.\nStep 2: Verify if any plan changes were activated during billing cycle.\nStep 3: Review transaction ID for recent payments.',
            'As outlined in [KB-201: Billing Statements & Pro-Rated Charges], mid-cycle plan adjustments or promotional expiration can cause temporary invoice variation. To investigate your specific balance, could you please provide your 10-digit Invoice Number or transaction date?',
            '[KB-201: Billing Policy & Invoices]',
            json.dumps(["invoice_number"])
        ),
        (
            'KB-301',
            '5G Mobile Data Throttle, APN Settings and Roaming Setup',
            'Mobile',
            'slow data, 5g slow, roaming, apn settings, international data, SIM card, data limit',
            'When mobile data usage exceeds high-speed data allocation (50GB for standard plans), speeds are throttled to 512Kbps until cycle refresh. For international roaming, data roaming must be enabled under Cellular Data Settings, and APN must be set to `apex.telecom.net`.',
            'Step 1: Check total data consumption in account app.\nStep 2: Ensure Data Roaming is turned ON in phone settings.\nStep 3: Verify Cellular Access Point Name (APN) is set to apex.telecom.net.',
            'Per [KB-301: 5G Mobile Data & APN Setup], if your data speed is reduced, check if you have reached your monthly high-speed limit (50GB). For international travel, make sure Data Roaming is ON and APN is set to apex.telecom.net.',
            '[KB-301: Mobile 5G & APN Settings]',
            json.dumps([])
        ),
        (
            'KB-401',
            'Broadband Service Outage Diagnostics and Maintenance',
            'Broadband',
            'outage, storm, service down, maintenance, emergency repair, local area down, node fault',
            'During severe weather or local fiber line cuts, regional outages occur. ApexConnect automated line monitoring polls local nodes every 5 minutes. If a node outage is identified, dispatch teams are deployed within 2 hours with an estimated resolution window of 3 to 6 hours.',
            'Step 1: Run line diagnostics query.\nStep 2: Match local node status.\nStep 3: Provide estimated repair arrival time to customer.',
            'Based on [KB-401: Outage Diagnostics], local infrastructure maintenance or line damage can affect fiber connectivity. Automated telemetry has logged a node alert in your area.',
            '[KB-401: Regional Network Maintenance]',
            json.dumps([])
        )
    ]

    cursor.executemany('''
        INSERT INTO kb_articles (
            article_id, title, category, keywords, content,
            troubleshooting_steps, resolution_template, citation_tag, required_slots
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', kb_articles)

    # Seed Initial Tickets & Messages
    # Ticket 1: Routine (Sarah Jenkins)
    cursor.execute('''
        INSERT INTO tickets (ticket_id, customer_id, subject, category, status, sentiment, complexity_score)
        VALUES ('TCK-8801', 'CUST-1001', 'How do I change my WiFi password?', 'Hardware', 'routine_draft', 'Positive', 0.15)
    ''')

    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender, content, citations, approved_by_agent)
        VALUES (
            'TCK-8801', 'customer', 'Hi, I got a new laptop and want to change my WiFi password to something easier to type. Where do I do that?', NULL, 0
        )
    ''')

    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender, content, citations, approved_by_agent)
        VALUES (
            'TCK-8801', 'assistant', 'Hello Sarah! According to [KB-102: WiFi & SSID Configuration], you can easily update your WiFi password using the ApexConnect Mobile App under My Router > Wireless Settings. Alternatively, navigate to http://192.168.1.1 in your browser and sign in using the Admin Key located on your gateway label.', '["[KB-102: WiFi & SSID Configuration]"]', 0
        )
    ''')

    # Ticket 2: Missing Info (Marcus Vance)
    cursor.execute('''
        INSERT INTO tickets (ticket_id, customer_id, subject, category, status, sentiment, complexity_score)
        VALUES ('TCK-8802', 'CUST-1002', 'Dispute on extra billing fee', 'Billing', 'missing_info', 'Frustrated', 0.45)
    ''')

    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender, content, citations, missing_slots_asked)
        VALUES (
            'TCK-8802', 'customer', 'I was charged an extra $15 late fee but I paid my bill! Fix this please.', NULL, NULL
        )
    ''')

    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender, content, citations, missing_slots_asked)
        VALUES (
            'TCK-8802', 'assistant', 'Hello Marcus, I can certainly assist with reviewing this late fee charge on your account. As outlined in [KB-201: Billing Policy & Invoices], to verify your payment timestamp, could you please provide your **Invoice Number** or your **Payment Confirmation Transaction ID**?', '["[KB-201: Billing Policy & Invoices]"]', '["invoice_number"]'
        )
    ''')

    # Ticket 3: Escalated / Handover (Elena Rostova)
    cursor.execute('''
        INSERT INTO tickets (ticket_id, customer_id, subject, category, status, sentiment, complexity_score)
        VALUES ('TCK-8803', 'CUST-1003', 'Fiber internet down completely after thunderstorm', 'Broadband', 'escalated', 'Critical', 0.85)
    ''')

    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender, content)
        VALUES (
            'TCK-8803', 'customer', 'Our business fiber internet has been completely dead since the storm last night. Modem light is flashing RED. We tried restarting 3 times. We are losing business operations!'
        )
    ''')

    cursor.execute('''
        INSERT INTO ticket_messages (ticket_id, sender, content, citations)
        VALUES (
            'TCK-8803', 'assistant', 'I am transferring your case immediately to a Senior Network Specialist. A detailed handover summary of your line status and attempted troubleshooting has been provided to the agent so you will not need to repeat anything.', '["[KB-101: Fiber Optical Troubleshooting]", "[KB-401: Regional Network Maintenance]"]'
        )
    ''')

    # Handover summary for TCK-8803
    cursor.execute('''
        INSERT INTO handover_summaries (
            ticket_id, issue_summary, established_facts, tried_solutions, recommended_action, escalation_reason
        ) VALUES (
            'TCK-8803',
            'Business fiber connection total outage following thunderstorm. Optical light on MODEM-BIZ-4412 is flashing RED.',
            '{"account_id": "CUST-1003", "client_name": "Elena Rostova", "plan": "Business Connect Pro (500Mbps)", "tier": "Business VIP", "billing_status": "Disputed ($185.00)", "line_telemetry": "Fault Detected - Download 12.4 Mbps / High Latency 145ms", "modem_id": "MODEM-BIZ-4412"}',
            '{"attempted_steps": ["Customer performed 3x manual power cycles on modem", "Assistant ran automated telemetry check which identified optical signal loss on fiber drop line"], "matched_kb": ["[KB-101: Fiber Optical Troubleshooting]", "[KB-401: Regional Network Maintenance]"]}',
            'Deploy Level-2 Field Dispatch team to inspect drop cable splice box at 88 Enterprise Way. Grant $50 service outage bill credit per SLA.',
            'Hardware optical failure & Business VIP SLA requirement'
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == '__main__':
    init_db()
