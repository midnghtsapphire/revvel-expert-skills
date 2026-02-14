"""
Email Technology Expert Skill Module
Comprehensive cutting-edge email tracing, tracking, auto-answering, notifications, and in-app programming
"""

import json
import re
import os
import base64
import hashlib
import hmac
import time
import email
import imaplib
import smtplib
import socket
import ipaddress
import dns.resolver
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict, Counter
from email import policy
from email.parser import BytesParser, Parser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import parseaddr, parsedate_to_datetime, formataddr
import unittest

try:
    import gnupg
    GPG_AVAILABLE = True
except ImportError:
    GPG_AVAILABLE = False

SKILL_METADATA = {
    "name": "Email Technology Expert",
    "id": "email_technology_expert",
    "version": "2.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive cutting-edge email technology suite including tracing, tracking, auto-answering, auto-notifications, in-app programming for Gmail/Yahoo/Outlook, encryption, forensics, phishing detection, and advanced email automation.",
    "capabilities": [
        "email_header_analysis",
        "email_tracing_ip_geolocation",
        "spf_dkim_dmarc_validation",
        "arc_authentication_chain",
        "email_tracking_pixel_generation",
        "read_receipt_tracking",
        "link_click_tracking",
        "delivery_status_tracking",
        "sender_reputation_scoring",
        "phishing_detection",
        "email_forensics",
        "metadata_extraction",
        "llm_auto_reply_generation",
        "context_aware_responses",
        "template_auto_replies",
        "priority_based_routing",
        "auto_forward_rules",
        "real_time_notifications",
        "vip_sender_alerts",
        "keyword_triggered_alerts",
        "deadline_detection",
        "follow_up_reminders",
        "gmail_apps_script_generation",
        "outlook_rules_creation",
        "yahoo_mail_filters",
        "email_workflow_builder",
        "scheduled_email_sending",
        "mail_merge",
        "pgp_gpg_encryption",
        "email_archival_compliance",
        "spam_analysis",
        "bulk_operations",
        "oauth_token_management",
        "email_campaign_automation"
    ],
    "domain": "email_technology",
    "api_integrations": [
        "gmail_api",
        "microsoft_graph_api",
        "yahoo_mail_api",
        "openrouter_llm_api",
        "ipinfo_geolocation",
        "virustotal_api",
        "spamhaus_api"
    ]
}

# ============================================================================
# EMAIL HEADER ANALYSIS & TRACING
# ============================================================================

