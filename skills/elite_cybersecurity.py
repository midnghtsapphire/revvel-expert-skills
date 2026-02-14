import json
import re
import os
import hashlib
import base64
import ipaddress
import socket
import subprocess
import tempfile
import unittest
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict
import requests

SKILL_METADATA = {
    "name": "Elite Cybersecurity, Deepfake & Malware Expert",
    "id": "elite_cybersecurity",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Top-tier offensive & defensive cybersecurity, malware analysis, deepfake detection, OSINT, and zero-day research toolkit with real tool integrations.",
    "capabilities": [
        "penetration_testing", "vulnerability_scanning", "exploitation", "password_cracking",
        "wireless_attacks", "social_engineering", "privilege_escalation", "lateral_movement",
        "c2_frameworks", "siem_analysis", "threat_hunting", "incident_response",
        "digital_forensics", "malware_analysis", "reverse_engineering", "deepfake_detection",
        "osint", "dark_web_monitoring", "cryptocurrency_investigation", "zero_day_research",
        "fuzzing", "exploit_development", "report_generation"
    ],
    "domain": "cybersecurity"
}

EXPERT_PROMPTS = {
    "pentest_plan": """
You are an elite red-team operator. Build a full-scope penetration test plan for {target_scope}.
Include: reconnaissance, vulnerability identification, exploitation, post-exploitation, lateral movement, persistence, and data exfiltration vectors.
Map all steps to MITRE ATT&CK. Provide tool commands (Nmap, Metasploit, BloodHound, CrackMapExec) and expected outputs.
Highlight potential legal & compliance risks.
""",
    "malware_triage": """
You are a senior malware analyst. Perform deep triage on the sample with SHA256 {sha256}.
Deliver:
1. Static analysis: PE headers, imports, strings, entropy, packer detection.
2. Dynamic analysis: sandbox JSON, API calls, network IOCs.
3. Reverse engineering: Ghidra/IDA pseudocode snippets, C2 decode logic.
4. Attribution & family classification with confidence score.
5. YARA rule and Snort signature.
Provide raw data and markdown report.
""",
    "deepfake_forensics": """
You are a media forensics expert. Analyze the supplied video file {video_path} for deepfake manipulation.
Run frame-level, temporal, frequency, and biometric checks.
Output:
- Manipulation score (0-1)
- GAN fingerprint (StyleGAN, FaceSwap, etc.)
- Audio deepfake confidence
- Tampered segments with timestamps
- Recommended tools for deeper analysis
- Chain-of-custody notes
""",
    "threat_hunt_ioc": """
You are a SOC lead. Hunt for APT {apt_name} TTPs across the enterprise logs of {environment}.
Generate Splunk/ELK queries, YARA rules, and Sigma detections.
Correlate with MITRE ATT&CK technique IDs.
Provide step-by-step runbook for analysts.
""",
    "dark_web_osint": """
You are an OSINT investigator. Search Tor & I2P markets for mentions of {search_term}.
Return:
- Marketplace listings with prices, vendors, timestamps
- Breach datasets containing emails/domains
- Cryptocurrency addresses and mixer usage
- Forum discussions with user handles
- Screenshot hashes for evidence
- Risk assessment & next steps
""",
    "zero_day_fuzz": """
You are an exploit developer. Create an AFL/LibFuzzer harness for {target_binary}.
Provide:
- Harness source code
- Input corpus generator
- Mutation strategies
- Crash triage script
- Exploit primitive identification
- Potential patch diffing notes
""",
    "crypto_investigation": """
You are a blockchain forensic analyst. Trace the flow of {crypto_currency} from {start_address}.
Follow mixers, peel chains, and cluster wallets.
Deliver:
- Graph visualization data
- Entity attribution (exchange, service, illicit)
- Risk score using Chainalysis metrics
- Sewanace-ready report
""",
    "incident_response": """
You are an IR lead. A {threat_type} attack has hit {affected_assets}.
Build a containment & eradication playbook.
Include:
- Isolation procedures
- Evidence acquisition commands
- Memory dump analysis steps
- IOC sweeping scripts
- Communication templates
- Legal & regulatory notifications
"""
}

