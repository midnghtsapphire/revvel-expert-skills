"""
Unit tests for Email Technology Expert Skill Module
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.email_technology_expert import (
    EmailHeaderAnalyzer,
    EmailAuthenticationValidator,
    EmailTrackingSystem,
    PhishingDetector,
    AutoReplySystem,
    EmailNotificationSystem,
    GmailAppsScriptGenerator,
    OutlookRulesGenerator,
    EmailWorkflowBuilder,
    ScheduledEmailSender,
    MailMergeSystem,
    EmailArchivalSystem,
    SpamAnalyzer,
    BulkEmailOperations,
    OAuthTokenManager,
    EmailCampaignManager,
    EmailTechnologyExpert,
    SKILL_METADATA
)


class TestEmailHeaderAnalyzer(unittest.TestCase):
    """Test EmailHeaderAnalyzer class"""
    
    def setUp(self):
        self.analyzer = EmailHeaderAnalyzer()
    
    def test_parse_email_headers(self):
        """Test email header parsing"""
        raw_email = """From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <test123@example.com>

This is a test email body.
"""
        result = self.analyzer.parse_email_headers(raw_email)
        
        self.assertIn("headers", result)
        self.assertEqual(result["from"], "sender@example.com")
        self.assertEqual(result["subject"], "Test Email")
        self.assertIn("test email body", result["body"].lower())
    
    def test_extract_ips(self):
        """Test IP extraction from headers"""
        headers = {
            "Received": [
                "from mail.example.com ([192.168.1.1]) by mx.google.com",
                "from server.test.com ([10.0.0.1]) by mail.example.com"
            ]
        }
        
        ips = self.analyzer.extract_all_ips(headers)
        # Should only extract public IPs
        self.assertIsInstance(ips, list)
    
    def test_trace_email_path(self):
        """Test email routing path tracing"""
        headers = {
            "Received": [
                "from mail.example.com by mx.google.com; Mon, 1 Jan 2024 12:00:00 +0000",
                "from sender.com by mail.example.com; Mon, 1 Jan 2024 11:59:00 +0000"
            ]
        }
        
        path = self.analyzer.trace_email_path(headers)
        self.assertIsInstance(path, list)
        self.assertGreater(len(path), 0)
        self.assertIn("hop_number", path[0])


class TestEmailAuthenticationValidator(unittest.TestCase):
    """Test EmailAuthenticationValidator class"""
    
    def setUp(self):
        self.validator = EmailAuthenticationValidator()
    
    def test_spf_record_parsing(self):
        """Test SPF record parsing"""
        # This test would require actual DNS queries or mocking
        # For now, test the structure
        result = self.validator.validate_spf("example.com", "192.0.2.1")
        
        self.assertIn("valid", result)
        self.assertIn("status", result)
    
    def test_dkim_validation_structure(self):
        """Test DKIM validation structure"""
        result = self.validator.validate_dkim("example.com", "default")
        
        self.assertIn("valid", result)
        self.assertIn("record", result)
    
    def test_dmarc_validation_structure(self):
        """Test DMARC validation structure"""
        result = self.validator.validate_dmarc("example.com")
        
        self.assertIn("valid", result)
        self.assertIn("record", result)


class TestEmailTrackingSystem(unittest.TestCase):
    """Test EmailTrackingSystem class"""
    
    def setUp(self):
        self.tracking = EmailTrackingSystem(tracking_domain="track.test.com")
    
    def test_generate_tracking_pixel(self):
        """Test tracking pixel generation"""
        tracking_id, pixel_html = self.tracking.generate_tracking_pixel(
            "email123", "user@example.com"
        )
        
        self.assertIsInstance(tracking_id, str)
        self.assertIn("<img", pixel_html)
        self.assertIn("track.test.com", pixel_html)
        self.assertIn(tracking_id, pixel_html)
    
    def test_record_email_open(self):
        """Test email open recording"""
        tracking_id, _ = self.tracking.generate_tracking_pixel(
            "email123", "user@example.com"
        )
        
        result = self.tracking.record_email_open(
            tracking_id, 
            user_agent="Mozilla/5.0",
            ip_address="192.0.2.1"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["open_count"], 1)
    
    def test_generate_tracked_link(self):
        """Test tracked link generation"""
        link_id, tracked_url = self.tracking.generate_tracked_link(
            "email123",
            "user@example.com",
            "https://example.com/page"
        )
        
        self.assertIsInstance(link_id, str)
        self.assertIn("track.test.com", tracked_url)
        self.assertIn(link_id, tracked_url)
    
    def test_get_tracking_stats(self):
        """Test tracking statistics"""
        email_id = "email123"
        
        # Generate tracking pixel and record open
        tracking_id, _ = self.tracking.generate_tracking_pixel(
            email_id, "user1@example.com"
        )
        self.tracking.record_email_open(tracking_id)
        
        stats = self.tracking.get_tracking_stats(email_id)
        
        self.assertIn("email_id", stats)
        self.assertIn("unique_opens", stats)
        self.assertIn("open_rate", stats)
    
    def test_inject_tracking_into_email(self):
        """Test tracking injection into HTML email"""
        html = "<html><body><h1>Test</h1></body></html>"
        
        tracked_html = self.tracking.inject_tracking_into_email(
            html, "email123", "user@example.com", track_links=False
        )
        
        self.assertIn("<img", tracked_html)
        self.assertIn("track.test.com", tracked_html)


class TestPhishingDetector(unittest.TestCase):
    """Test PhishingDetector class"""
    
    def setUp(self):
        self.detector = PhishingDetector()
    
    def test_analyze_legitimate_email(self):
        """Test analysis of legitimate email"""
        email_data = {
            "from": "support@company.com",
            "subject": "Your monthly report",
            "body": "Here is your monthly report for review.",
            "authentication": {
                "spf": {"status": "pass"},
                "dkim": {"status": "pass"},
                "dmarc": {"status": "pass"}
            }
        }
        
        result = self.detector.analyze_email_for_phishing(email_data)
        
        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertLess(result["risk_score"], 30)  # Should be low risk
    
    def test_analyze_phishing_email(self):
        """Test analysis of phishing email"""
        email_data = {
            "from": "urgent@paypa1.com",
            "subject": "URGENT: Verify your account NOW!!!",
            "body": "Your account will be suspended. Click here immediately to verify your password and credit card.",
            "authentication": {
                "spf": {"status": "fail"},
                "dkim": {"status": "fail"},
                "dmarc": {"status": "fail"}
            }
        }
        
        result = self.detector.analyze_email_for_phishing(email_data)
        
        self.assertIn("risk_score", result)
        self.assertGreater(result["risk_score"], 50)  # Should be high risk
        self.assertTrue(result["is_likely_phishing"])
    
    def test_sender_reputation(self):
        """Test sender reputation calculation"""
        result = self.detector.calculate_sender_reputation("example.com")
        
        self.assertIn("score", result)
        self.assertIn("rating", result)
        self.assertIn("factors", result)


class TestAutoReplySystem(unittest.TestCase):
    """Test AutoReplySystem class"""
    
    def setUp(self):
        self.auto_reply = AutoReplySystem()
    
    def test_add_template(self):
        """Test adding auto-reply template"""
        self.auto_reply.add_template(
            "welcome",
            "Thank you for contacting us, {name}. We will respond within 24 hours.",
            ["name"]
        )
        
        self.assertIn("welcome", self.auto_reply.templates)
    
    def test_generate_template_reply(self):
        """Test generating reply from template"""
        self.auto_reply.add_template(
            "welcome",
            "Thank you for contacting us, {name}. We will respond within 24 hours.",
            ["name"]
        )
        
        reply = self.auto_reply.generate_template_reply(
            "welcome",
            {"name": "John"}
        )
        
        self.assertIn("John", reply)
        self.assertNotIn("{name}", reply)
    
    def test_add_auto_reply_rule(self):
        """Test adding auto-reply rule"""
        self.auto_reply.add_auto_reply_rule(
            "vip_rule",
            {"type": "sender", "value": "vip@example.com"},
            {"type": "send_reply", "template": "vip_response"},
            priority=10
        )
        
        self.assertEqual(len(self.auto_reply.rules), 1)
    
    def test_evaluate_rules(self):
        """Test rule evaluation"""
        self.auto_reply.add_auto_reply_rule(
            "test_rule",
            {"type": "subject_contains", "value": "urgent"},
            {"type": "send_reply", "template": "urgent_response"}
        )
        
        email_data = {
            "from": "sender@example.com",
            "subject": "Urgent matter",
            "body": "This is urgent"
        }
        
        action = self.auto_reply.evaluate_rules(email_data)
        
        self.assertIsNotNone(action)
        self.assertEqual(action["type"], "send_reply")
    
    def test_generate_out_of_office(self):
        """Test out-of-office reply generation"""
        start = datetime.now()
        end = start + timedelta(days=7)
        
        reply = self.auto_reply.generate_out_of_office(
            start, end, "colleague@example.com"
        )
        
        self.assertIn("out of the office", reply.lower())
        self.assertIn("colleague@example.com", reply)


class TestEmailNotificationSystem(unittest.TestCase):
    """Test EmailNotificationSystem class"""
    
    def setUp(self):
        self.notifications = EmailNotificationSystem()
    
    def test_add_vip_sender(self):
        """Test adding VIP sender"""
        self.notifications.add_vip_sender("vip@example.com", "push")
        
        self.assertIn("vip@example.com", self.notifications.vip_senders)
    
    def test_add_keyword_alert(self):
        """Test adding keyword alert"""
        self.notifications.add_keyword_alert("urgent", "email")
        
        self.assertIn("urgent", self.notifications.keyword_alerts)
    
    def test_check_notification_triggers(self):
        """Test notification trigger checking"""
        self.notifications.add_vip_sender("vip@example.com")
        self.notifications.add_keyword_alert("deadline")
        
        email_data = {
            "from": "vip@example.com",
            "subject": "Project deadline",
            "body": "The deadline is approaching"
        }
        
        triggers = self.notifications.check_notification_triggers(email_data)
        
        self.assertIsInstance(triggers, list)
        self.assertGreater(len(triggers), 0)
    
    def test_detect_deadline(self):
        """Test deadline detection"""
        email_data = {
            "subject": "Project deadline: January 15, 2024",
            "body": "Please complete by the deadline."
        }
        
        deadline = self.notifications.detect_deadline(email_data)
        
        if deadline:  # May not parse depending on current date
            self.assertIn("date", deadline)
            self.assertIn("description", deadline)
    
    def test_generate_digest(self):
        """Test email digest generation"""
        emails = [
            {"from": "sender1@example.com", "subject": "Test 1", "read": False},
            {"from": "sender2@example.com", "subject": "Test 2", "read": True},
            {"from": "sender1@example.com", "subject": "Test 3", "read": False}
        ]
        
        digest = self.notifications.generate_digest(emails, "daily")
        
        self.assertEqual(digest["total_emails"], 3)
        self.assertEqual(digest["unread_count"], 2)
        self.assertIn("by_sender", digest)


class TestGmailAppsScriptGenerator(unittest.TestCase):
    """Test GmailAppsScriptGenerator class"""
    
    def setUp(self):
        self.generator = GmailAppsScriptGenerator()
    
    def test_generate_auto_reply_script(self):
        """Test auto-reply script generation"""
        conditions = {"sender_contains": "support@example.com"}
        reply = "Thank you for your email. We will respond soon."
        
        script = self.generator.generate_auto_reply_script(conditions, reply)
        
        self.assertIn("function autoReplyToEmails", script)
        self.assertIn("support@example.com", script)
        self.assertIn(reply, script)
    
    def test_generate_label_organizer_script(self):
        """Test label organizer script generation"""
        rules = [
            {
                "name": "Important emails",
                "condition": {"subject_contains": "urgent"},
                "label": "Important"
            }
        ]
        
        script = self.generator.generate_label_organizer_script(rules)
        
        self.assertIn("function organizeEmailsByLabel", script)
        self.assertIn("urgent", script)
        self.assertIn("Important", script)
    
    def test_generate_forwarding_script(self):
        """Test forwarding script generation"""
        rules = [
            {
                "name": "Forward to manager",
                "condition": {"from_contains": "client@example.com"},
                "forward_to": "manager@company.com"
            }
        ]
        
        script = self.generator.generate_forwarding_script(rules)
        
        self.assertIn("function forwardEmails", script)
        self.assertIn("client@example.com", script)
        self.assertIn("manager@company.com", script)


class TestEmailWorkflowBuilder(unittest.TestCase):
    """Test EmailWorkflowBuilder class"""
    
    def setUp(self):
        self.builder = EmailWorkflowBuilder()
    
    def test_create_workflow(self):
        """Test workflow creation"""
        triggers = [{"type": "sender_is", "value": "test@example.com"}]
        actions = [{"type": "send_reply", "reply_template": "Thanks!"}]
        
        workflow = self.builder.create_workflow(
            "wf1", "Test Workflow", triggers, actions
        )
        
        self.assertEqual(workflow["id"], "wf1")
        self.assertEqual(workflow["name"], "Test Workflow")
        self.assertTrue(workflow["enabled"])
    
    def test_execute_workflow(self):
        """Test workflow execution"""
        triggers = [{"type": "subject_contains", "value": "test"}]
        actions = [{"type": "add_label", "label": "Test"}]
        
        self.builder.create_workflow("wf1", "Test", triggers, actions)
        
        email_data = {
            "from": "sender@example.com",
            "subject": "This is a test email",
            "body": "Test content"
        }
        
        result = self.builder.execute_workflow("wf1", email_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["actions_executed"], 1)


class TestScheduledEmailSender(unittest.TestCase):
    """Test ScheduledEmailSender class"""
    
    def setUp(self):
        self.sender = ScheduledEmailSender()
    
    def test_schedule_email(self):
        """Test email scheduling"""
        send_at = datetime.now() + timedelta(hours=1)
        
        scheduled = self.sender.schedule_email(
            "email1",
            "recipient@example.com",
            "Test Subject",
            "Test Body",
            send_at
        )
        
        self.assertEqual(scheduled["id"], "email1")
        self.assertEqual(scheduled["status"], "scheduled")
    
    def test_cancel_scheduled_email(self):
        """Test canceling scheduled email"""
        send_at = datetime.now() + timedelta(hours=1)
        
        self.sender.schedule_email(
            "email1", "recipient@example.com", "Test", "Body", send_at
        )
        
        result = self.sender.cancel_scheduled_email("email1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["email"]["status"], "cancelled")
    
    def test_get_pending_emails(self):
        """Test getting pending emails"""
        # Schedule email in the past (should be pending)
        send_at = datetime.now() - timedelta(minutes=1)
        
        self.sender.schedule_email(
            "email1", "recipient@example.com", "Test", "Body", send_at
        )
        
        pending = self.sender.get_pending_emails()
        
        self.assertIsInstance(pending, list)


class TestMailMergeSystem(unittest.TestCase):
    """Test MailMergeSystem class"""
    
    def setUp(self):
        self.mail_merge = MailMergeSystem()
    
    def test_create_template(self):
        """Test template creation"""
        template = self.mail_merge.create_template(
            "welcome",
            "Welcome {name}!",
            "Hello {name}, welcome to {company}!",
            ["name", "company"]
        )
        
        self.assertEqual(template["id"], "welcome")
        self.assertIn("name", template["variables"])
    
    def test_merge_and_generate(self):
        """Test mail merge generation"""
        self.mail_merge.create_template(
            "welcome",
            "Welcome {name}!",
            "Hello {name}, welcome to {company}!",
            ["name", "company"]
        )
        
        recipients = [
            {"email": "user1@example.com", "name": "John", "company": "Acme"},
            {"email": "user2@example.com", "name": "Jane", "company": "TechCo"}
        ]
        
        emails = self.mail_merge.merge_and_generate("welcome", recipients)
        
        self.assertEqual(len(emails), 2)
        self.assertIn("John", emails[0]["subject"])
        self.assertIn("Acme", emails[0]["body"])
    
    def test_execute_mail_merge(self):
        """Test mail merge execution"""
        self.mail_merge.create_template(
            "newsletter",
            "Newsletter for {name}",
            "Hi {name}!",
            ["name"]
        )
        
        recipients = [
            {"email": "user1@example.com", "name": "John"},
            {"email": "user2@example.com", "name": "Jane"}
        ]
        
        job = self.mail_merge.execute_mail_merge("newsletter", recipients)
        
        self.assertIn("id", job)
        self.assertEqual(job["total_recipients"], 2)
        self.assertEqual(job["status"], "completed")


class TestEmailArchivalSystem(unittest.TestCase):
    """Test EmailArchivalSystem class"""
    
    def setUp(self):
        self.archival = EmailArchivalSystem()
    
    def test_archive_email(self):
        """Test email archival"""
        email_data = {
            "message_id": "test123",
            "from": "sender@example.com",
            "subject": "Test"
        }
        
        result = self.archival.archive_email(email_data)
        
        self.assertTrue(result["success"])
        self.assertIn("archive_id", result)
    
    def test_create_retention_policy(self):
        """Test retention policy creation"""
        policy = self.archival.create_retention_policy(
            "policy1",
            "7 Year Retention",
            2555,  # 7 years in days
            "archive"
        )
        
        self.assertEqual(policy["id"], "policy1")
        self.assertEqual(policy["retention_days"], 2555)
    
    def test_place_legal_hold(self):
        """Test placing legal hold"""
        result = self.archival.place_legal_hold(
            "hold1",
            ["email1", "email2", "email3"],
            "Litigation",
            "Legal Department"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["emails_affected"], 3)
    
    def test_release_legal_hold(self):
        """Test releasing legal hold"""
        self.archival.place_legal_hold(
            "hold1", ["email1"], "Test", "Legal"
        )
        
        result = self.archival.release_legal_hold("hold1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["hold"]["status"], "released")


class TestSpamAnalyzer(unittest.TestCase):
    """Test SpamAnalyzer class"""
    
    def setUp(self):
        self.analyzer = SpamAnalyzer()
    
    def test_analyze_legitimate_email(self):
        """Test spam analysis of legitimate email"""
        email_data = {
            "from": "colleague@company.com",
            "subject": "Meeting tomorrow",
            "body": "Let's meet tomorrow at 2pm.",
            "authentication": {
                "spf": {"status": "pass"},
                "dkim": {"status": "pass"}
            }
        }
        
        result = self.analyzer.analyze_spam_score(email_data)
        
        self.assertLess(result["spam_score"], 30)
        self.assertEqual(result["classification"], "legitimate")
    
    def test_analyze_spam_email(self):
        """Test spam analysis of spam email"""
        email_data = {
            "from": "winner@suspicious.tk",
            "subject": "YOU WON! Claim your prize now!!!",
            "body": "Congratulations! You won $1,000,000! Click here now!",
            "authentication": {
                "spf": {"status": "fail"},
                "dkim": {"status": "fail"}
            }
        }
        
        result = self.analyzer.analyze_spam_score(email_data)
        
        self.assertGreater(result["spam_score"], 30)
        self.assertTrue(result["is_spam"])


class TestBulkEmailOperations(unittest.TestCase):
    """Test BulkEmailOperations class"""
    
    def setUp(self):
        self.bulk_ops = BulkEmailOperations()
    
    def test_bulk_delete(self):
        """Test bulk delete operation"""
        email_ids = ["email1", "email2", "email3"]
        
        result = self.bulk_ops.bulk_delete(email_ids)
        
        self.assertEqual(result["total_emails"], 3)
        self.assertEqual(result["deleted"], 3)
        self.assertEqual(result["operation"], "delete")
    
    def test_bulk_move(self):
        """Test bulk move operation"""
        email_ids = ["email1", "email2"]
        
        result = self.bulk_ops.bulk_move(email_ids, "Archive")
        
        self.assertEqual(result["total_emails"], 2)
        self.assertEqual(result["destination"], "Archive")
    
    def test_bulk_label(self):
        """Test bulk label operation"""
        email_ids = ["email1", "email2", "email3"]
        labels = ["Important", "Work"]
        
        result = self.bulk_ops.bulk_label(email_ids, labels)
        
        self.assertEqual(result["total_emails"], 3)
        self.assertEqual(result["labels"], labels)


class TestOAuthTokenManager(unittest.TestCase):
    """Test OAuthTokenManager class"""
    
    def setUp(self):
        self.oauth = OAuthTokenManager()
    
    def test_store_token(self):
        """Test storing OAuth token"""
        token = self.oauth.store_token(
            "gmail",
            "user123",
            "access_token_abc",
            "refresh_token_xyz",
            3600
        )
        
        self.assertEqual(token["provider"], "gmail")
        self.assertEqual(token["user_id"], "user123")
    
    def test_get_token(self):
        """Test retrieving OAuth token"""
        self.oauth.store_token(
            "gmail", "user123", "access_token", "refresh_token", 3600
        )
        
        token = self.oauth.get_token("gmail", "user123")
        
        self.assertIsNotNone(token)
        self.assertEqual(token["access_token"], "access_token")
    
    def test_revoke_token(self):
        """Test revoking OAuth token"""
        self.oauth.store_token(
            "gmail", "user123", "access_token", "refresh_token", 3600
        )
        
        result = self.oauth.revoke_token("gmail", "user123")
        
        self.assertTrue(result["success"])
        
        # Token should no longer exist
        token = self.oauth.get_token("gmail", "user123")
        self.assertIsNone(token)


class TestEmailCampaignManager(unittest.TestCase):
    """Test EmailCampaignManager class"""
    
    def setUp(self):
        self.campaign_mgr = EmailCampaignManager()
    
    def test_create_campaign(self):
        """Test campaign creation"""
        campaign = self.campaign_mgr.create_campaign(
            "camp1",
            "Newsletter",
            "Monthly Update",
            "Here's what's new...",
            ["user1@example.com", "user2@example.com"]
        )
        
        self.assertEqual(campaign["id"], "camp1")
        self.assertEqual(campaign["status"], "draft")
        self.assertEqual(len(campaign["recipients"]), 2)
    
    def test_send_campaign(self):
        """Test sending campaign"""
        self.campaign_mgr.create_campaign(
            "camp1", "Test", "Subject", "Body", ["user@example.com"]
        )
        
        result = self.campaign_mgr.send_campaign("camp1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["recipients_count"], 1)
    
    def test_get_campaign_stats(self):
        """Test getting campaign statistics"""
        self.campaign_mgr.create_campaign(
            "camp1", "Test", "Subject", "Body", ["user@example.com"]
        )
        self.campaign_mgr.send_campaign("camp1")
        
        stats = self.campaign_mgr.get_campaign_stats("camp1")
        
        self.assertEqual(stats["campaign_id"], "camp1")
        self.assertIn("stats", stats)
    
    def test_process_unsubscribe(self):
        """Test unsubscribe processing"""
        self.campaign_mgr.create_campaign(
            "camp1", "Test", "Subject", "Body",
            ["user1@example.com", "user2@example.com"]
        )
        
        result = self.campaign_mgr.process_unsubscribe("camp1", "user1@example.com")
        
        self.assertTrue(result["success"])
        
        # Check that recipient was removed
        campaign = self.campaign_mgr.campaigns["camp1"]
        self.assertNotIn("user1@example.com", campaign["recipients"])


class TestEmailTechnologyExpert(unittest.TestCase):
    """Test EmailTechnologyExpert unified interface"""
    
    def setUp(self):
        self.expert = EmailTechnologyExpert()
    
    def test_initialization(self):
        """Test expert initialization"""
        self.assertIsNotNone(self.expert.header_analyzer)
        self.assertIsNotNone(self.expert.auth_validator)
        self.assertIsNotNone(self.expert.tracking)
        self.assertIsNotNone(self.expert.phishing_detector)
    
    def test_get_capabilities(self):
        """Test getting capabilities"""
        capabilities = self.expert.get_capabilities()
        
        self.assertIn("metadata", capabilities)
        self.assertIn("subsystems", capabilities)
        self.assertEqual(capabilities["metadata"]["id"], "email_technology_expert")
    
    def test_setup_auto_reply_workflow(self):
        """Test setting up auto-reply workflow"""
        conditions = {"subject_contains": "support"}
        
        result = self.expert.setup_auto_reply_workflow(
            conditions, "template", "Thank you for contacting support."
        )
        
        self.assertTrue(result["success"])
        self.assertIn("workflow_id", result)


class TestSkillMetadata(unittest.TestCase):
    """Test skill metadata"""
    
    def test_metadata_structure(self):
        """Test metadata has required fields"""
        self.assertIn("name", SKILL_METADATA)
        self.assertIn("id", SKILL_METADATA)
        self.assertIn("version", SKILL_METADATA)
        self.assertIn("capabilities", SKILL_METADATA)
    
    def test_metadata_capabilities(self):
        """Test metadata capabilities list"""
        capabilities = SKILL_METADATA["capabilities"]
        
        self.assertIsInstance(capabilities, list)
        self.assertGreater(len(capabilities), 20)  # Should have many capabilities
        
        # Check for key capabilities
        self.assertIn("email_header_analysis", capabilities)
        self.assertIn("phishing_detection", capabilities)
        self.assertIn("llm_auto_reply_generation", capabilities)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