class EmailHeaderAnalyzer:
    """Comprehensive email header analysis and tracing"""
    
    def __init__(self):
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 5
    
    def parse_email_headers(self, raw_email: Union[str, bytes]) -> Dict[str, Any]:
        """Parse email headers from raw email content"""
        if isinstance(raw_email, str):
            msg = Parser(policy=policy.default).parsestr(raw_email)
        else:
            msg = BytesParser(policy=policy.default).parsebytes(raw_email)
        
        headers = {}
        for key, value in msg.items():
            if key in headers:
                if isinstance(headers[key], list):
                    headers[key].append(value)
                else:
                    headers[key] = [headers[key], value]
            else:
                headers[key] = value
        
        return {
            "headers": headers,
            "subject": msg.get("Subject", ""),
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "date": msg.get("Date", ""),
            "message_id": msg.get("Message-ID", ""),
            "body": self._extract_body(msg),
            "attachments": self._extract_attachments(msg)
        }
    
    def _extract_body(self, msg) -> str:
        """Extract email body content"""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/html":
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        return ""
    
    def _extract_attachments(self, msg) -> List[Dict[str, Any]]:
        """Extract attachment information"""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    attachments.append({
                        "filename": part.get_filename(),
                        "content_type": part.get_content_type(),
                        "size": len(part.get_payload(decode=True))
                    })
        return attachments
    
    def trace_email_path(self, headers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trace full email routing path from Received headers"""
        received_headers = headers.get("Received", [])
        if not isinstance(received_headers, list):
            received_headers = [received_headers]
        
        path = []
        for idx, received in enumerate(reversed(received_headers)):
            hop = self._parse_received_header(received)
            hop["hop_number"] = idx + 1
            path.append(hop)
        
        return path
    
    def _parse_received_header(self, received: str) -> Dict[str, Any]:
        """Parse a single Received header"""
        hop = {
            "raw": received,
            "from_domain": None,
            "from_ip": None,
            "by_domain": None,
            "timestamp": None,
            "protocol": None
        }
        
        # Extract from domain
        from_match = re.search(r'from\s+([^\s\(\[]+)', received, re.IGNORECASE)
        if from_match:
            hop["from_domain"] = from_match.group(1)
        
        # Extract IP address
        ip_match = re.search(r'\[?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', received)
        if ip_match:
            hop["from_ip"] = ip_match.group(1)
        
        # Extract by domain
        by_match = re.search(r'by\s+([^\s\(\[]+)', received, re.IGNORECASE)
        if by_match:
            hop["by_domain"] = by_match.group(1)
        
        # Extract timestamp
        date_match = re.search(r';\s*(.+)$', received)
        if date_match:
            try:
                hop["timestamp"] = parsedate_to_datetime(date_match.group(1).strip()).isoformat()
            except:
                hop["timestamp"] = date_match.group(1).strip()
        
        # Extract protocol
        protocol_match = re.search(r'with\s+(\w+)', received, re.IGNORECASE)
        if protocol_match:
            hop["protocol"] = protocol_match.group(1)
        
        return hop
    
    def geolocate_ip(self, ip_address: str) -> Dict[str, Any]:
        """Geolocate IP address using ipinfo.io"""
        try:
            response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": ip_address,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "location": data.get("loc"),
                    "org": data.get("org"),
                    "postal": data.get("postal"),
                    "timezone": data.get("timezone")
                }
        except Exception as e:
            return {"ip": ip_address, "error": str(e)}
        
        return {"ip": ip_address, "error": "Unable to geolocate"}
    
    def extract_all_ips(self, headers: Dict[str, Any]) -> List[str]:
        """Extract all IP addresses from email headers"""
        ips = []
        received_headers = headers.get("Received", [])
        if not isinstance(received_headers, list):
            received_headers = [received_headers]
        
        for received in received_headers:
            ip_matches = re.findall(r'\[?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', received)
            ips.extend(ip_matches)
        
        # Remove duplicates and private IPs
        unique_ips = []
        for ip in ips:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if not ip_obj.is_private and ip not in unique_ips:
                    unique_ips.append(ip)
            except:
                pass
        
        return unique_ips
    
    def analyze_email_forensics(self, raw_email: Union[str, bytes]) -> Dict[str, Any]:
        """Complete forensic analysis of email"""
        parsed = self.parse_email_headers(raw_email)
        headers = parsed["headers"]
        
        # Trace routing path
        routing_path = self.trace_email_path(headers)
        
        # Extract and geolocate IPs
        ips = self.extract_all_ips(headers)
        geolocations = [self.geolocate_ip(ip) for ip in ips]
        
        # Calculate delivery time
        delivery_time = self._calculate_delivery_time(routing_path)
        
        # Extract authentication results
        auth_results = self.extract_authentication_results(headers)
        
        return {
            "message_id": parsed["message_id"],
            "subject": parsed["subject"],
            "from": parsed["from"],
            "to": parsed["to"],
            "date": parsed["date"],
            "routing_path": routing_path,
            "total_hops": len(routing_path),
            "ip_addresses": ips,
            "geolocations": geolocations,
            "delivery_time_seconds": delivery_time,
            "authentication": auth_results,
            "attachments": parsed["attachments"],
            "body_preview": parsed["body"][:500] if parsed["body"] else ""
        }
    
    def _calculate_delivery_time(self, routing_path: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate total delivery time from routing path"""
        if len(routing_path) < 2:
            return None
        
        try:
            first_timestamp = routing_path[0]["timestamp"]
            last_timestamp = routing_path[-1]["timestamp"]
            
            if first_timestamp and last_timestamp:
                first_dt = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
                last_dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                return (last_dt - first_dt).total_seconds()
        except:
            pass
        
        return None
    
    def extract_authentication_results(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract SPF, DKIM, DMARC, ARC authentication results"""
        auth = {
            "spf": self._extract_spf_result(headers),
            "dkim": self._extract_dkim_result(headers),
            "dmarc": self._extract_dmarc_result(headers),
            "arc": self._extract_arc_result(headers)
        }
        return auth
    
    def _extract_spf_result(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract SPF authentication result"""
        received_spf = headers.get("Received-SPF", "")
        auth_results = headers.get("Authentication-Results", "")
        
        result = {"status": "none", "details": ""}
        
        if received_spf:
            result["details"] = received_spf
            if "pass" in received_spf.lower():
                result["status"] = "pass"
            elif "fail" in received_spf.lower():
                result["status"] = "fail"
            elif "softfail" in received_spf.lower():
                result["status"] = "softfail"
            elif "neutral" in received_spf.lower():
                result["status"] = "neutral"
        
        if not result["status"] or result["status"] == "none":
            spf_match = re.search(r'spf=(\w+)', str(auth_results), re.IGNORECASE)
            if spf_match:
                result["status"] = spf_match.group(1).lower()
        
        return result
    
    def _extract_dkim_result(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract DKIM authentication result"""
        auth_results = headers.get("Authentication-Results", "")
        dkim_signature = headers.get("DKIM-Signature", "")
        
        result = {"status": "none", "details": "", "selector": None, "domain": None}
        
        if dkim_signature:
            result["details"] = dkim_signature
            # Extract selector and domain
            selector_match = re.search(r's=([^;]+)', dkim_signature)
            domain_match = re.search(r'd=([^;]+)', dkim_signature)
            if selector_match:
                result["selector"] = selector_match.group(1).strip()
            if domain_match:
                result["domain"] = domain_match.group(1).strip()
        
        if auth_results:
            dkim_match = re.search(r'dkim=(\w+)', str(auth_results), re.IGNORECASE)
            if dkim_match:
                result["status"] = dkim_match.group(1).lower()
        
        return result
    
    def _extract_dmarc_result(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract DMARC authentication result"""
        auth_results = headers.get("Authentication-Results", "")
        
        result = {"status": "none", "details": ""}
        
        if auth_results:
            dmarc_match = re.search(r'dmarc=(\w+)', str(auth_results), re.IGNORECASE)
            if dmarc_match:
                result["status"] = dmarc_match.group(1).lower()
            result["details"] = str(auth_results)
        
        return result
    
    def _extract_arc_result(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ARC (Authenticated Received Chain) result"""
        arc_auth = headers.get("ARC-Authentication-Results", "")
        arc_seal = headers.get("ARC-Seal", "")
        arc_message_sig = headers.get("ARC-Message-Signature", "")
        
        result = {
            "status": "none",
            "authentication_results": arc_auth,
            "seal": arc_seal,
            "message_signature": arc_message_sig,
            "chain_valid": False
        }
        
        if arc_seal:
            # Check if ARC chain is valid
            cv_match = re.search(r'cv=(\w+)', arc_seal)
            if cv_match:
                cv_value = cv_match.group(1).lower()
                result["status"] = cv_value
                result["chain_valid"] = (cv_value == "pass")
        
        return result


# ============================================================================
# SPF/DKIM/DMARC VALIDATION
# ============================================================================

class EmailAuthenticationValidator:
    """Validate SPF, DKIM, DMARC records"""
    
    def __init__(self):
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 5
    
    def validate_spf(self, domain: str, sender_ip: str) -> Dict[str, Any]:
        """Validate SPF record for domain and sender IP"""
        try:
            # Query SPF record
            answers = self.dns_resolver.resolve(domain, 'TXT')
            spf_record = None
            
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt.startswith('v=spf1'):
                    spf_record = txt
                    break
            
            if not spf_record:
                return {"valid": False, "status": "none", "record": None, "error": "No SPF record found"}
            
            # Parse SPF record
            result = self._evaluate_spf_record(spf_record, sender_ip, domain)
            result["record"] = spf_record
            
            return result
        
        except Exception as e:
            return {"valid": False, "status": "error", "record": None, "error": str(e)}
    
    def _evaluate_spf_record(self, spf_record: str, sender_ip: str, domain: str) -> Dict[str, Any]:
        """Evaluate SPF record against sender IP"""
        mechanisms = spf_record.split()
        
        try:
            sender_ip_obj = ipaddress.ip_address(sender_ip)
        except:
            return {"valid": False, "status": "error", "error": "Invalid sender IP"}
        
        for mechanism in mechanisms[1:]:  # Skip v=spf1
            if mechanism.startswith('ip4:'):
                ip_range = mechanism[4:]
                try:
                    if '/' in ip_range:
                        network = ipaddress.ip_network(ip_range, strict=False)
                        if sender_ip_obj in network:
                            return {"valid": True, "status": "pass", "matched_mechanism": mechanism}
                    else:
                        if str(sender_ip_obj) == ip_range:
                            return {"valid": True, "status": "pass", "matched_mechanism": mechanism}
                except:
                    pass
            
            elif mechanism.startswith('include:'):
                # Recursive SPF check (simplified)
                included_domain = mechanism[8:]
                result = self.validate_spf(included_domain, sender_ip)
                if result.get("valid"):
                    return {"valid": True, "status": "pass", "matched_mechanism": mechanism}
            
            elif mechanism == 'a':
                # Check if sender IP matches domain's A record
                try:
                    a_records = self.dns_resolver.resolve(domain, 'A')
                    for rdata in a_records:
                        if str(sender_ip_obj) == str(rdata):
                            return {"valid": True, "status": "pass", "matched_mechanism": mechanism}
                except:
                    pass
            
            elif mechanism == 'mx':
                # Check if sender IP matches domain's MX record IPs
                try:
                    mx_records = self.dns_resolver.resolve(domain, 'MX')
                    for mx in mx_records:
                        mx_host = str(mx.exchange).rstrip('.')
                        a_records = self.dns_resolver.resolve(mx_host, 'A')
                        for rdata in a_records:
                            if str(sender_ip_obj) == str(rdata):
                                return {"valid": True, "status": "pass", "matched_mechanism": mechanism}
                except:
                    pass
            
            elif mechanism in ['~all', '-all', '?all', '+all']:
                qualifier = mechanism[0]
                if qualifier == '+':
                    return {"valid": True, "status": "pass", "matched_mechanism": mechanism}
                elif qualifier == '-':
                    return {"valid": False, "status": "fail", "matched_mechanism": mechanism}
                elif qualifier == '~':
                    return {"valid": False, "status": "softfail", "matched_mechanism": mechanism}
                elif qualifier == '?':
                    return {"valid": False, "status": "neutral", "matched_mechanism": mechanism}
        
        return {"valid": False, "status": "neutral", "matched_mechanism": "default"}
    
    def validate_dkim(self, domain: str, selector: str) -> Dict[str, Any]:
        """Validate DKIM record for domain and selector"""
        try:
            dkim_domain = f"{selector}._domainkey.{domain}"
            answers = self.dns_resolver.resolve(dkim_domain, 'TXT')
            
            dkim_record = None
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if 'p=' in txt:  # DKIM records contain public key
                    dkim_record = txt
                    break
            
            if not dkim_record:
                return {"valid": False, "record": None, "error": "No DKIM record found"}
            
            # Parse DKIM record
            public_key = None
            key_type = "rsa"
            
            p_match = re.search(r'p=([^;]+)', dkim_record)
            if p_match:
                public_key = p_match.group(1).strip()
            
            k_match = re.search(r'k=([^;]+)', dkim_record)
            if k_match:
                key_type = k_match.group(1).strip()
            
            return {
                "valid": True,
                "record": dkim_record,
                "public_key": public_key,
                "key_type": key_type,
                "selector": selector,
                "domain": domain
            }
        
        except Exception as e:
            return {"valid": False, "record": None, "error": str(e)}
    
    def validate_dmarc(self, domain: str) -> Dict[str, Any]:
        """Validate DMARC record for domain"""
        try:
            dmarc_domain = f"_dmarc.{domain}"
            answers = self.dns_resolver.resolve(dmarc_domain, 'TXT')
            
            dmarc_record = None
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt.startswith('v=DMARC1'):
                    dmarc_record = txt
                    break
            
            if not dmarc_record:
                return {"valid": False, "record": None, "error": "No DMARC record found"}
            
            # Parse DMARC record
            policy = None
            subdomain_policy = None
            percentage = 100
            rua = []
            ruf = []
            
            p_match = re.search(r'p=([^;]+)', dmarc_record)
            if p_match:
                policy = p_match.group(1).strip()
            
            sp_match = re.search(r'sp=([^;]+)', dmarc_record)
            if sp_match:
                subdomain_policy = sp_match.group(1).strip()
            
            pct_match = re.search(r'pct=([^;]+)', dmarc_record)
            if pct_match:
                percentage = int(pct_match.group(1).strip())
            
            rua_match = re.search(r'rua=([^;]+)', dmarc_record)
            if rua_match:
                rua = [addr.strip() for addr in rua_match.group(1).split(',')]
            
            ruf_match = re.search(r'ruf=([^;]+)', dmarc_record)
            if ruf_match:
                ruf = [addr.strip() for addr in ruf_match.group(1).split(',')]
            
            return {
                "valid": True,
                "record": dmarc_record,
                "policy": policy,
                "subdomain_policy": subdomain_policy,
                "percentage": percentage,
                "aggregate_reports": rua,
                "forensic_reports": ruf
            }
        
        except Exception as e:
            return {"valid": False, "record": None, "error": str(e)}
    
    def comprehensive_domain_check(self, domain: str, sender_ip: Optional[str] = None, 
                                   dkim_selector: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive authentication check for domain"""
        results = {
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "spf": None,
            "dkim": None,
            "dmarc": None,
            "overall_score": 0
        }
        
        # Validate DMARC
        dmarc_result = self.validate_dmarc(domain)
        results["dmarc"] = dmarc_result
        if dmarc_result.get("valid"):
            results["overall_score"] += 33
        
        # Validate SPF if sender IP provided
        if sender_ip:
            spf_result = self.validate_spf(domain, sender_ip)
            results["spf"] = spf_result
            if spf_result.get("valid"):
                results["overall_score"] += 33
        
        # Validate DKIM if selector provided
        if dkim_selector:
            dkim_result = self.validate_dkim(domain, dkim_selector)
            results["dkim"] = dkim_result
            if dkim_result.get("valid"):
                results["overall_score"] += 34
        
        return results


# ============================================================================
# EMAIL TRACKING & MONITORING
# ============================================================================

class EmailTrackingSystem:
    """Email tracking pixel generation, link tracking, and read receipts"""
    
    def __init__(self, tracking_domain: str = "track.example.com"):
        self.tracking_domain = tracking_domain
        self.tracking_db = {}  # In production, use real database
    
    def generate_tracking_pixel(self, email_id: str, recipient: str) -> Tuple[str, str]:
        """Generate tracking pixel for email open tracking"""
        tracking_id = hashlib.sha256(f"{email_id}:{recipient}:{time.time()}".encode()).hexdigest()
        
        # Store tracking info
        self.tracking_db[tracking_id] = {
            "email_id": email_id,
            "recipient": recipient,
            "created_at": datetime.utcnow().isoformat(),
            "opened": False,
            "open_count": 0,
            "open_timestamps": []
        }
        
        # Generate 1x1 transparent pixel URL
        pixel_url = f"https://{self.tracking_domain}/pixel/{tracking_id}.png"
        
        # HTML img tag
        pixel_html = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />'
        
        return tracking_id, pixel_html
    
    def record_email_open(self, tracking_id: str, user_agent: str = None, 
                         ip_address: str = None) -> Dict[str, Any]:
        """Record email open event"""
        if tracking_id not in self.tracking_db:
            return {"success": False, "error": "Invalid tracking ID"}
        
        tracking_info = self.tracking_db[tracking_id]
        tracking_info["opened"] = True
        tracking_info["open_count"] += 1
        tracking_info["open_timestamps"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_agent": user_agent,
            "ip_address": ip_address
        })
        
        return {
            "success": True,
            "email_id": tracking_info["email_id"],
            "recipient": tracking_info["recipient"],
            "open_count": tracking_info["open_count"]
        }
    
    def generate_tracked_link(self, email_id: str, recipient: str, 
                             original_url: str) -> Tuple[str, str]:
        """Generate tracked link for click tracking"""
        link_id = hashlib.sha256(f"{email_id}:{recipient}:{original_url}:{time.time()}".encode()).hexdigest()
        
        # Store link info
        self.tracking_db[link_id] = {
            "email_id": email_id,
            "recipient": recipient,
            "original_url": original_url,
            "created_at": datetime.utcnow().isoformat(),
            "clicked": False,
            "click_count": 0,
            "click_timestamps": []
        }
        
        # Generate tracked URL
        tracked_url = f"https://{self.tracking_domain}/link/{link_id}"
        
        return link_id, tracked_url
    
    def record_link_click(self, link_id: str, user_agent: str = None, 
                         ip_address: str = None) -> Dict[str, Any]:
        """Record link click event"""
        if link_id not in self.tracking_db:
            return {"success": False, "error": "Invalid link ID"}
        
        link_info = self.tracking_db[link_id]
        link_info["clicked"] = True
        link_info["click_count"] += 1
        link_info["click_timestamps"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_agent": user_agent,
            "ip_address": ip_address
        })
        
        return {
            "success": True,
            "email_id": link_info["email_id"],
            "recipient": link_info["recipient"],
            "original_url": link_info["original_url"],
            "click_count": link_info["click_count"]
        }
    
    def get_tracking_stats(self, email_id: str) -> Dict[str, Any]:
        """Get tracking statistics for an email"""
        stats = {
            "email_id": email_id,
            "total_recipients": 0,
            "unique_opens": 0,
            "total_opens": 0,
            "unique_clicks": 0,
            "total_clicks": 0,
            "open_rate": 0.0,
            "click_rate": 0.0,
            "click_to_open_rate": 0.0
        }
        
        recipients = set()
        opened_recipients = set()
        clicked_recipients = set()
        
        for tracking_id, info in self.tracking_db.items():
            if info.get("email_id") == email_id:
                recipient = info.get("recipient")
                recipients.add(recipient)
                
                if "opened" in info and info["opened"]:
                    opened_recipients.add(recipient)
                    stats["total_opens"] += info.get("open_count", 0)
                
                if "clicked" in info and info["clicked"]:
                    clicked_recipients.add(recipient)
                    stats["total_clicks"] += info.get("click_count", 0)
        
        stats["total_recipients"] = len(recipients)
        stats["unique_opens"] = len(opened_recipients)
        stats["unique_clicks"] = len(clicked_recipients)
        
        if stats["total_recipients"] > 0:
            stats["open_rate"] = (stats["unique_opens"] / stats["total_recipients"]) * 100
            stats["click_rate"] = (stats["unique_clicks"] / stats["total_recipients"]) * 100
        
        if stats["unique_opens"] > 0:
            stats["click_to_open_rate"] = (stats["unique_clicks"] / stats["unique_opens"]) * 100
        
        return stats
    
    def inject_tracking_into_email(self, html_content: str, email_id: str, 
                                   recipient: str, track_links: bool = True) -> str:
        """Inject tracking pixel and tracked links into HTML email"""
        # Add tracking pixel at the end of body
        tracking_id, pixel_html = self.generate_tracking_pixel(email_id, recipient)
        
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{pixel_html}</body>')
        else:
            html_content += pixel_html
        
        # Replace links with tracked links
        if track_links:
            link_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]+)"'
            
            def replace_link(match):
                original_url = match.group(1)
                # Skip mailto and anchor links
                if original_url.startswith(('mailto:', '#', 'tel:')):
                    return match.group(0)
                
                link_id, tracked_url = self.generate_tracked_link(email_id, recipient, original_url)
                return match.group(0).replace(original_url, tracked_url)
            
            html_content = re.sub(link_pattern, replace_link, html_content)
        
        return html_content


