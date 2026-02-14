# Email Technology Expert Skill

This file provides the instructions for the AI agent on how to use the `email_technology_expert.py` skill module.

## 1. Core Concept

The `EmailTechnologyExpert` class is the primary entry point. It provides a unified interface to all email-related functionalities. Always start by instantiating this class:

```python
from skills.email_technology_expert import EmailTechnologyExpert

# Pass optional config, like API keys
config = {
    "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
    "outlook_access_token": os.getenv("MS_GRAPH_ACCESS_TOKEN")
}
expert = EmailTechnologyExpert(config)
```

## 2. Key Capabilities and How to Use Them

### 2.1. Comprehensive Email Analysis

**Use Case:** When you need to investigate a suspicious email, understand its origin, or check for threats.

**Method:** `expert.analyze_email_complete(raw_email)`

This is the most powerful analysis function. It combines forensics, authentication checks, phishing detection, and spam analysis into a single call.

```python
# raw_email should be the full email content as a string or bytes
analysis = expert.analyze_email_complete(raw_email)

# Access different parts of the analysis
risk_score = analysis["phishing_analysis"]["risk_score"]
recommendation = analysis["phishing_analysis"]["recommendation"]
routing_path = analysis["forensics"]["routing_path"]

print(f"Phishing Risk: {risk_score}/100. Recommendation: {recommendation}")
```

### 2.2. Generating Intelligent Replies

**Use Case:** When you need to draft a reply to an email, especially when context is important.

**Method:** `expert.auto_reply.generate_llm_reply(email_content, context)`

This method uses the OpenRouter API to generate human-like responses. Always provide as much context as possible for the best results.

```python
email_body = "Can we schedule a demo for next week?"

context = {
    "sender_name": "Jane Doe",
    "relationship": "Lead",
    "tone": "Professional and accommodating",
    "key_points": ["Offer times on Tuesday and Wednesday", "Ask for their preferred duration"]
}

reply = expert.auto_reply.generate_llm_reply(email_body, context)

if reply["success"]:
    print(reply["reply"])
```

### 2.3. Automating Gmail and Outlook

**Use Case:** When the user wants to automate email organization, forwarding, or replies in their Gmail or Outlook account.

- **For Gmail:** Use `expert.gmail_script_gen` to generate Google Apps Script code. You should then provide this code to the user with instructions to paste it into `script.google.com`.

- **For Outlook:** Use `expert.outlook_rules` to directly create rules via the Microsoft Graph API. This requires a valid OAuth access token for the user's account.

```python
# Example: Generate a Gmail script to label all emails from "newsletter@example.com"

rules = [{
    "name": "Newsletters",
    "condition": {"from_contains": "newsletter@example.com"},
    "label": "Newsletters"
}]

script = expert.gmail_script_gen.generate_label_organizer_script(rules)

# Present the script to the user with deployment instructions.
```

### 2.4. Email Tracking

**Use Case:** When sending an important email and needing to know if it was opened or if links were clicked.

**Method:** `expert.tracking.inject_tracking_into_email(html_content, email_id, recipient)`

This method automatically adds a tracking pixel and replaces links with tracked versions. You must have a `tracking_domain` configured.

```python
html_body = "<h1>Proposal</h1><p>Please review our <a href=\"https://example.com/proposal.pdf\">proposal</a>.</p>"

tracked_html = expert.tracking.inject_tracking_into_email(
    html_content=html_body,
    email_id="proposal_email_01",
    recipient="client@example.com"
)

# Now, send the `tracked_html` as the email body.
```

### 2.5. PGP/GPG Encryption

**Use Case:** When sending or receiving highly sensitive information that requires end-to-end encryption.

**Prerequisites:** The `python-gnupg` library and `gnupg` system package must be installed. The user must have a GPG keypair and have imported the recipient's public key.

**Methods:**
- `expert.encryption.encrypt_message(message, recipient_key_id)`
- `expert.encryption.decrypt_message(encrypted_message, passphrase)`

```python
# Encrypt a message
encrypted = expert.encryption.encrypt_message(
    "This is a secret.",
    "recipient@example.com"
)

if encrypted["success"]:
    # Send the encrypted_message
    pass
```

## 3. General Workflow

1.  **Understand the Goal:** Determine what the user wants to achieve (e.g., analyze a threat, automate a task, send a secure message).
2.  **Select the Right Tool:** Based on the goal, choose the appropriate class from the `EmailTechnologyExpert` instance (e.g., `phishing_detector`, `gmail_script_gen`, `encryption`).
3.  **Gather Inputs:** Collect the necessary information, such as raw email content, user preferences for a reply, or rules for automation.
4.  **Execute the Method:** Call the relevant method from the chosen class.
5.  **Present the Output:** Format the result in a clear and useful way for the user. For example, present analysis reports in a structured format, provide generated code in a code block with instructions, or show a generated reply for approval.