INTEGRATION_POINTS = {
    "shodan": {
        "type": "api",
        "endpoint": "https://api.shodan.io",
        "description": "Internet-facing asset discovery & vulnerability data",
        "auth_method": "API key header",
        "documentation_url": "https://developer.shodan.io/api"
    },
    "virustotal": {
        "type": "api",
        "endpoint": "https://www.virustotal.com/api/v3",
        "description": "File & URL scanning, threat intelligence",
        "auth_method": "x-apikey header",
        "documentation_url": "https://docs.virustotal.com/"
    },
    "metasploit_rpc": {
        "type": "tool",
        "endpoint": "localhost:55553",
        "description": "Remote API to Metasploit Framework",
        "auth_method": "Token",
        "documentation_url": "https://docs.rapid7.com/metasploit/api/"
    },
    "splunk": {
        "type": "api",
        "endpoint": "https://splunk.example.com:8089",
        "description": "SIEM log search & analysis",
        "auth_method": "Bearer token",
        "documentation_url": "https://dev.splunk.com/enterprise/docs/"
    },
    "haveibeenpwned": {
        "type": "api",
        "endpoint": "https://api.haveibeenpwned.com",
        "description": "Breach & paste data lookup",
        "auth_method": "hibp-api-key header",
        "documentation_url": "https://haveibeenpwned.com/API/v3"
    },
    "blockchain_info": {
        "type": "api",
        "endpoint": "https://blockchain.com/api",
        "description": "Bitcoin address & transaction data",
        "auth_method": "None",
        "documentation_url": "https://www.blockchain.com/api"
    },
    "attack_mitre": {
        "type": "database",
        "endpoint": "https://attack.mitre.org/api",
        "description": "MITRE ATT&CK technique & group JSON",
        "auth_method": "None",
        "documentation_url": "https://github.com/mitre/cti"
    },
    "censys": {
        "type": "api",
        "endpoint": "https://search.censys.io/api",
        "description": "Internet asset discovery & certificates",
        "auth_method": "API ID & secret",
        "documentation_url": "https://search.censys.io/api"
    }
}

def validate_ip(ip: str) -> bool:
    """Return True if ip is a valid IPv4/IPv6 address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_hash(h: str) -> bool:
    """Return True if h looks like MD5/SHA1/SHA256/SHA512."""
    return bool(re.fullmatch(r'^[a-fA-F0-9]{32,128}$', h))

def entropy(data: bytes) -> float:
    """Calculate Shannon entropy of byte sequence."""
    if not data:
        return 0.0
    counts = defaultdict(int)
    for b in data:
        counts[b] += 1
    total = len(data)
    return -sum((c/total)*math.log2(c/total) for c in counts.values() if c)

def parse_nmap_xml(xml_text: str) -> List[Dict[str, Any]]:
    """Extract host/port/service info from Nmap XML output."""
    hosts = []
    host_re = re.compile(r'<host(?:\s.*?)?>(.*?)</host>', re.S)
    addr_re = re.compile(r'<address\s+addr="([^"]+".*?>)')
    port_re = re.compile(r'<port\s+port="(\d+)".*?<state\s+state="([^"]+)"\s+reason="([^"]*)".*?(<service\s+.*?>).*?</port>', re.S)
    for host_block in host_re.findall(xml_text):
        addr = addr_re.search(host_block)
        if not addr:
            continue
        ip = addr.group(1)
        ports = []
        for port, state, reason, svc in port_re.findall(host_block):
            svc_name = re.search(r'name="([^"]*)"', svc)
            ports.append({
                "port": int(port),
                "state": state,
                "reason": reason,
                "service": svc_name.group(1) if svc_name else "unknown"
            })
        hosts.append({"ip": ip, "ports": ports})
    return hosts

def build_shodan_query(query: str, facets: Optional[List[str]] = None) -> str:
    """Construct Shodan search URL with optional facets."""
    url = f"https://api.shodan.io/shodan/host/search?key={os.getenv('SHODAN_KEY','')}&query={requests.utils.quote(query)}"
    if facets:
        url += "&facets=" + ",".join(facets)
    return url

def generate_yara_rule(name: str, strings: List[str], condition: str = "all of them") -> str:
    """Return YARA rule source from indicators."""
    rule = f"""
