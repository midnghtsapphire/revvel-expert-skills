# Email Technology Expert Skill

**Version:** 2.0.0  
**Author:** Revvel AI Engine

## Overview

The **Email Technology Expert** is a comprehensive, cutting-edge Python skill module designed to provide a full suite of tools for advanced email analysis, automation, security, and management. It empowers AI agents with the capabilities to trace email origins, detect phishing threats, generate intelligent replies, automate workflows across major email providers, and handle advanced features like encryption and compliance.

This skill is built to be robust, modular, and production-ready, offering a unified interface to a wide array of complex email-related tasks. It integrates with external services for IP geolocation and LLM-powered text generation, making it a powerful tool for developers, security analysts, and marketing professionals.

## Features

This skill module is organized into a collection of powerful, single-responsibility classes. Below is a summary of the key features and the classes that provide them.

| Feature Category              | Key Capabilities                                                                                                | Primary Class(es)                                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Email Tracing & Forensics** | Full header analysis, routing path tracing, IP extraction and geolocation, delivery timeline analysis.          | `EmailHeaderAnalyzer`                                                                                         |
| **Authentication & Security** | SPF, DKIM, DMARC, and ARC record validation and analysis.                                                       | `EmailAuthenticationValidator`                                                                                |
| **Threat Detection**          | Advanced phishing detection, sender reputation scoring, and spam analysis based on content and metadata.        | `PhishingDetector`, `SpamAnalyzer`                                                                            |
| **Email Tracking**            | Generation and monitoring of tracking pixels (open tracking) and tracked links (click tracking).                | `EmailTrackingSystem`                                                                                         |
| **Intelligent Auto-Reply**    | Context-aware, LLM-powered smart replies (via OpenRouter), template-based responses, and rule-based automation. | `AutoReplySystem`                                                                                             |
| **Notification System**       | Real-time alerts for VIP senders, keyword triggers, and deadline detection.                                     | `EmailNotificationSystem`                                                                                     |
| **In-App Programming**        | Automated generation of scripts and rules for Gmail (Apps Script) and Outlook (Microsoft Graph).              | `GmailAppsScriptGenerator`, `OutlookRulesGenerator`                                                           |
| **Workflow Automation**       | A flexible if-then rule engine to build and execute complex, multi-step email processing workflows.           | `EmailWorkflowBuilder`                                                                                        |
| **Scheduling & Campaigns**    | Scheduled email sending, mail merge for personalized bulk email, and full email campaign management.            | `ScheduledEmailSender`, `MailMergeSystem`, `EmailCampaignManager`                                             |
| **Encryption**                | PGP/GPG key generation, encryption, decryption, signing, and verification of messages.                        | `EmailEncryptionSystem`                                                                                       |
| **Compliance & Archival**     | Email archival, retention policy management, and legal hold capabilities for eDiscovery.                        | `EmailArchivalSystem`                                                                                         |
| **Bulk Operations**           | Perform bulk operations like delete, move, label, and mark-as-read on large sets of emails.                     | `BulkEmailOperations`                                                                                         |
| **API Integration**           | Built-in support for managing OAuth tokens for various email providers.                                         | `OAuthTokenManager`                                                                                           |

## Installation

This skill module has a few external dependencies that need to be installed.

```bash
sudo pip3 install python-gnupg dnspython geoip2 requests
```

For the PGP/GPG encryption features, you must also have GnuPG installed on the system:

```bash
sudo apt-get update && sudo apt-get install -y gnupg
```

## Quick Start: Unified Interface

The `EmailTechnologyExpert` class provides a unified interface to all the skill's capabilities. This is the recommended way to use the module.

```python
from skills.email_technology_expert import EmailTechnologyExpert

# Initialize the expert with optional configuration
config = {
    "openrouter_api_key": "YOUR_OPENROUTER_KEY",
    "tracking_domain": "my.tracker.com"
}
expert = EmailTechnologyExpert(config)

# --- Example 1: Perform a complete analysis of a raw email ---
with open("sample_email.eml", "rb") as f:
    raw_email = f.read()

analysis_result = expert.analyze_email_complete(raw_email)

print("--- Forensic Analysis ---")
print(f"Origin IP: {analysis_result["forensics"]["ip_addresses"]}")
print(f"Delivery Time: {analysis_result["forensics"]["delivery_time_seconds"]}s")

print("\n--- Phishing Analysis ---")
print(f"Risk Score: {analysis_result["phishing_analysis"]["risk_score"]}")
print(f"Recommendation: {analysis_result["phishing_analysis"]["recommendation"]}")
```

