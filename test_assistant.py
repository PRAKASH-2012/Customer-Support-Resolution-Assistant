import unittest
import json
import os
from database import init_db, get_db_connection
from kb_manager import find_best_matching_articles, get_article_by_id
from resolution_engine import process_customer_request, generate_handover_summary
from app import app

class TestResolutionAssistant(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_01_routine_request_grounded_citation(self):
        """Test routine WiFi password inquiry returns grounded resolution with citation tag."""
        res = process_customer_request('CUST-1001', 'TCK-TEST-01', 'How can I change my WiFi password on my modem?')
        self.assertEqual(res['status'], 'routine_draft')
        self.assertIn('[KB-102: WiFi & SSID Configuration]', res['citations'])
        self.assertIn('http://192.168.1.1', res['response_text'])

    def test_02_missing_information_slot_filling(self):
        """Test billing inquiry missing invoice details prompts for missing invoice_number slot."""
        res = process_customer_request('CUST-1002', 'TCK-TEST-02', 'I want to dispute an extra fee on my recent bill!')
        self.assertEqual(res['status'], 'missing_info')
        self.assertIn('invoice_number', res['missing_slots'])
        self.assertIn('Invoice Number', res['response_text'])

    def test_03_complex_issue_handover_generation(self):
        """Test complex physical fiber failure generates structured handover card for human agent."""
        res = process_customer_request('CUST-1003', 'TCK-8803', 'Our fiber modem light is RED and internet is down completely after the thunderstorm!')
        self.assertEqual(res['status'], 'escalated')
        self.assertIsNotNone(res['handover'])
        self.assertIn('issue_summary', res['handover'])
        self.assertIn('established_facts', res['handover'])
        self.assertIn('tried_solutions', res['handover'])
        self.assertIn('recommended_action', res['handover'])

    def test_04_api_ticket_retrieval_and_approval(self):
        """Test REST endpoints for fetching tickets and approving drafts."""
        # Fetch ticket detail
        response = self.client.get('/api/tickets/TCK-8801')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['ticket']['customer_name'], 'Sarah Jenkins')

        # Approve draft
        approve_resp = self.client.post('/api/tickets/TCK-8801/approve')
        self.assertEqual(approve_resp.status_code, 200)
        approve_data = approve_resp.get_json()
        self.assertTrue(approve_data['success'])

    def test_05_line_diagnostics_telemetry(self):
        """Test automated telemetry line test endpoint."""
        resp = self.client.post('/api/diagnostics/run', json={'customer_id': 'CUST-1001'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['diagnostics']['line_status'], 'Online')
        self.assertGreater(data['diagnostics']['download_mbps'], 500)

if __name__ == '__main__':
    unittest.main()