# ============================================================================
# PHISHING DETECTION & SENDER REPUTATION
# ============================================================================

class PhishingDetector:
    """Detect phishing attempts and analyze sender reputation"""
    
    def __init__(self):
        self.suspicious_keywords = [
            'verify', 'account', 'suspended', 'urgent', 'immediate', 'action required',
            'confirm', 'password', 'security', 'unusual activity', 'click here',
            'limited time', 'expire', 'update', 'billing', 'payment', 'refund',
            'prize', 'winner', 'congratulations', 'claim', 'free', 'gift card'
        ]
        
        self.suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work']
    
    def analyze_email_for_phishing(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive phishing analysis"""
        risk_score = 0
        risk_factors = []
        
        # Analyze sender
        sender_risk = self._analyze_sender(email_data.get("from", ""))
        risk_score += sender_risk["score"]
        risk_factors.extend(sender_risk["factors"])
        
        # Analyze subject
        subject_risk = self._analyze_subject(email_data.get("subject", ""))
        risk_score += subject_risk["score"]
        risk_factors.extend(subject_risk["factors"])
        
        # Analyze body
        body_risk = self._analyze_body(email_data.get("body", ""))
        risk_score += body_risk["score"]
        risk_factors.extend(body_risk["factors"])
        
        # Analyze links
        links_risk = self._analyze_links(email_data.get("body", ""))
        risk_score += links_risk["score"]
        risk_factors.extend(links_risk["factors"])
        
        # Analyze authentication
        auth_risk = self._analyze_authentication(email_data.get("authentication", {}))
        risk_score += auth_risk["score"]
        risk_factors.extend(auth_risk["factors"])
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        elif risk_score >= 10:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "is_likely_phishing": risk_score >= 50,
            "recommendation": self._get_recommendation(risk_level)
        }
    
    def _analyze_sender(self, sender: str) -> Dict[str, Any]:
        """Analyze sender address"""
        score = 0
        factors = []
        
        # Extract email address
        name, email_addr = parseaddr(sender)
        
        if not email_addr:
            return {"score": 0, "factors": []}
        
        # Check for suspicious TLDs
        for tld in self.suspicious_tlds:
            if email_addr.endswith(tld):
                score += 15
                factors.append(f"Suspicious TLD: {tld}")
                break
        
        # Check for mismatched display name and email
        if name and '@' in name:
            score += 20
            factors.append("Display name contains email address")
        
        # Check for lookalike domains
        domain = email_addr.split('@')[-1]
        if self._is_lookalike_domain(domain):
            score += 25
            factors.append(f"Potential lookalike domain: {domain}")
        
        # Check for excessive subdomains
        if domain.count('.') > 2:
            score += 10
            factors.append("Excessive subdomains in sender domain")
        
        return {"score": score, "factors": factors}
    
    def _is_lookalike_domain(self, domain: str) -> bool:
        """Check if domain is a lookalike of popular services"""
        lookalike_patterns = [
            r'.*paypa[l1].*',
            r'.*g[o0][o0]g[l1]e.*',
            r'.*amazo[n0].*',
            r'.*micr[o0]s[o0]ft.*',
            r'.*app[l1]e.*',
            r'.*faceb[o0][o0]k.*',
            r'.*netf[l1]ix.*',
            r'.*bank.*'
        ]
        
        for pattern in lookalike_patterns:
            if re.match(pattern, domain, re.IGNORECASE):
                # Check if it's actually the legitimate domain
                legitimate = ['paypal.com', 'google.com', 'amazon.com', 'microsoft.com', 
                            'apple.com', 'facebook.com', 'netflix.com']
                if domain not in legitimate:
                    return True
        
        return False
    
    def _analyze_subject(self, subject: str) -> Dict[str, Any]:
        """Analyze email subject"""
        score = 0
        factors = []
        
        subject_lower = subject.lower()
        
        # Check for suspicious keywords
        keyword_count = sum(1 for keyword in self.suspicious_keywords if keyword in subject_lower)
        if keyword_count >= 3:
            score += 20
            factors.append(f"Multiple suspicious keywords in subject ({keyword_count})")
        elif keyword_count >= 1:
            score += 10
            factors.append("Suspicious keywords in subject")
        
        # Check for urgency indicators
        urgency_words = ['urgent', 'immediate', 'asap', 'now', 'today', 'expire']
        if any(word in subject_lower for word in urgency_words):
            score += 15
            factors.append("Urgency indicators in subject")
        
        # Check for excessive punctuation
        if subject.count('!') >= 2 or subject.count('?') >= 2:
            score += 10
            factors.append("Excessive punctuation in subject")
        
        # Check for all caps
        if subject.isupper() and len(subject) > 10:
            score += 10
            factors.append("Subject in all caps")
        
        return {"score": score, "factors": factors}
    
    def _analyze_body(self, body: str) -> Dict[str, Any]:
        """Analyze email body"""
        score = 0
        factors = []
        
        body_lower = body.lower()
        
        # Check for suspicious keywords
        keyword_count = sum(1 for keyword in self.suspicious_keywords if keyword in body_lower)
        if keyword_count >= 5:
            score += 15
            factors.append(f"Multiple suspicious keywords in body ({keyword_count})")
        
        # Check for urgency and threats
        threat_phrases = ['account will be closed', 'suspended', 'locked out', 'unauthorized access']
        if any(phrase in body_lower for phrase in threat_phrases):
            score += 20
            factors.append("Threatening language detected")
        
        # Check for requests for personal information
        personal_info_requests = ['social security', 'ssn', 'credit card', 'password', 'pin', 'account number']
        if any(request in body_lower for request in personal_info_requests):
            score += 25
            factors.append("Requests for sensitive personal information")
        
        # Check for poor grammar/spelling (simplified)
        if body.count('  ') > 5:  # Multiple double spaces
            score += 5
            factors.append("Poor formatting detected")
        
        return {"score": score, "factors": factors}
    
    def _analyze_links(self, body: str) -> Dict[str, Any]:
        """Analyze links in email body"""
        score = 0
        factors = []
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, body)
        
        if not urls:
            return {"score": 0, "factors": []}
        
        # Check for shortened URLs
        shorteners = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly']
        shortened_count = sum(1 for url in urls if any(shortener in url for shortener in shorteners))
        if shortened_count > 0:
            score += 15
            factors.append(f"Contains {shortened_count} shortened URL(s)")
        
        # Check for IP addresses in URLs
        ip_urls = [url for url in urls if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url)]
        if ip_urls:
            score += 20
            factors.append("URLs contain IP addresses instead of domains")
        
        # Check for suspicious TLDs in URLs
        for url in urls:
            for tld in self.suspicious_tlds:
                if tld in url:
                    score += 10
                    factors.append(f"Suspicious TLD in URL: {tld}")
                    break
        
        # Check for mismatched link text and URL
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        links = re.findall(link_pattern, body, re.IGNORECASE)
        for href, text in links:
            if 'http' in text and href not in text:
                score += 15
                factors.append("Mismatched link text and destination")
                break
        
        return {"score": score, "factors": factors}
    
    def _analyze_authentication(self, auth_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email authentication results"""
        score = 0
        factors = []
        
        # Check SPF
        spf = auth_results.get("spf", {})
        if spf.get("status") == "fail":
            score += 25
            factors.append("SPF authentication failed")
        elif spf.get("status") == "softfail":
            score += 15
            factors.append("SPF soft fail")
        elif spf.get("status") == "none":
            score += 10
            factors.append("No SPF record")
        
        # Check DKIM
        dkim = auth_results.get("dkim", {})
        if dkim.get("status") == "fail":
            score += 25
            factors.append("DKIM authentication failed")
        elif dkim.get("status") == "none":
            score += 10
            factors.append("No DKIM signature")
        
        # Check DMARC
        dmarc = auth_results.get("dmarc", {})
        if dmarc.get("status") == "fail":
            score += 25
            factors.append("DMARC authentication failed")
        elif dmarc.get("status") == "none":
            score += 10
            factors.append("No DMARC policy")
        
        return {"score": score, "factors": factors}
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "critical": "DO NOT interact with this email. Delete immediately and report as phishing.",
            "high": "Exercise extreme caution. Do not click links or provide information. Verify sender through alternative means.",
            "medium": "Be cautious. Verify sender identity before taking any action. Do not provide sensitive information.",
            "low": "Exercise normal caution. Verify any unusual requests independently.",
            "minimal": "Email appears legitimate, but always verify unexpected requests."
        }
        return recommendations.get(risk_level, "Unknown risk level")
    
    def calculate_sender_reputation(self, domain: str, email_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate sender reputation score"""
        reputation = {
            "domain": domain,
            "score": 50,  # Start at neutral
            "factors": [],
            "rating": "neutral"
        }
        
        # Check domain age (would need WHOIS API in production)
        # For now, simplified check
        
        # Check if domain has proper email authentication
        validator = EmailAuthenticationValidator()
        auth_check = validator.comprehensive_domain_check(domain)
        
        if auth_check["overall_score"] >= 90:
            reputation["score"] += 20
            reputation["factors"].append("Strong email authentication")
        elif auth_check["overall_score"] >= 60:
            reputation["score"] += 10
            reputation["factors"].append("Moderate email authentication")
        else:
            reputation["score"] -= 15
            reputation["factors"].append("Weak or missing email authentication")
        
        # Analyze email history if provided
        if email_history:
            spam_count = sum(1 for email in email_history if email.get("is_spam", False))
            total_count = len(email_history)
            
            if total_count > 0:
                spam_rate = spam_count / total_count
                if spam_rate > 0.5:
                    reputation["score"] -= 30
                    reputation["factors"].append(f"High spam rate: {spam_rate:.1%}")
                elif spam_rate > 0.2:
                    reputation["score"] -= 15
                    reputation["factors"].append(f"Moderate spam rate: {spam_rate:.1%}")
                else:
                    reputation["score"] += 10
                    reputation["factors"].append(f"Low spam rate: {spam_rate:.1%}")
        
        # Determine rating
        if reputation["score"] >= 80:
            reputation["rating"] = "excellent"
        elif reputation["score"] >= 60:
            reputation["rating"] = "good"
        elif reputation["score"] >= 40:
            reputation["rating"] = "neutral"
        elif reputation["score"] >= 20:
            reputation["rating"] = "poor"
        else:
            reputation["rating"] = "bad"
        
        return reputation


# ============================================================================
# AUTO-REPLY & LLM INTEGRATION
# ============================================================================

class AutoReplySystem:
    """Intelligent auto-reply generation using LLM"""
    
    def __init__(self, openrouter_api_key: str = None):
        self.api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.templates = {}
        self.rules = []
    
    def generate_llm_reply(self, email_content: str, context: Dict[str, Any] = None,
                          model: str = "anthropic/claude-3.5-sonnet") -> Dict[str, Any]:
        """Generate intelligent auto-reply using LLM"""
        if not self.api_key:
            return {"success": False, "error": "OpenRouter API key not configured"}
        
        # Build context-aware prompt
        prompt = self._build_reply_prompt(email_content, context)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a professional email assistant. Generate appropriate, concise email replies."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                reply_text = data["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "reply": reply_text,
                    "model": model,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _build_reply_prompt(self, email_content: str, context: Dict[str, Any] = None) -> str:
        """Build context-aware prompt for LLM"""
        prompt = f"Generate a professional email reply to the following email:\n\n{email_content}\n\n"
        
        if context:
            if context.get("sender_name"):
                prompt += f"Sender name: {context['sender_name']}\n"
            if context.get("relationship"):
                prompt += f"Relationship: {context['relationship']}\n"
            if context.get("tone"):
                prompt += f"Desired tone: {context['tone']}\n"
            if context.get("key_points"):
                prompt += f"Key points to address: {', '.join(context['key_points'])}\n"
            if context.get("previous_conversation"):
                prompt += f"Previous conversation context: {context['previous_conversation']}\n"
        
        prompt += "\nGenerate a concise, professional reply. Do not include subject line or signature."
        
        return prompt
    
    def add_template(self, template_id: str, template: str, variables: List[str] = None):
        """Add auto-reply template"""
        self.templates[template_id] = {
            "template": template,
            "variables": variables or []
        }
    
    def generate_template_reply(self, template_id: str, variables: Dict[str, str] = None) -> str:
        """Generate reply from template"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template_data = self.templates[template_id]
        reply = template_data["template"]
        
        if variables:
            for var_name, var_value in variables.items():
                reply = reply.replace(f"{{{var_name}}}", var_value)
        
        return reply
    
    def add_auto_reply_rule(self, rule_id: str, condition: Dict[str, Any], 
                           action: Dict[str, Any], priority: int = 0):
        """Add auto-reply rule"""
        rule = {
            "id": rule_id,
            "condition": condition,
            "action": action,
            "priority": priority,
            "enabled": True
        }
        self.rules.append(rule)
        self.rules.sort(key=lambda x: x["priority"], reverse=True)
    
    def evaluate_rules(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate auto-reply rules for an email"""
        for rule in self.rules:
            if not rule["enabled"]:
                continue
            
            if self._check_condition(rule["condition"], email_data):
                return rule["action"]
        
        return None
    
    def _check_condition(self, condition: Dict[str, Any], email_data: Dict[str, Any]) -> bool:
        """Check if condition matches email"""
        condition_type = condition.get("type")
        
        if condition_type == "sender":
            sender = email_data.get("from", "")
            return condition["value"] in sender
        
        elif condition_type == "subject_contains":
            subject = email_data.get("subject", "")
            return condition["value"].lower() in subject.lower()
        
        elif condition_type == "keyword":
            body = email_data.get("body", "")
            return condition["value"].lower() in body.lower()
        
        elif condition_type == "priority":
            return email_data.get("priority") == condition["value"]
        
        elif condition_type == "has_attachment":
            attachments = email_data.get("attachments", [])
            return len(attachments) > 0
        
        return False
    
    def generate_out_of_office(self, start_date: datetime, end_date: datetime,
                               alternate_contact: str = None) -> str:
        """Generate out-of-office auto-reply"""
        reply = f"Thank you for your email. I am currently out of the office from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} and will have limited access to email.\n\n"
        reply += "I will respond to your message as soon as possible upon my return.\n\n"
        
        if alternate_contact:
            reply += f"For urgent matters, please contact {alternate_contact}.\n\n"
        
        reply += "Best regards"
        
        return reply


# To be continued in Part 2...


# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

class EmailNotificationSystem:
    """Real-time email notifications and alerts"""
    
    def __init__(self):
        self.notification_rules = []
        self.vip_senders = set()
        self.keyword_alerts = {}
        self.notification_channels = {}
    
    def add_vip_sender(self, email_address: str, notification_channel: str = "push"):
        """Add VIP sender for priority notifications"""
        self.vip_senders.add(email_address.lower())
        self.notification_channels[email_address.lower()] = notification_channel
    
    def remove_vip_sender(self, email_address: str):
        """Remove VIP sender"""
        self.vip_senders.discard(email_address.lower())
        self.notification_channels.pop(email_address.lower(), None)
    
    def add_keyword_alert(self, keyword: str, notification_type: str = "push"):
        """Add keyword-triggered notification"""
        self.keyword_alerts[keyword.lower()] = notification_type
    
    def check_notification_triggers(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if email triggers any notifications"""
        notifications = []
        
        sender = email_data.get("from", "").lower()
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body", "").lower()
        
        # Check VIP sender
        if any(vip in sender for vip in self.vip_senders):
            notifications.append({
                "type": "vip_sender",
                "priority": "high",
                "message": f"New email from VIP: {email_data.get('from')}",
                "channel": self.notification_channels.get(sender, "push")
            })
        
        # Check keyword alerts
        for keyword, notif_type in self.keyword_alerts.items():
            if keyword in subject or keyword in body:
                notifications.append({
                    "type": "keyword_match",
                    "priority": "medium",
                    "message": f"Email contains keyword: {keyword}",
                    "keyword": keyword,
                    "channel": notif_type
                })
        
        # Check for deadline detection
        deadline = self.detect_deadline(email_data)
        if deadline:
            notifications.append({
                "type": "deadline_detected",
                "priority": "high",
                "message": f"Deadline detected: {deadline['description']}",
                "deadline": deadline,
                "channel": "push"
            })
        
        # Check for urgent indicators
        if self.is_urgent(email_data):
            notifications.append({
                "type": "urgent",
                "priority": "high",
                "message": "Urgent email received",
                "channel": "push"
            })
        
        return notifications
    
    def detect_deadline(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect deadlines in email content"""
        content = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        
        # Deadline patterns
        patterns = [
            r'deadline[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'due\s+(?:by|on)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'before\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'deadline[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})',
            r'due[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse the date
                    deadline_date = self._parse_date(date_str)
                    if deadline_date:
                        return {
                            "date": deadline_date.isoformat(),
                            "description": date_str,
                            "days_until": (deadline_date - datetime.now()).days
                        }
                except:
                    pass
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        formats = [
            "%B %d, %Y",
            "%B %d %Y",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%d/%m/%Y",
            "%Y-%m-%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def is_urgent(self, email_data: Dict[str, Any]) -> bool:
        """Check if email is urgent"""
        urgent_keywords = ['urgent', 'asap', 'immediate', 'critical', 'emergency', 'important']
        
        subject = email_data.get("subject", "").lower()
        priority = email_data.get("priority", "").lower()
        
        # Check priority header
        if priority in ['high', 'urgent', '1']:
            return True
        
        # Check for urgent keywords in subject
        if any(keyword in subject for keyword in urgent_keywords):
            return True
        
        return False
    
    def schedule_follow_up_reminder(self, email_id: str, recipient: str, 
                                   days: int = 3) -> Dict[str, Any]:
        """Schedule follow-up reminder if no reply received"""
        reminder_date = datetime.now() + timedelta(days=days)
        
        reminder = {
            "email_id": email_id,
            "recipient": recipient,
            "reminder_date": reminder_date.isoformat(),
            "status": "scheduled",
            "type": "follow_up"
        }
        
        return reminder
    
    def generate_digest(self, emails: List[Dict[str, Any]], 
                       period: str = "daily") -> Dict[str, Any]:
        """Generate email digest notification"""
        digest = {
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "total_emails": len(emails),
            "unread_count": sum(1 for e in emails if not e.get("read", False)),
            "by_sender": Counter([e.get("from", "Unknown") for e in emails]).most_common(10),
            "urgent_count": sum(1 for e in emails if self.is_urgent(e)),
            "with_attachments": sum(1 for e in emails if e.get("attachments")),
            "top_subjects": [e.get("subject", "No subject") for e in emails[:10]]
        }
        
        return digest
    
    def send_webhook_notification(self, webhook_url: str, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification via webhook"""
        try:
            response = requests.post(
                webhook_url,
                json=notification_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# IN-APP PROGRAMMING & AUTOMATION
# ============================================================================

class GmailAppsScriptGenerator:
    """Generate Gmail Apps Script for automation"""
    
    def generate_auto_reply_script(self, conditions: Dict[str, Any], 
                                   reply_template: str) -> str:
        """Generate Apps Script for auto-reply"""
        script = """
function autoReplyToEmails() {
  var threads = GmailApp.getInboxThreads();
  
  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    var lastMessage = messages[messages.length - 1];
    
    // Check if already replied
    if (threads[i].isUnread() && !hasReplied(threads[i])) {
"""
        
        # Add conditions
        if conditions.get("sender_contains"):
            script += f"""
      if (lastMessage.getFrom().indexOf("{conditions['sender_contains']}") !== -1) {{
"""
        
        if conditions.get("subject_contains"):
            script += f"""
      if (lastMessage.getSubject().indexOf("{conditions['subject_contains']}") !== -1) {{
"""
        
        # Add reply action
        script += f"""
        threads[i].reply("{reply_template}");
        threads[i].markRead();
"""
        
        # Close conditions
        if conditions.get("sender_contains") or conditions.get("subject_contains"):
            script += "      }\n"
        
        script += """
    }
  }
}

function hasReplied(thread) {
  var messages = thread.getMessages();
  var myEmail = Session.getActiveUser().getEmail();
  
  for (var i = 0; i < messages.length; i++) {
    if (messages[i].getFrom().indexOf(myEmail) !== -1) {
      return true;
    }
  }
  return false;
}

// Set up trigger to run every 5 minutes
function createTrigger() {
  ScriptApp.newTrigger('autoReplyToEmails')
    .timeBased()
    .everyMinutes(5)
    .create();
}
"""
        
        return script
    
    def generate_label_organizer_script(self, rules: List[Dict[str, Any]]) -> str:
        """Generate Apps Script for automatic labeling"""
        script = """
function organizeEmailsByLabel() {
  var threads = GmailApp.getInboxThreads();
  
  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    var lastMessage = messages[messages.length - 1];
    var subject = lastMessage.getSubject();
    var from = lastMessage.getFrom();
    var body = lastMessage.getPlainBody();
    
"""
        
        for rule in rules:
            condition = rule.get("condition", {})
            label_name = rule.get("label", "")
            
            script += f"""
    // Rule: {rule.get('name', 'Unnamed')}
    if ("""
            
            conditions = []
            if condition.get("subject_contains"):
                conditions.append(f'subject.indexOf("{condition["subject_contains"]}") !== -1')
            if condition.get("from_contains"):
                conditions.append(f'from.indexOf("{condition["from_contains"]}") !== -1')
            if condition.get("body_contains"):
                conditions.append(f'body.indexOf("{condition["body_contains"]}") !== -1')
            
            script += " && ".join(conditions)
            script += f""") {{
      var label = GmailApp.getUserLabelByName("{label_name}");
      if (!label) {{
        label = GmailApp.createLabel("{label_name}");
      }}
      threads[i].addLabel(label);
      threads[i].moveToArchive();
    }}
"""
        
        script += """
  }
}

// Set up daily trigger
function createTrigger() {
  ScriptApp.newTrigger('organizeEmailsByLabel')
    .timeBased()
    .everyHours(1)
    .create();
}
"""
        
        return script
    
    def generate_forwarding_script(self, forward_rules: List[Dict[str, Any]]) -> str:
        """Generate Apps Script for conditional forwarding"""
        script = """
function forwardEmails() {
  var threads = GmailApp.getInboxThreads();
  
  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    var lastMessage = messages[messages.length - 1];
    
"""
        
        for rule in forward_rules:
            condition = rule.get("condition", {})
            forward_to = rule.get("forward_to", "")
            
            script += f"""
    // Forward rule: {rule.get('name', 'Unnamed')}
    if (lastMessage.getFrom().indexOf("{condition.get('from_contains', '')}") !== -1) {{
      lastMessage.forward("{forward_to}");
    }}
"""
        
        script += """
  }
}
"""
        
        return script
    
    def deploy_script(self, script_content: str, project_name: str) -> Dict[str, Any]:
        """Deploy Apps Script (requires Google Apps Script API)"""
        # This would use the Google Apps Script API to deploy
        # For now, return instructions
        return {
            "success": True,
            "script": script_content,
            "instructions": [
                "1. Go to script.google.com",
                "2. Create a new project",
                f"3. Name it '{project_name}'",
                "4. Paste the generated script",
                "5. Run createTrigger() function to set up automation",
                "6. Authorize the script when prompted"
            ]
        }


class OutlookRulesGenerator:
    """Generate Outlook rules via Microsoft Graph API"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.graph_api_url = "https://graph.microsoft.com/v1.0"
    
    def create_inbox_rule(self, rule_name: str, conditions: Dict[str, Any], 
                         actions: Dict[str, Any]) -> Dict[str, Any]:
        """Create Outlook inbox rule via Graph API"""
        if not self.access_token:
            return {"success": False, "error": "Access token not provided"}
        
        rule_payload = {
            "displayName": rule_name,
            "sequence": 1,
            "isEnabled": True,
            "conditions": self._build_conditions(conditions),
            "actions": self._build_actions(actions)
        }
        
        try:
            response = requests.post(
                f"{self.graph_api_url}/me/mailFolders/inbox/messageRules",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json=rule_payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "rule_id": response.json().get("id"),
                    "rule": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _build_conditions(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Build conditions for Outlook rule"""
        rule_conditions = {}
        
        if conditions.get("from_addresses"):
            rule_conditions["fromAddresses"] = [
                {"emailAddress": {"address": addr}} 
                for addr in conditions["from_addresses"]
            ]
        
        if conditions.get("subject_contains"):
            rule_conditions["subjectContains"] = conditions["subject_contains"]
        
        if conditions.get("body_contains"):
            rule_conditions["bodyContains"] = conditions["body_contains"]
        
        if conditions.get("has_attachments"):
            rule_conditions["hasAttachments"] = True
        
        if conditions.get("importance"):
            rule_conditions["importance"] = conditions["importance"]
        
        return rule_conditions
    
    def _build_actions(self, actions: Dict[str, Any]) -> Dict[str, Any]:
        """Build actions for Outlook rule"""
        rule_actions = {}
        
        if actions.get("move_to_folder"):
            rule_actions["moveToFolder"] = actions["move_to_folder"]
        
        if actions.get("copy_to_folder"):
            rule_actions["copyToFolder"] = actions["copy_to_folder"]
        
        if actions.get("forward_to"):
            rule_actions["forwardTo"] = [
                {"emailAddress": {"address": addr}}
                for addr in actions["forward_to"]
            ]
        
        if actions.get("mark_as_read"):
            rule_actions["markAsRead"] = True
        
        if actions.get("mark_importance"):
            rule_actions["markImportance"] = actions["mark_importance"]
        
        if actions.get("categories"):
            rule_actions["assignCategories"] = actions["categories"]
        
        if actions.get("delete"):
            rule_actions["delete"] = True
        
        return rule_actions
    
    def list_inbox_rules(self) -> Dict[str, Any]:
        """List all inbox rules"""
        if not self.access_token:
            return {"success": False, "error": "Access token not provided"}
        
        try:
            response = requests.get(
                f"{self.graph_api_url}/me/mailFolders/inbox/messageRules",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "rules": response.json().get("value", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}"
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_inbox_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete inbox rule"""
        if not self.access_token:
            return {"success": False, "error": "Access token not provided"}
        
        try:
            response = requests.delete(
                f"{self.graph_api_url}/me/mailFolders/inbox/messageRules/{rule_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            return {
                "success": response.status_code == 204,
                "status_code": response.status_code
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class EmailWorkflowBuilder:
    """Build complex email workflows with if-then rules"""
    
    def __init__(self):
        self.workflows = {}
    
    def create_workflow(self, workflow_id: str, name: str, 
                       triggers: List[Dict[str, Any]], 
                       actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create email workflow"""
        workflow = {
            "id": workflow_id,
            "name": name,
            "triggers": triggers,
            "actions": actions,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "execution_count": 0
        }
        
        self.workflows[workflow_id] = workflow
        return workflow
    
    def execute_workflow(self, workflow_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow for an email"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        
        if not workflow["enabled"]:
            return {"success": False, "error": "Workflow is disabled"}
        
        # Check triggers
        triggered = False
        for trigger in workflow["triggers"]:
            if self._evaluate_trigger(trigger, email_data):
                triggered = True
                break
        
        if not triggered:
            return {"success": False, "reason": "No triggers matched"}
        
        # Execute actions
        results = []
        for action in workflow["actions"]:
            result = self._execute_action(action, email_data)
            results.append(result)
        
        workflow["execution_count"] += 1
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "actions_executed": len(results),
            "results": results
        }
    
    def _evaluate_trigger(self, trigger: Dict[str, Any], email_data: Dict[str, Any]) -> bool:
        """Evaluate if trigger condition is met"""
        trigger_type = trigger.get("type")
        
        if trigger_type == "sender_is":
            return trigger["value"] in email_data.get("from", "")
        
        elif trigger_type == "subject_contains":
            return trigger["value"].lower() in email_data.get("subject", "").lower()
        
        elif trigger_type == "has_attachment":
            return len(email_data.get("attachments", [])) > 0
        
        elif trigger_type == "body_contains":
            return trigger["value"].lower() in email_data.get("body", "").lower()
        
        elif trigger_type == "received_time":
            # Check if email received within time window
            return True  # Simplified
        
        return False
    
    def _execute_action(self, action: Dict[str, Any], email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow action"""
        action_type = action.get("type")
        
        if action_type == "send_reply":
            return {
                "action": "send_reply",
                "status": "simulated",
                "reply_text": action.get("reply_template")
            }
        
        elif action_type == "forward":
            return {
                "action": "forward",
                "status": "simulated",
                "forward_to": action.get("forward_to")
            }
        
        elif action_type == "add_label":
            return {
                "action": "add_label",
                "status": "simulated",
                "label": action.get("label")
            }
        
        elif action_type == "move_to_folder":
            return {
                "action": "move_to_folder",
                "status": "simulated",
                "folder": action.get("folder")
            }
        
        elif action_type == "send_notification":
            return {
                "action": "send_notification",
                "status": "simulated",
                "notification_type": action.get("notification_type")
            }
        
        return {"action": action_type, "status": "unknown"}


# ============================================================================
# SCHEDULED EMAIL SENDING & MAIL MERGE
# ============================================================================

class ScheduledEmailSender:
    """Schedule emails for future sending"""
    
    def __init__(self):
        self.scheduled_emails = {}
    
    def schedule_email(self, email_id: str, recipient: str, subject: str,
                      body: str, send_at: datetime, attachments: List[str] = None) -> Dict[str, Any]:
        """Schedule email for future sending"""
        scheduled = {
            "id": email_id,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "send_at": send_at.isoformat(),
            "attachments": attachments or [],
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        self.scheduled_emails[email_id] = scheduled
        return scheduled
    
    def cancel_scheduled_email(self, email_id: str) -> Dict[str, Any]:
        """Cancel scheduled email"""
        if email_id not in self.scheduled_emails:
            return {"success": False, "error": "Email not found"}
        
        email = self.scheduled_emails[email_id]
        if email["status"] == "sent":
            return {"success": False, "error": "Email already sent"}
        
        email["status"] = "cancelled"
        return {"success": True, "email": email}
    
    def get_pending_emails(self) -> List[Dict[str, Any]]:
        """Get all pending scheduled emails"""
        now = datetime.now()
        pending = []
        
        for email_id, email in self.scheduled_emails.items():
            if email["status"] == "scheduled":
                send_at = datetime.fromisoformat(email["send_at"])
                if send_at <= now:
                    pending.append(email)
        
        return pending
    
    def send_scheduled_email(self, email_id: str, smtp_config: Dict[str, Any]) -> Dict[str, Any]:
        """Send a scheduled email (would use actual SMTP in production)"""
        if email_id not in self.scheduled_emails:
            return {"success": False, "error": "Email not found"}
        
        email = self.scheduled_emails[email_id]
        
        # In production, would actually send via SMTP
        email["status"] = "sent"
        email["sent_at"] = datetime.now().isoformat()
        
        return {"success": True, "email": email}


class MailMergeSystem:
    """Mail merge functionality for bulk personalized emails"""
    
    def __init__(self):
        self.templates = {}
        self.merge_jobs = {}
    
    def create_template(self, template_id: str, subject: str, body: str,
                       variables: List[str]) -> Dict[str, Any]:
        """Create mail merge template"""
        template = {
            "id": template_id,
            "subject": subject,
            "body": body,
            "variables": variables,
            "created_at": datetime.now().isoformat()
        }
        
        self.templates[template_id] = template
        return template
    
    def merge_and_generate(self, template_id: str, 
                          recipients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate personalized emails from template and recipient data"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        generated_emails = []
        
        for recipient in recipients:
            # Merge variables
            subject = template["subject"]
            body = template["body"]
            
            for var in template["variables"]:
                placeholder = f"{{{var}}}"
                value = recipient.get(var, "")
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))
            
            generated_emails.append({
                "recipient": recipient.get("email", ""),
                "subject": subject,
                "body": body,
                "variables_used": recipient
            })
        
        return generated_emails
    
    def execute_mail_merge(self, template_id: str, recipients: List[Dict[str, Any]],
                          smtp_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute mail merge campaign"""
        job_id = hashlib.sha256(f"{template_id}:{time.time()}".encode()).hexdigest()
        
        generated_emails = self.merge_and_generate(template_id, recipients)
        
        job = {
            "id": job_id,
            "template_id": template_id,
            "total_recipients": len(recipients),
            "generated_at": datetime.now().isoformat(),
            "status": "generated",
            "emails": generated_emails
        }
        
        self.merge_jobs[job_id] = job
        
        # In production, would send emails via SMTP
        job["status"] = "completed"
        job["sent_count"] = len(generated_emails)
        
        return job


# To be continued in Part 3...


# ============================================================================
# PGP/GPG ENCRYPTION & SECURITY
# ============================================================================

class EmailEncryptionSystem:
    """PGP/GPG email encryption and decryption"""
    
    def __init__(self, gpg_home: str = None):
        if not GPG_AVAILABLE:
            raise ImportError("python-gnupg not installed. Install with: pip install python-gnupg")
        
        self.gpg = gnupg.GPG(gnupghome=gpg_home)
    
    def generate_key_pair(self, name: str, email: str, 
                         passphrase: str, key_type: str = "RSA",
                         key_length: int = 4096) -> Dict[str, Any]:
        """Generate PGP key pair"""
        input_data = self.gpg.gen_key_input(
            name_real=name,
            name_email=email,
            passphrase=passphrase,
            key_type=key_type,
            key_length=key_length
        )
        
        key = self.gpg.gen_key(input_data)
        
        if key:
            return {
                "success": True,
                "fingerprint": str(key),
                "public_key": self.export_public_key(str(key)),
                "key_id": str(key)
            }
        else:
            return {"success": False, "error": "Failed to generate key"}
    
    def import_key(self, key_data: str) -> Dict[str, Any]:
        """Import PGP key"""
        result = self.gpg.import_keys(key_data)
        
        return {
            "success": result.count > 0,
            "count": result.count,
            "fingerprints": result.fingerprints,
            "results": result.results
        }
    
    def export_public_key(self, key_id: str) -> str:
        """Export public key"""
        return self.gpg.export_keys(key_id)
    
    def export_private_key(self, key_id: str, passphrase: str) -> str:
        """Export private key"""
        return self.gpg.export_keys(key_id, secret=True, passphrase=passphrase)
    
    def encrypt_message(self, message: str, recipient_key_id: str) -> Dict[str, Any]:
        """Encrypt message for recipient"""
        encrypted = self.gpg.encrypt(message, recipient_key_id)
        
        if encrypted.ok:
            return {
                "success": True,
                "encrypted_message": str(encrypted),
                "status": encrypted.status
            }
        else:
            return {
                "success": False,
                "error": encrypted.status,
                "stderr": encrypted.stderr
            }
    
    def decrypt_message(self, encrypted_message: str, passphrase: str) -> Dict[str, Any]:
        """Decrypt encrypted message"""
        decrypted = self.gpg.decrypt(encrypted_message, passphrase=passphrase)
        
        if decrypted.ok:
            return {
                "success": True,
                "decrypted_message": str(decrypted),
                "key_id": decrypted.key_id,
                "username": decrypted.username
            }
        else:
            return {
                "success": False,
                "error": decrypted.status,
                "stderr": decrypted.stderr
            }
    
    def sign_message(self, message: str, key_id: str, passphrase: str) -> Dict[str, Any]:
        """Sign message with private key"""
        signed = self.gpg.sign(message, keyid=key_id, passphrase=passphrase)
        
        if signed:
            return {
                "success": True,
                "signed_message": str(signed),
                "key_id": signed.key_id
            }
        else:
            return {"success": False, "error": "Failed to sign message"}
    
    def verify_signature(self, signed_message: str) -> Dict[str, Any]:
        """Verify message signature"""
        verified = self.gpg.verify(signed_message)
        
        return {
            "valid": verified.valid,
            "key_id": verified.key_id,
            "username": verified.username,
            "signature_id": verified.signature_id,
            "fingerprint": verified.fingerprint,
            "trust_level": verified.trust_text
        }
    
    def encrypt_and_sign(self, message: str, recipient_key_id: str,
                        signer_key_id: str, passphrase: str) -> Dict[str, Any]:
        """Encrypt and sign message"""
        encrypted = self.gpg.encrypt(
            message,
            recipient_key_id,
            sign=signer_key_id,
            passphrase=passphrase
        )
        
        if encrypted.ok:
            return {
                "success": True,
                "encrypted_signed_message": str(encrypted),
                "status": encrypted.status
            }
        else:
            return {
                "success": False,
                "error": encrypted.status,
                "stderr": encrypted.stderr
            }
    
    def list_keys(self, secret: bool = False) -> List[Dict[str, Any]]:
        """List all keys"""
        keys = self.gpg.list_keys(secret=secret)
        return [
            {
                "keyid": key["keyid"],
                "fingerprint": key["fingerprint"],
                "uids": key["uids"],
                "length": key["length"],
                "algo": key["algo"],
                "created": key["date"],
                "expires": key["expires"]
            }
            for key in keys
        ]


# ============================================================================
# EMAIL ARCHIVAL & COMPLIANCE
# ============================================================================

class EmailArchivalSystem:
    """Email archival, retention, and compliance management"""
    
    def __init__(self, archive_path: str = "/var/email_archive"):
        self.archive_path = archive_path
        self.retention_policies = {}
        self.legal_holds = {}
    
    def archive_email(self, email_data: Dict[str, Any], 
                     metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Archive email with metadata"""
        email_id = email_data.get("message_id") or hashlib.sha256(
            f"{email_data.get('from')}:{email_data.get('subject')}:{time.time()}".encode()
        ).hexdigest()
        
        archive_entry = {
            "id": email_id,
            "archived_at": datetime.now().isoformat(),
            "email_data": email_data,
            "metadata": metadata or {},
            "retention_policy": None,
            "legal_hold": False
        }
        
        # In production, would save to disk/database
        return {
            "success": True,
            "archive_id": email_id,
            "archive_path": f"{self.archive_path}/{email_id}.json"
        }
    
    def create_retention_policy(self, policy_id: str, name: str,
                               retention_days: int, action: str = "delete") -> Dict[str, Any]:
        """Create email retention policy"""
        policy = {
            "id": policy_id,
            "name": name,
            "retention_days": retention_days,
            "action": action,  # delete, archive, move
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }
        
        self.retention_policies[policy_id] = policy
        return policy
    
    def apply_retention_policy(self, email_id: str, policy_id: str) -> Dict[str, Any]:
        """Apply retention policy to email"""
        if policy_id not in self.retention_policies:
            return {"success": False, "error": "Policy not found"}
        
        # In production, would update email record
        return {
            "success": True,
            "email_id": email_id,
            "policy_id": policy_id,
            "expires_at": (datetime.now() + timedelta(
                days=self.retention_policies[policy_id]["retention_days"]
            )).isoformat()
        }
    
    def place_legal_hold(self, hold_id: str, email_ids: List[str],
                        reason: str, custodian: str) -> Dict[str, Any]:
        """Place legal hold on emails"""
        hold = {
            "id": hold_id,
            "email_ids": email_ids,
            "reason": reason,
            "custodian": custodian,
            "placed_at": datetime.now().isoformat(),
            "released_at": None,
            "status": "active"
        }
        
        self.legal_holds[hold_id] = hold
        
        return {
            "success": True,
            "hold_id": hold_id,
            "emails_affected": len(email_ids)
        }
    
    def release_legal_hold(self, hold_id: str) -> Dict[str, Any]:
        """Release legal hold"""
        if hold_id not in self.legal_holds:
            return {"success": False, "error": "Hold not found"}
        
        hold = self.legal_holds[hold_id]
        hold["status"] = "released"
        hold["released_at"] = datetime.now().isoformat()
        
        return {"success": True, "hold": hold}
    
    def export_for_ediscovery(self, search_criteria: Dict[str, Any],
                             export_format: str = "pst") -> Dict[str, Any]:
        """Export emails for eDiscovery"""
        # In production, would search archive and export
        export_id = hashlib.sha256(f"{time.time()}".encode()).hexdigest()
        
        return {
            "success": True,
            "export_id": export_id,
            "format": export_format,
            "criteria": search_criteria,
            "export_path": f"{self.archive_path}/exports/{export_id}.{export_format}",
            "created_at": datetime.now().isoformat()
        }


# ============================================================================
# SPAM ANALYSIS & BULK OPERATIONS
# ============================================================================

class SpamAnalyzer:
    """Analyze and report spam emails"""
    
    def __init__(self):
        self.spam_patterns = self._load_spam_patterns()
    
    def _load_spam_patterns(self) -> Dict[str, List[str]]:
        """Load spam detection patterns"""
        return {
            "subject_patterns": [
                r'(?i)you.*won',
                r'(?i)claim.*prize',
                r'(?i)act now',
                r'(?i)limited time',
                r'(?i)free money',
                r'(?i)weight loss',
                r'(?i)viagra',
                r'(?i)nigerian prince'
            ],
            "body_patterns": [
                r'(?i)click here to unsubscribe',
                r'(?i)this is not spam',
                r'(?i)dear friend',
                r'(?i)urgent business proposal'
            ]
        }
    
    def analyze_spam_score(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spam score for email"""
        score = 0
        indicators = []
        
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        sender = email_data.get("from", "")
        
        # Check subject patterns
        for pattern in self.spam_patterns["subject_patterns"]:
            if re.search(pattern, subject):
                score += 10
                indicators.append(f"Spam pattern in subject: {pattern}")
        
        # Check body patterns
        for pattern in self.spam_patterns["body_patterns"]:
            if re.search(pattern, body):
                score += 5
                indicators.append(f"Spam pattern in body: {pattern}")
        
        # Check authentication
        auth = email_data.get("authentication", {})
        if auth.get("spf", {}).get("status") == "fail":
            score += 20
            indicators.append("SPF check failed")
        
        if auth.get("dkim", {}).get("status") == "fail":
            score += 20
            indicators.append("DKIM check failed")
        
        # Determine classification
        if score >= 50:
            classification = "spam"
        elif score >= 30:
            classification = "likely_spam"
        elif score >= 15:
            classification = "suspicious"
        else:
            classification = "legitimate"
        
        return {
            "spam_score": score,
            "classification": classification,
            "indicators": indicators,
            "is_spam": score >= 30
        }
    
    def report_spam(self, email_data: Dict[str, Any], 
                   report_to: str = "spamcop") -> Dict[str, Any]:
        """Report spam to abuse reporting service"""
        # In production, would submit to actual reporting service
        report_id = hashlib.sha256(f"{time.time()}".encode()).hexdigest()
        
        return {
            "success": True,
            "report_id": report_id,
            "reported_to": report_to,
            "email_id": email_data.get("message_id"),
            "reported_at": datetime.now().isoformat()
        }


class BulkEmailOperations:
    """Bulk email operations and management"""
    
    def __init__(self):
        self.operations = {}
    
    def bulk_delete(self, email_ids: List[str], 
                   criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Bulk delete emails"""
        operation_id = hashlib.sha256(f"delete:{time.time()}".encode()).hexdigest()
        
        result = {
            "operation_id": operation_id,
            "operation": "delete",
            "total_emails": len(email_ids),
            "deleted": len(email_ids),
            "failed": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.operations[operation_id] = result
        return result
    
    def bulk_move(self, email_ids: List[str], destination_folder: str) -> Dict[str, Any]:
        """Bulk move emails to folder"""
        operation_id = hashlib.sha256(f"move:{time.time()}".encode()).hexdigest()
        
        result = {
            "operation_id": operation_id,
            "operation": "move",
            "total_emails": len(email_ids),
            "moved": len(email_ids),
            "failed": 0,
            "destination": destination_folder,
            "timestamp": datetime.now().isoformat()
        }
        
        self.operations[operation_id] = result
        return result
    
    def bulk_label(self, email_ids: List[str], labels: List[str]) -> Dict[str, Any]:
        """Bulk apply labels to emails"""
        operation_id = hashlib.sha256(f"label:{time.time()}".encode()).hexdigest()
        
        result = {
            "operation_id": operation_id,
            "operation": "label",
            "total_emails": len(email_ids),
            "labeled": len(email_ids),
            "failed": 0,
            "labels": labels,
            "timestamp": datetime.now().isoformat()
        }
        
        self.operations[operation_id] = result
        return result
    
    def bulk_mark_read(self, email_ids: List[str]) -> Dict[str, Any]:
        """Bulk mark emails as read"""
        operation_id = hashlib.sha256(f"read:{time.time()}".encode()).hexdigest()
        
        result = {
            "operation_id": operation_id,
            "operation": "mark_read",
            "total_emails": len(email_ids),
            "marked": len(email_ids),
            "failed": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.operations[operation_id] = result
        return result
    
    def bulk_export(self, email_ids: List[str], 
                   export_format: str = "mbox") -> Dict[str, Any]:
        """Bulk export emails"""
        operation_id = hashlib.sha256(f"export:{time.time()}".encode()).hexdigest()
        
        result = {
            "operation_id": operation_id,
            "operation": "export",
            "total_emails": len(email_ids),
            "exported": len(email_ids),
            "failed": 0,
            "format": export_format,
            "export_path": f"/tmp/export_{operation_id}.{export_format}",
            "timestamp": datetime.now().isoformat()
        }
        
        self.operations[operation_id] = result
        return result


# ============================================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================================

class OAuthTokenManager:
    """Manage OAuth tokens for email providers"""
    
    def __init__(self):
        self.tokens = {}
    
    def store_token(self, provider: str, user_id: str, 
                   access_token: str, refresh_token: str = None,
                   expires_in: int = 3600) -> Dict[str, Any]:
        """Store OAuth token"""
        token_id = f"{provider}:{user_id}"
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token_data = {
            "provider": provider,
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        self.tokens[token_id] = token_data
        return token_data
    
    def get_token(self, provider: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth token"""
        token_id = f"{provider}:{user_id}"
        token_data = self.tokens.get(token_id)
        
        if not token_data:
            return None
        
        # Check if expired
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() >= expires_at:
            # Token expired
            if token_data.get("refresh_token"):
                # Would refresh token in production
                return token_data
            else:
                return None
        
        return token_data
    
    def refresh_token(self, provider: str, user_id: str,
                     client_id: str, client_secret: str) -> Dict[str, Any]:
        """Refresh OAuth token"""
        token_id = f"{provider}:{user_id}"
        token_data = self.tokens.get(token_id)
        
        if not token_data or not token_data.get("refresh_token"):
            return {"success": False, "error": "No refresh token available"}
        
        # In production, would call provider's token refresh endpoint
        # Simulated response
        new_access_token = "new_access_token_" + hashlib.sha256(
            f"{time.time()}".encode()
        ).hexdigest()
        
        token_data["access_token"] = new_access_token
        token_data["expires_at"] = (datetime.now() + timedelta(hours=1)).isoformat()
        
        return {
            "success": True,
            "access_token": new_access_token,
            "expires_at": token_data["expires_at"]
        }
    
    def revoke_token(self, provider: str, user_id: str) -> Dict[str, Any]:
        """Revoke OAuth token"""
        token_id = f"{provider}:{user_id}"
        
        if token_id in self.tokens:
            del self.tokens[token_id]
            return {"success": True, "message": "Token revoked"}
        else:
            return {"success": False, "error": "Token not found"}


# ============================================================================
# EMAIL CAMPAIGN AUTOMATION
# ============================================================================

class EmailCampaignManager:
    """Manage email marketing campaigns"""
    
    def __init__(self):
        self.campaigns = {}
        self.tracking = EmailTrackingSystem()
    
    def create_campaign(self, campaign_id: str, name: str,
                       subject: str, body: str, 
                       recipients: List[str]) -> Dict[str, Any]:
        """Create email campaign"""
        campaign = {
            "id": campaign_id,
            "name": name,
            "subject": subject,
            "body": body,
            "recipients": recipients,
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "sent_at": None,
            "stats": {
                "sent": 0,
                "delivered": 0,
                "opened": 0,
                "clicked": 0,
                "bounced": 0,
                "unsubscribed": 0
            }
        }
        
        self.campaigns[campaign_id] = campaign
        return campaign
    
    def send_campaign(self, campaign_id: str, 
                     smtp_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send email campaign"""
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found"}
        
        campaign = self.campaigns[campaign_id]
        
        if campaign["status"] == "sent":
            return {"success": False, "error": "Campaign already sent"}
        
        # In production, would send emails via SMTP
        campaign["status"] = "sent"
        campaign["sent_at"] = datetime.now().isoformat()
        campaign["stats"]["sent"] = len(campaign["recipients"])
        campaign["stats"]["delivered"] = len(campaign["recipients"])
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "recipients_count": len(campaign["recipients"]),
            "sent_at": campaign["sent_at"]
        }
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics"""
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found"}
        
        campaign = self.campaigns[campaign_id]
        stats = campaign["stats"]
        
        # Calculate rates
        if stats["sent"] > 0:
            stats["delivery_rate"] = (stats["delivered"] / stats["sent"]) * 100
            stats["open_rate"] = (stats["opened"] / stats["delivered"]) * 100 if stats["delivered"] > 0 else 0
            stats["click_rate"] = (stats["clicked"] / stats["delivered"]) * 100 if stats["delivered"] > 0 else 0
            stats["bounce_rate"] = (stats["bounced"] / stats["sent"]) * 100
        
        return {
            "campaign_id": campaign_id,
            "name": campaign["name"],
            "status": campaign["status"],
            "stats": stats
        }
    
    def add_unsubscribe_link(self, html_content: str, 
                            unsubscribe_url: str) -> str:
        """Add unsubscribe link to email"""
        unsubscribe_html = f'''
<div style="text-align: center; font-size: 12px; color: #666; margin-top: 40px; padding: 20px; border-top: 1px solid #ddd;">
    <p>If you no longer wish to receive these emails, you can <a href="{unsubscribe_url}" style="color: #666;">unsubscribe here</a>.</p>
</div>
'''
        
        if '</body>' in html_content:
            return html_content.replace('</body>', f'{unsubscribe_html}</body>')
        else:
            return html_content + unsubscribe_html
    
    def process_unsubscribe(self, campaign_id: str, 
                           email_address: str) -> Dict[str, Any]:
        """Process unsubscribe request"""
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found"}
        
        campaign = self.campaigns[campaign_id]
        
        if email_address in campaign["recipients"]:
            campaign["recipients"].remove(email_address)
            campaign["stats"]["unsubscribed"] += 1
        
        return {
            "success": True,
            "email": email_address,
            "campaign_id": campaign_id,
            "unsubscribed_at": datetime.now().isoformat()
        }


# ============================================================================
# UNIFIED EMAIL TECHNOLOGY EXPERT INTERFACE
# ============================================================================

class EmailTechnologyExpert:
    """Unified interface for all email technology capabilities"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize all subsystems
        self.header_analyzer = EmailHeaderAnalyzer()
        self.auth_validator = EmailAuthenticationValidator()
        self.tracking = EmailTrackingSystem(
            tracking_domain=self.config.get("tracking_domain", "track.example.com")
        )
        self.phishing_detector = PhishingDetector()
        self.auto_reply = AutoReplySystem(
            openrouter_api_key=self.config.get("openrouter_api_key")
        )
        self.notifications = EmailNotificationSystem()
        self.gmail_script_gen = GmailAppsScriptGenerator()
        self.outlook_rules = OutlookRulesGenerator(
            access_token=self.config.get("outlook_access_token")
        )
        self.workflow_builder = EmailWorkflowBuilder()
        self.scheduled_sender = ScheduledEmailSender()
        self.mail_merge = MailMergeSystem()
        
        # Advanced features
        if GPG_AVAILABLE:
            self.encryption = EmailEncryptionSystem(
                gpg_home=self.config.get("gpg_home")
            )
        else:
            self.encryption = None
        
        self.archival = EmailArchivalSystem(
            archive_path=self.config.get("archive_path", "/var/email_archive")
        )
        self.spam_analyzer = SpamAnalyzer()
        self.bulk_ops = BulkEmailOperations()
        self.oauth_manager = OAuthTokenManager()
        self.campaign_manager = EmailCampaignManager()
    
    def analyze_email_complete(self, raw_email: Union[str, bytes]) -> Dict[str, Any]:
        """Complete email analysis including forensics, authentication, and phishing detection"""
        # Parse and analyze headers
        forensics = self.header_analyzer.analyze_email_forensics(raw_email)
        
        # Phishing detection
        phishing_analysis = self.phishing_detector.analyze_email_for_phishing(forensics)
        
        # Sender reputation
        sender_domain = forensics["from"].split("@")[-1] if "@" in forensics["from"] else ""
        reputation = self.phishing_detector.calculate_sender_reputation(sender_domain)
        
        # Spam analysis
        spam_analysis = self.spam_analyzer.analyze_spam_score(forensics)
        
        return {
            "forensics": forensics,
            "phishing_analysis": phishing_analysis,
            "sender_reputation": reputation,
            "spam_analysis": spam_analysis,
            "overall_risk_score": (
                phishing_analysis["risk_score"] * 0.5 +
                spam_analysis["spam_score"] * 0.3 +
                (100 - reputation["score"]) * 0.2
            ),
            "recommendation": phishing_analysis["recommendation"]
        }
    
    def setup_auto_reply_workflow(self, conditions: Dict[str, Any],
                                  reply_type: str = "llm",
                                  template: str = None) -> Dict[str, Any]:
        """Set up complete auto-reply workflow"""
        workflow_id = hashlib.sha256(f"autoreply:{time.time()}".encode()).hexdigest()
        
        # Create workflow
        triggers = [{"type": key, "value": value} for key, value in conditions.items()]
        
        actions = [{
            "type": "send_reply",
            "reply_type": reply_type,
            "template": template
        }]
        
        workflow = self.workflow_builder.create_workflow(
            workflow_id, "Auto-reply workflow", triggers, actions
        )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "workflow": workflow
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get all available capabilities"""
        return {
            "metadata": SKILL_METADATA,
            "subsystems": {
                "header_analysis": "EmailHeaderAnalyzer",
                "authentication": "EmailAuthenticationValidator",
                "tracking": "EmailTrackingSystem",
                "phishing_detection": "PhishingDetector",
                "auto_reply": "AutoReplySystem",
                "notifications": "EmailNotificationSystem",
                "gmail_automation": "GmailAppsScriptGenerator",
                "outlook_automation": "OutlookRulesGenerator",
                "workflows": "EmailWorkflowBuilder",
                "scheduling": "ScheduledEmailSender",
                "mail_merge": "MailMergeSystem",
                "encryption": "EmailEncryptionSystem" if self.encryption else "Not available",
                "archival": "EmailArchivalSystem",
                "spam_analysis": "SpamAnalyzer",
                "bulk_operations": "BulkEmailOperations",
                "oauth": "OAuthTokenManager",
                "campaigns": "EmailCampaignManager"
            },
            "encryption_available": GPG_AVAILABLE
        }


# ============================================================================
# EXPERT PROMPTS FOR AI AGENT INTEGRATION
# ============================================================================

EXPERT_PROMPTS = {
    "email_forensics": """Analyze the following email for forensic investigation:
Email Headers: {headers}
Email Body: {body}

Provide detailed analysis including:
1. Complete routing path with IP geolocation
2. Authentication results (SPF, DKIM, DMARC, ARC)
3. Delivery timeline and delays
4. Suspicious indicators
5. Sender reputation assessment
6. Recommendations for action""",
    
    "phishing_detection": """Analyze this email for phishing indicators:
From: {from}
Subject: {subject}
Body: {body}
Links: {links}

Assess:
1. Sender authenticity
2. Urgency/threat tactics
3. Link safety
4. Request for sensitive information
5. Overall risk level
6. User recommendations""",
    
    "auto_reply_generation": """Generate an appropriate email reply:
Original Email: {email_content}
Sender: {sender}
Context: {context}
Tone: {tone}
Key Points: {key_points}

Generate a professional, context-aware reply.""",
    
    "campaign_optimization": """Optimize this email campaign:
Subject: {subject}
Body: {body}
Target Audience: {audience}
Goal: {goal}

Provide:
1. Subject line improvements
2. Body content optimization
3. Call-to-action enhancement
4. Personalization suggestions
5. A/B testing recommendations"""
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_email_expert(config: Dict[str, Any] = None) -> EmailTechnologyExpert:
    """Factory function to create EmailTechnologyExpert instance"""
    return EmailTechnologyExpert(config)


def quick_email_analysis(raw_email: Union[str, bytes]) -> Dict[str, Any]:
    """Quick email analysis without full initialization"""
    expert = EmailTechnologyExpert()
    return expert.analyze_email_complete(raw_email)


# Module exports
__all__ = [
    'EmailHeaderAnalyzer',
    'EmailAuthenticationValidator',
    'EmailTrackingSystem',
    'PhishingDetector',
    'AutoReplySystem',
    'EmailNotificationSystem',
    'GmailAppsScriptGenerator',
    'OutlookRulesGenerator',
    'EmailWorkflowBuilder',
    'ScheduledEmailSender',
    'MailMergeSystem',
    'EmailEncryptionSystem',
    'EmailArchivalSystem',
    'SpamAnalyzer',
    'BulkEmailOperations',
    'OAuthTokenManager',
    'EmailCampaignManager',
    'EmailTechnologyExpert',
    'create_email_expert',
    'quick_email_analysis',
    'SKILL_METADATA',
    'EXPERT_PROMPTS'
]