## Usage Examples

Below are examples demonstrating how to use some of the key classes directly.

### 1. Email Tracing and Forensics

Use `EmailHeaderAnalyzer` to trace an email's path and extract forensic data.

```python
from skills.email_technology_expert import EmailHeaderAnalyzer

analyzer = EmailHeaderAnalyzer()

with open("suspicious_email.eml", "r") as f:
    raw_email = f.read()

# Perform a full forensic analysis
forensics = analyzer.analyze_email_forensics(raw_email)

# Print the routing path
for hop in forensics["routing_path"]:
    print(f"Hop {hop["hop_number"]}: From {hop["from_ip"]} by {hop["by_domain"]}")

# Get geolocation of the first public IP
if forensics["ip_addresses"]:
    geo_info = analyzer.geolocate_ip(forensics["ip_addresses"][0])
    print(f"Origin Geolocation: {geo_info.get("city")}, {geo_info.get("country")}")
```

### 2. Phishing Detection

Use `PhishingDetector` to assess the threat level of an email.

```python
from skills.email_technology_expert import PhishingDetector, EmailHeaderAnalyzer

# First, parse the email to get structured data
analyzer = EmailHeaderAnalyzer()
with open("phishing_email.eml", "r") as f:
    email_data = analyzer.parse_email_headers(f.read())

detector = PhishingDetector()
phishing_report = detector.analyze_email_for_phishing(email_data)

print(f"Risk Score: {phishing_report["risk_score"]}")
print(f"Is Likely Phishing: {phishing_report["is_likely_phishing"]}")
print("Risk Factors:")
for factor in phishing_report["risk_factors"]:
    print(f"- {factor}")
```

### 3. Generating an LLM-Powered Auto-Reply

Use `AutoReplySystem` to generate smart replies using the OpenRouter API.

```python
from skills.email_technology_expert import AutoReplySystem

# Make sure OPENROUTER_API_KEY is set as an environment variable
auto_reply_system = AutoReplySystem()

email_content = "Hi, I was wondering if you have any availability for a meeting next week?"

# Add context for a more tailored response
context = {
    "sender_name": "John Doe",
    "relationship": "Potential Client",
    "tone": "Enthusiastic and helpful",
    "key_points": ["Confirm availability on Tuesday and Thursday afternoons", "Suggest a 30-minute call"]
}

llm_reply = auto_reply_system.generate_llm_reply(email_content, context)

if llm_reply["success"]:
    print("Generated Reply:")
    print(llm_reply["reply"])
```

### 4. Generating Gmail Automation Scripts

Use `GmailAppsScriptGenerator` to create Google Apps Script code for automating Gmail tasks.

```python
from skills.email_technology_expert import GmailAppsScriptGenerator

script_generator = GmailAppsScriptGenerator()

# Define rules for organizing emails
rules = [
    {
        "name": "Invoices",
        "condition": {"subject_contains": "[Invoice]"},
        "label": "Finances/Invoices"
    },
    {
        "name": "Project Updates",
        "condition": {"from_contains": "project-updates@company.com"},
        "label": "Projects/Updates"
    }
]

# Generate the script
apps_script_code = script_generator.generate_label_organizer_script(rules)

print("--- Gmail Apps Script for Organization ---")
print(apps_script_code)

# You can now deploy this script at script.google.com
```

### 5. Encrypting a Message with PGP/GPG

Use `EmailEncryptionSystem` to perform PGP encryption. Requires `python-gnupg` and GnuPG to be installed.

```python
from skills.email_technology_expert import EmailEncryptionSystem

# This assumes you have GPG installed and a gpg_home directory
# and have imported the recipient's public key.
encryption_system = EmailEncryptionSystem(gpg_home="/home/ubuntu/.gnupg")

recipient_key_id = "RECIPIENT_FINGERPRINT_OR_EMAIL"
message = "This is a top secret message."

encrypted_result = encryption_system.encrypt_message(message, recipient_key_id)

if encrypted_result["success"]:
    print("--- Encrypted PGP Message ---")
    print(encrypted_result["encrypted_message"])
```

## Running Tests

A comprehensive test suite is included to ensure the reliability and correctness of all components. To run the tests, navigate to the root directory of the `revvel-expert-skills` repository and run:

```bash
python3 -m unittest tests/test_email_technology_expert.py
```

This will execute all 56 unit tests, covering every class and major function in the module.