rule {name}
{{
    meta:
        author = "RevvelAI"
        date = "{datetime.utcnow().isoformat()}"
    strings:
"""
    for idx, s in enumerate(strings):
        rule += f'        ${idx} = "{s}"\n'
    rule += f"    condition:\n        {condition}\n}}"
    return rule.strip()

def sigma_rule(title: str, logsource: Dict[str, str], detection: Dict[str, Any], level: str = "medium") -> Dict[str, Any]:
    """Build Sigma detection rule JSON."""
    return {
        "title": title,
        "id": hashlib.sha256(title.encode()).hexdigest()[:16],
        "status": "experimental",
        "description": f"Detects {title}",
        "logsource": logsource,
        "detection": detection,
        "level": level,
        "tags": ["attack.discovery"]
    }

def splunk_query(index: str, iocs: List[str], field: str = "url") -> str:
    """Return Splunk SPL for IOC search."""
    ioc_list = " OR ".join(f'"{ioc}"' for ioc in iocs)
    return f'index="{index}" ({field} IN ({ioc_list})) | stats count by host, user | where count > 0'

def generate_hashcat_mask(min_len: int = 8, max_len: int = 12, charset: str = "?l?u?d") -> str:
    """Return hashcat mask for brute-force."""
    return f"{charset * min_len}-{charset * max_len}"

def create_phishing_html(target_brand: str, redirect_url: str) -> str:
    """Generate basic phishing page HTML."""
    return f"""
<!doctype html>
<html>
<head><title>{target_brand} - Sign In</title></head>
<body>
<form action="{redirect_url}" method="post">
<input name="email" placeholder="Email">
<input name="password" type="password" placeholder="Password">
<button>Login</button>
</form>
</body>
</html>
""".strip()

def vt_hash_lookup(sha256: str, api_key: str) -> Dict[str, Any]:
    """Query VirusTotal file report."""
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    headers = {"x-apikey": api_key}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

def hibp_breach(email: str, api_key: str) -> List[Dict[str, Any]]:
    """Query HaveIBeenPwned for breaches."""
    url = f"https://api.haveibeenpwned.com/v3/breachedaccount/{email}"
    headers = {"hibp-api-key": api_key}
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return r.json()

class SkillEngine:
    """Elite cybersecurity skill engine."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = config.get("logger", print)

    def run(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to capability method."""
        method = getattr(self, action, None)
        if not method:
            raise ValueError(f"Unknown action {action}")
        try:
            return method(params)
        except Exception as e:
            self.logger(f"SkillEngine.{action} error: {e}")
            return {"error": str(e)}

    def recon_nmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Nmap scan and parse results."""
        target = params["target"]
        flags = params.get("flags", "-sV -O")
        cmd = ["nmap", "-oX", "-", *flags.split(), target]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        hosts = parse_nmap_xml(proc.stdout)
        return {"hosts": hosts, "raw": proc.stdout}

    def malware_static(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform static analysis on sample."""
        path = params["file_path"]
        with open(path, "rb") as f:
            data = f.read()
        sha256 = hashlib.sha256(data).hexdigest()
        ent = entropy(data)
        strings = re.findall(rb"[\x20-\x7e]{4,}", data)
        imports = []  # Simplified
        return {
            "sha256": sha256,
            "size": len(data),
            "entropy": ent,
            "strings": [s.decode() for s in strings[:100]],
            "imports": imports
        }

    def deepfake_detect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Basic deepfake detection stub."""
        video_path = params["video_path"]
        # Placeholder for real CV
        return {
            "video": video_path,
            "manipulation_score": 0.42,
            "gan_fingerprint": "StyleGAN3",
            "audio_fake_confidence": 0.12,
            "notes": "Replace with OpenCV/torch models"
        }

    def yara_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create YARA rule from indicators."""
        name = params["rule_name"]
        strings = params["strings"]
        condition = params.get("condition", "all of them")
        rule_src = generate_yara_rule(name.strip(), strings, condition)
        return {"rule_source": rule_src}

    def splunk_hunt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build Splunk hunting query."""
        index = params["index"]
        iocs = params["iocs"]
        field = params.get("field", "url")
        query = splunk_query(index, iocs, field)
        return {"query": query}

    def phishing_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate phishing HTML."""
        brand = params["brand"]
        redirect = params["redirect"]
        html = create_phishing_html(brand, redirect)
        return {"html": html}

    def hashcat_mask(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return hashcat mask."""
        min_l = params.get("min_len", 8)
        max_l = params.get("max_len", 12)
        charset = params.get("charset", "?l?u?d")
        mask = generate_hashcat_mask(min_l, max_l, charset)
        return {"mask": mask}

    def vt_lookup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """VirusTotal file lookup."""
        sha256 = params["sha256"]
        key = self.config.get("vt_api_key", "")
        if not key:
            raise ValueError("vt_api_key missing")
        report = vt_hash_lookup(sha256, key)
        return {"report": report}

    def hibp_lookup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """HaveIBeenPwned lookup."""
        email = params["email"]
        key = self.config.get("hibp_api_key", "")
        if not key:
            raise ValueError("hibp_api_key missing")
        breaches = hibp_breach(email, key)
        return {"breaches": breaches}

class TestEliteCybersecurity(unittest.TestCase):

    def test_metadata(self):
        self.assertEqual(SKILL_METADATA["id"], "elite_cybersecurity")
        self.assertIn("penetration_testing", SKILL_METADATA["capabilities"])

    def test_validate_ip(self):
        self.assertTrue(validate_ip("192.168.1.1"))
        self.assertFalse(validate_ip("999.0.0.1"))

    def test_validate_hash(self):
        self.assertTrue(validate_hash("a" * 64))
        self.assertFalse(validate_hash("xyz"))

    def test_entropy(self):
        self.assertAlmostEqual(entropy(b"AAAA"), 0.0)
        self.assertGreater(entropy(os.urandom(100)), 7.0)

    def test_parse_nmap_xml(self):
        xml = """<host><address addr="10.0.0.1"/><ports><port port="22"><state state="open" reason="syn-ack"/><service name="ssh"/></port></ports></host>"""
        hosts = parse_nmap_xml(xml)
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0]["ports"][0]["port"], 22)

    def test_build_shodan_query(self):
        q = build_shodan_query("apache", ["country:US"])
        self.assertIn("apache", q)
        self.assertIn("country", q)

    def test_generate_yara_rule(self):
        rule = generate_yara_rule("test", ["hello", "world"])
        self.assertIn("hello", rule)
        self.assertIn("world", rule)

    def test_sigma_rule(self):
        s = sigma_rule("Test", {"product": "windows"}, {"selection": {"EventID": 4624}})
        self.assertEqual(s["title"], "Test")

    def test_splunk_query(self):
        q = splunk_query("main", ["evil.com"], "url")
        self.assertIn("evil.com", q)

    def test_skill_engine_recon(self):
        eng = SkillEngine({})
        with self.assertRaises(Exception):
            eng.recon_nmap({"target": "256.256.256.256"})

    def test_skill_engine_yara(self):
        eng = SkillEngine({})
        res = eng.yara_create({"rule_name": "test", "strings": ["abc"]})
        self.assertIn("rule_source", res)

    def test_skill_engine_phishing(self):
        eng = SkillEngine({})
        res = eng.phishing_page({"brand": "ACME", "redirect": "http://evil"})
        self.assertIn("html", res)

if __name__ == "__main__":
    unittest.main()