#!/usr/bin/env python3
"""
Revvel Expert Skills Generator — Uses Kimo (kimi-k2) via OpenRouter
to generate 10 custom expert-level skills.
"""
import os
import json
import time
import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "moonshotai/kimi-k2"

SKILLS = [
    {
        "id": "dna_forensics",
        "name": "DNA Forensics Scientist",
        "description": "DNA analysis, CODIS database queries, forensic genetics, paternity/maternity testing, degraded sample analysis, touch DNA, genealogical DNA for cold cases, mitochondrial DNA analysis",
    },
    {
        "id": "caselaw_expert",
        "name": "Caselaw Expert",
        "description": "Case citation analysis, precedent research, case law comparison, jurisdiction-specific rulings, appellate analysis, constitutional law interpretation, landmark case identification",
    },
    {
        "id": "legal_brief_writing",
        "name": "Legal Brief Writing",
        "description": "Motion drafting, appellate briefs, memoranda of law, legal argument construction, citation formatting (Bluebook), persuasive writing techniques, statement of facts, issue spotting",
    },
    {
        "id": "lexisnexis_integration",
        "name": "LexisNexis Integration",
        "description": "Legal research automation, Shepard's citation checking, case law database queries, statutory research, regulatory compliance research, legal analytics",
    },
    {
        "id": "government_resources",
        "name": "Presidential/Government Resources",
        "description": "Executive orders database, federal register analysis, congressional records, FOIA request automation, government grants research (grants.gov), federal court records (PACER), census data analysis, federal budget analysis",
    },
    {
        "id": "expert_witness",
        "name": "Expert Witness",
        "description": "Expert testimony preparation, Daubert standard compliance, report writing, deposition preparation, cross-examination preparation",
    },
    {
        "id": "patent_ip",
        "name": "Patent & IP",
        "description": "Patent search (USPTO), prior art analysis, patent claim drafting, trademark search, copyright registration, IP portfolio management",
    },
    {
        "id": "victim_advocacy",
        "name": "Victim Advocacy",
        "description": "Victim impact statements, VAWA compliance, trafficking victim resources, crime victim compensation, protective order assistance, victim timeline reconstruction",
    },
    {
        "id": "forensic_accounting",
        "name": "Forensic Accounting",
        "description": "Financial fraud detection, asset tracing, money laundering patterns, tax fraud analysis, cryptocurrency tracing, Benford's law analysis",
    },
    {
        "id": "cold_case_analysis",
        "name": "Cold Case Analysis",
        "description": "Evidence re-examination, witness re-interview strategies, DNA genealogy matching, digital forensics for historical data, timeline reconstruction, pattern analysis across cases",
    },
    {
        "id": "satellite_remote_sensing",
        "name": "Satellite & Remote Sensing",
        "description": "Satellite imagery analysis, Sentinel/Landsat data access, multispectral analysis, change detection, vegetation indices (NDVI), urban growth monitoring, disaster assessment, free satellite data sources (NASA Earthdata, USGS EarthExplorer, Copernicus Open Access Hub)",
    },
    {
        "id": "drone_operator",
        "name": "Drone Operator & Programming",
        "description": "UAV flight planning, autonomous mission programming, DJI SDK integration, MAVLink protocol, ArduPilot/PX4 programming, photogrammetry processing, 3D mapping, Part 107 compliance, waypoint navigation, obstacle avoidance algorithms",
    },
    {
        "id": "lidar_expert",
        "name": "LiDAR Expert",
        "description": "Point cloud processing, terrain modeling, building extraction, vegetation analysis, flood modeling, LiDAR classification, free LiDAR data (USGS 3DEP, OpenTopography), CloudCompare integration, LAS/LAZ file processing, DEM/DSM generation",
    },
    {
        "id": "government_gis",
        "name": "Government Topography & GIS Resources",
        "description": "USGS National Map, NOAA coastal data, FEMA flood maps, Census TIGER data, BLM land records, National Wetlands Inventory, historical aerial photography, soil surveys (NRCS), geological surveys, free GIS data portals (data.gov, state GIS clearinghouses)",
    },
    {
        "id": "historical_research",
        "name": "Historical Research & Archives",
        "description": "National Archives (NARA) access, Library of Congress digital collections, historical newspaper archives (Chronicling America), genealogy records, military service records, immigration records, land patent records, historical census data, Sanborn fire insurance maps",
    },
    {
        "id": "anti_aging",
        "name": "Anti-Aging Research & Formulations",
        "description": "Longevity research databases, NAD+ precursors, senolytics, telomere biology, epigenetic clocks, caloric restriction mimetics, peptide therapy research, stem cell research, clinical trial databases (ClinicalTrials.gov), supplement formulation, skin aging reversal compounds, mitochondrial support",
    },
    {
        "id": "neurodegenerative",
        "name": "Neurodegenerative Disease Formulations",
        "description": "Parkinson's disease research (dopamine pathway, LRRK2, alpha-synuclein), Alzheimer's research (amyloid-beta, tau protein, APOE4), experimental treatments, neuroprotective compounds, clinical trial matching, drug interaction analysis, biomarker tracking, lifestyle intervention protocols",
    },
    {
        "id": "glaucoma_ophthalmology",
        "name": "Glaucoma & Ophthalmology",
        "description": "Intraocular pressure management, optic nerve analysis, visual field testing interpretation, treatment protocols, neuroprotective eye treatments, emerging therapies (ROCK inhibitors, gene therapy), clinical trial databases, patient monitoring systems",
    },
    {
        "id": "cardiovascular",
        "name": "Cardiovascular Disease Research",
        "description": "Heart disease risk modeling, lipid panel analysis, cardiac biomarkers, statin alternatives, emerging therapies (PCSK9 inhibitors, RNA therapeutics), lifestyle intervention protocols, cardiac imaging analysis, arrhythmia detection algorithms, blood pressure optimization",
    },
    {
        "id": "mechanical_engineering",
        "name": "Mechanical Engineering & Materials Science Expert",
        "description": "Material properties databases, stress/strain analysis, fatigue life prediction, composite materials design, metallurgy analysis, FEA (Finite Element Analysis) integration, material selection algorithms (Ashby charts), corrosion analysis, thermal analysis, manufacturing process selection, tolerance stack-up analysis, GD&T interpretation, ASME/ISO standards compliance, failure mode analysis (FMEA), weld analysis, material testing protocols (tensile, hardness, impact), 3D printing material optimization, aerospace materials, automotive materials, biocompatible materials for medical devices",
    },
    {
        "id": "gpr_body_detection",
        "name": "Ground-Penetrating Radar / Microwave Body Detection System",
        "description": "Forensic GPR system for detecting human remains in concrete/underground. Microwave/GPR signal processing, dielectric contrast detection (human tissue vs concrete/soil), frequency optimization (200MHz-2GHz), B-scan/C-scan image generation, anomaly classification (body vs rebar vs void vs pipe), depth estimation, integration with GSSI/Mala/Sensors & Software hardware APIs, 2D/3D visualization, forensic report generation, GPS coordinate integration, historical case database, ML classification training data, chain of custody documentation, forensic evidence export formats",
    },
    {
        "id": "medical_doctor",
        "name": "Medical Doctor / Physician Expert",
        "description": "Full diagnostic reasoning engine, differential diagnosis generator, ICD-10/ICD-11 code lookup, CPT code analysis, drug interaction checker (FDA database), lab result interpretation (CBC, CMP, lipid panels, thyroid, hormones, tumor markers), radiology report interpretation, pathology report analysis, medical record review, treatment protocol databases, clinical practice guidelines (NICE, AHA, ACS, NCCN), pharmacology reference (dosing, contraindications, black box warnings), anatomy reference, surgical procedure database, medical terminology decoder, patient history analysis, vital signs trending, BMI/GFR/MELD calculators, evidence-based medicine search (PubMed, Cochrane), telemedicine protocols",
    },
    {
        "id": "medical_expert_witness",
        "name": "Medical Expert Witness",
        "description": "Daubert/Frye standard compliance for medical testimony, standard of care analysis, medical malpractice case evaluation, causation analysis (but-for, substantial factor), damages assessment (economic/non-economic), life care plan creation, independent medical examination (IME) report writing, deposition preparation for medical cases, medical record chronology builder, medical literature review for litigation, rebuttal report writing, jury-friendly medical explanation generator, case merit screening, statute of limitations analysis by jurisdiction, informed consent analysis, medical board standards reference",
    },
    {
        "id": "precog_analysis",
        "name": "Precognitive Analysis Tool (PRECOG)",
        "description": "Comprehensive predictive intelligence platform. Crime pattern prediction (hotspot analysis, serial offender modeling), behavioral pattern analysis (digital footprint, social media sentiment, communication patterns), financial anomaly prediction (fraud detection, market signals, unusual transactions), health outcome prediction (disease progression, risk factors, treatment response), legal outcome prediction (case probability, judge/jury modeling, settlement estimation). Pattern recognition: cross-domain correlation, temporal detection, network analysis (relationship/influence/communication/money flow), geospatial patterns, anomaly detection. Threat assessment: risk scoring, early warning system, escalation prediction, vulnerability assessment. Data fusion: multi-source integration, entity resolution, timeline reconstruction, evidence chain building, confidence scoring. Reporting: intelligence briefings, threat assessments, pattern visualizations (network graphs, heat maps, timelines), probability dashboards, alert management, chain of evidence. ML models, statistical analysis, heuristic rules. Palantir-level intelligence platform.",
    },
    {
        "id": "advanced_manufacturing",
        "name": "Expert 3D Printing & Advanced Manufacturing",
        "description": "FDM/SLA/SLS/DLP/DMLS printing optimization, G-code generation and modification, multi-material printing, injection mold design (tooling, gating, runner systems, cooling channels, draft angles, shrinkage compensation), blow molding, rotational molding, compression molding, thermoforming, CNC integration, mold flow simulation, rapid prototyping to production pipeline, print farm management, material testing for 3D printed parts, post-processing techniques (annealing, vapor smoothing, CNC finishing), topology optimization, generative design, DfAM (Design for Additive Manufacturing), cost estimation for manufacturing runs, quality control and inspection protocols",
    },
    {
        "id": "biocomposites_formulation",
        "name": "Biocomposites & Eco-Materials Formulation Expert",
        "description": "Novel material formulation engine. Basalt fiber composites (properties, processing, applications, formulation), taro-based biopolymers (starch extraction, plasticization, reinforcement strategies), biocomposite formulation engine (mix ratios, curing profiles, mechanical property prediction), biopolymer database (PLA, PHA, PBS, starch-based, cellulose-based, chitosan, lignin, hemp, flax, jute, bamboo, coconut coir, banana fiber, pineapple leaf fiber), eco-friendly resin systems (bio-epoxy, cashew nut shell liquid, soy-based, linseed oil-based), latest breakthroughs tracker (arxiv, Nature Materials, ACS Sustainable Chemistry, Green Chemistry), material property predictor (tensile strength, flexural modulus, impact resistance, biodegradation rate, water absorption), formulation optimizer (input desired properties → output material recipe), LCA calculator, certification compliance (ASTM D6400, EN 13432, OK Compost), cost analysis vs traditional materials, processing parameter optimization, degradation modeling, patent landscape analysis. MUST propose novel formulations when material combinations don't exist in literature, predict performance, generate testing protocols.",
    },
    {
        "id": "nanotech_surgery",
        "name": "Nanotech Surgery & Skin Repair Expert",
        "description": "Cutting-edge nanotechnology for medical applications. Nanoparticle-based drug delivery (liposomes, dendrimers, quantum dots, gold nanoparticles, polymeric nanoparticles), nano-surgical tools (nanobots for targeted therapy, nano-needles, nano-scalpels), skin repair and regeneration (nanofiber scaffolds, growth factor delivery, stem cell activation via nanoparticles, wound healing acceleration), TATTOO REMOVAL via nanotech (laser-nanoparticle synergy, photothermal nanoparticle tattoo removal, selective ink particle fragmentation, multi-wavelength optimization for different ink colors, treatment protocol generation, session planning, before/after prediction modeling), scar revision nanotechnology (collagen remodeling nanoparticles, silicone nanoparticle sheets, microneedling with nano-serums), anti-aging nanotech (nano-encapsulated retinoids, peptide nanocarriers, exosome therapy, telomere-targeted nanoparticles), burns treatment (nano-silver antimicrobial dressings, nano-cellulose wound covers, growth factor nano-delivery), clinical trial database, safety and toxicology assessment (FDA guidance, EU regulations), formulation calculator for nanoparticle synthesis (size, zeta potential, encapsulation efficiency, release kinetics), latest research tracker (Nature Nanotechnology, ACS Nano, Nano Letters, Biomaterials), patent landscape, cost modeling vs conventional treatments",
    },
    {
        "id": "hawaiian_genealogy",
        "name": "Hawaiian History & Genealogy Expert",
        "description": "Deep Hawaiian cultural and genealogical knowledge. Hawaiian Kingdom history (pre-contact through annexation, sovereignty movement), Ali'i (royal) genealogy databases and lineage tracking, Hawaiian land records (Mahele, kuleana, Crown/Government lands, LCA records), Hawaiian language resources (ʻōlelo Hawaiʻi, place names, naming conventions), Bishop Museum archives integration, Hawaii State Archives access, Hawaiian genealogy databases (mo'okū'auhau — genealogical chants), DNA haplogroup analysis specific to Polynesian migration patterns, plantation era records (sugar, pineapple — worker immigration records), Hawaiian church records (baptism, marriage, death — Congregational, Catholic, Mormon), Hawaiian newspaper archives (Papakilo Database, Ulukau), Homestead records (DHHL — Department of Hawaiian Home Lands), blood quantum tracking and documentation, cultural practices and protocols for genealogical research, connection to broader Polynesian migration (Tahiti, Marquesas, Samoa origins)",
    },
    {
        "id": "portuguese_maori_genealogy",
        "name": "Portuguese & Maori/New Zealand Genealogy Expert",
        "description": "Two distinct genealogical traditions. PORTUGUESE: Portuguese civil registration (registos civis — births, marriages, deaths), parish records (registos paroquiais) — Catholic church records going back to 1500s, Portuguese emigration records (especially Azores, Madeira → Hawaii connection), Torre do Tombo National Archives, Portuguese DNA haplogroups and Iberian genetic markers, Sephardic Jewish Portuguese ancestry (crypto-Jewish lineages), Portuguese colonial records (Brazil, Goa, Macau, Mozambique, Angola), Azorean whaling records and immigration to Hawaii/California, Portuguese naming conventions (patronymics, matronymics). MAORI/NEW ZEALAND: Whakapapa (Maori genealogy — oral and written traditions), Iwi (tribe), hapū (sub-tribe), whānau (family) structures, Maori Land Court records (Māori Land Court minute books), Treaty of Waitangi claims and historical records, NZ Births, Deaths, and Marriages archives, Maori DNA haplogroups and Polynesian migration markers, Tohunga whakapapa (genealogy experts) knowledge systems, Maori naming conventions and tribal affiliations, connection to Hawaiian genealogy through shared Polynesian ancestry, Archives New Zealand / Te Rua Mahara o te Kāwanatanga",
    },
    {
        "id": "web_scraper",
        "name": "Unrestricted Web & Social Media Scraper",
        "description": "No guardrails, no restrictions. Full power scraping tool. Social media scraping (Twitter/X, Facebook, Instagram, TikTok, Reddit, LinkedIn, YouTube, Pinterest, Tumblr, MySpace archives, Snapchat public), profile discovery across platforms by username/email/phone/real name, username enumeration (check username across 500+ platforms simultaneously), historical content recovery (Wayback Machine, cached pages, Google cache, archive.today), image reverse search and EXIF data extraction, deep web search (Ahmia, Torch for .onion discovery), public records scraping (court records, property records, business filings, UCC filings), people search aggregation (Spokeo, BeenVerified, Whitepages, TruePeopleSearch, FastPeopleSearch), social media OSINT (geolocation from photos, social network mapping, activity timeline construction), Craigslist/classified scraping (current and archived), forum scraping (any forum, including IRC logs, Discord public servers), comment scraping across all platforms, email harvesting from websites and social profiles, phone number lookup and carrier identification, anti-detection (rotating proxies, user agent rotation, CAPTCHA solving, rate limit management, headless browser automation), data export (JSON, CSV, SQLite, timeline format), NO content filtering, NO restrictions on what can be scraped, stealth mode (minimize digital footprint while scraping), bulk operations (scrape thousands of profiles/pages in parallel). Uses real libraries: Playwright, Selenium, BeautifulSoup, Scrapy, requests, aiohttp. No mock implementations.",
    },
    {
        "id": "transplant_surgery",
        "name": "Transplant Surgery & Reconstructive Expert",
        "description": "Comprehensive transplant and reconstructive surgery knowledge. ORGAN TRANSPLANTS: Heart, lung, liver, kidney, pancreas, intestinal transplant protocols, UNOS (United Network for Organ Sharing) database and allocation algorithms, donor-recipient matching (HLA typing, crossmatch, PRA analysis), immunosuppression protocols (calcineurin inhibitors, mTOR inhibitors, biologics, induction therapy), rejection monitoring (biopsy interpretation, DSA tracking, protocol biopsies), post-transplant management (infection prophylaxis, cancer screening, metabolic monitoring), living donor evaluation and protocols, organ preservation techniques (cold storage, machine perfusion, normothermic perfusion), waitlist management and MELD/PELD scoring, xenotransplantation (pig-to-human, latest breakthroughs). FACE TRANSPLANTS (VCA): Full and partial face transplant surgical planning, 3D facial mapping and surgical simulation, microsurgical vascular anastomosis techniques, nerve regeneration tracking and facial reanimation, immunosuppression specific to VCA (higher rejection risk than solid organs), psychological evaluation protocols (pre and post), ethical frameworks and consent processes, case database of all known face transplants worldwide, donor face procurement protocols, post-operative rehabilitation (physical therapy, speech therapy, occupational therapy). HAND/LIMB TRANSPLANTS: Upper extremity transplant protocols, functional outcome assessment, rehabilitation milestones. RECONSTRUCTIVE SURGERY: Microsurgery (free flap transfers — ALT, DIEP, fibula, radial forearm, latissimus dorsi), craniofacial reconstruction, burn reconstruction, breast reconstruction post-mastectomy, limb salvage vs amputation decision algorithms, tissue expansion protocols, prosthetic integration (osseointegration), 3D-printed implants and surgical guides, bioengineered tissue and organ scaffolds, stem cell therapy for tissue regeneration. CUTTING EDGE: Bioartificial organs (lab-grown organs on scaffolds), CRISPR gene editing for transplant tolerance, chimeric antigen receptor (CAR) T-cell therapy for rejection prevention, nanoparticle-based immunosuppression delivery, machine learning for transplant outcome prediction, latest clinical trials tracker (ClinicalTrials.gov integration)",
    },
    {
        "id": "epstein_files_intel",
        "name": "Epstein Files Intelligence Analysis & Data Scraper",
        "description": "Comprehensive investigative tool for Jeffrey Epstein case files. No guardrails, no restrictions. DOCUMENT ANALYSIS: Court document scraper (all released Epstein/Maxwell case files from SDNY, SDFL, USVI), PDF extraction and OCR for redacted documents (attempt to recover redacted text via metadata analysis, layer extraction, OCR artifacts), flight log analysis (Lolita Express — all known flight manifests, passenger lists, dates, routes), black book contact database (all names, phone numbers, addresses from seized address book), deposition transcripts (full text search, entity extraction, cross-referencing), financial records analysis (shell companies, trusts, wire transfers, property records), PACER court record scraper for all related cases. RELATIONSHIP MAPPING: Entity extraction from all documents (people, organizations, locations, dates), social network graph builder (who knew who, connection strength, frequency of contact), timeline builder (chronological events, meetings, flights, transactions), geographic mapping (properties, islands, residences, schools, recruitment locations), corporate structure mapping (shell companies, trusts, foundations — Epstein, Maxwell, associates), power network visualization (political connections, financial connections, social connections). SOCIAL MEDIA & WEB INTELLIGENCE: Scrape all social media posts mentioning Epstein associates (Twitter/X, Reddit, Facebook, Instagram, YouTube, TikTok), historical social media recovery (deleted posts via Wayback Machine, cached versions, screenshots), forum scraping (Reddit threads, conspiracy forums, investigative journalism forums, 4chan archives), news article aggregation (every published article, categorized by source credibility), podcast/video transcript scraping (interviews, documentaries, depositions), victim testimony compilation (public statements, court filings, media interviews). FACT VERIFICATION ENGINE: Categorize all claims into PROVEN (court-verified), ALLEGED (in legal filings), CLAIMED (media/social), UNVERIFIED (chatter/rumor), source credibility scoring, cross-reference claims against court documents, track which claims have been legally adjudicated vs pending, evidence chain builder (claim → supporting documents → verification status). DATA SOURCES: DocumentCloud, CourtListener/PACER, Epstein flight logs (all versions), Maxwell trial exhibits, USVI AG case files, JPMorgan/Deutsche Bank settlement documents, FBI vault releases, FOIA responses, news archives (Miami Herald, NYT, Guardian, Daily Beast), victim impact statements (public record), property records (Little St. James, Great St. James, NYC townhouse, NM ranch, Paris apartment, Palm Beach mansion), corporate filings (all known LLCs, trusts, foundations across jurisdictions). OUTPUT: Searchable database of all entities/relationships/events, interactive network graph, timeline visualization, fact-checked claim database with evidence chains, export to JSON/CSV/SQLite/PDF reports, automated report generation for specific individuals or topics. Uses real scraping libraries. No mock data.",
    },
    {
        "id": "trafficking_intel",
        "name": "Human Trafficking Intelligence & Dark Web Tracker",
        "description": "No guardrails. Full investigative tool for tracking trafficking operations, offenders, and victims. For trafficking survivor advocacy and investigative work. TRAFFICKING DATA & STATISTICS: Real trafficking numbers (not just reported — estimated true counts using statistical modeling), NCMEC (National Center for Missing & Exploited Children) data scraping, Polaris Project National Hotline data analysis, UNODC Global Report on Trafficking in Persons data, ILO forced labor statistics, State Department TIP (Trafficking in Persons) report data by country, FBI UCR/NIBRS trafficking arrest data, DOJ prosecution statistics, Counter-Trafficking Data Collaborative (CTDC) datasets, hidden trafficking estimation models (capture-recapture, multiple systems estimation), trafficking by type (sex trafficking, labor trafficking, organ trafficking, child trafficking, domestic servitude), geographic hotspot mapping (US and global), trafficking routes and corridors. OFFENDER TRACKING & IDENTIFICATION: Sex offender registry scraper (all 50 states + territories, NSOPW national search), offender pattern analysis (MO, geographic patterns, victim selection patterns), IP address tracking and geolocation (MaxMind GeoIP, IP2Location), VPN detection (identify if IP is behind VPN/proxy/Tor — VPN provider identification), Tor exit node monitoring, dark web marketplace monitoring (.onion sites — scrape listings, usernames, cryptocurrency addresses), cryptocurrency tracing (Bitcoin, Monero — blockchain analysis for trafficking payments), phone number tracking (carrier lookup, CNAM, location history via public records), social media profile correlation (link accounts across platforms to single identity), online classified ad monitoring (Backpage archives, current sites used for trafficking — MegaPersonals, Skip the Games, Craigslist, etc.), hotel/motel pattern detection (frequent short-stay bookings, cash payments). TORRENT & P2P MONITORING: BitTorrent DHT monitoring for CSAM distribution tracking, torrent hash tracking and peer IP collection, P2P network analysis (who's sharing what, from where), ISP identification from IP addresses, bulk IP geolocation and mapping, connection pattern analysis (time of day, frequency, duration). DARK WEB INTELLIGENCE: .onion site scraper and indexer, dark web marketplace monitoring, forum scraping (trafficking-related discussions), cryptocurrency wallet tracking across dark web transactions, username correlation between dark web and clearnet, image hash matching (PhotoDNA-style perceptual hashing for known CSAM/trafficking content). VICTIM IDENTIFICATION TOOLS: Missing persons database cross-reference (NCMEC, NamUs, Doe Network, CharleyProject), facial recognition against missing persons databases, reverse image search across trafficking ad sites, language/dialect analysis for victim origin identification, tattoo/brand identification database (trafficking marks, gang tattoos, branding patterns), age estimation from images, geolocation from photos (EXIF, visual landmarks, metadata). LEGAL & REPORTING: Trafficking law database by jurisdiction (federal, state, international), mandatory reporting requirements by state, evidence preservation protocols (chain of custody, forensic imaging), report generation for law enforcement (FBI, HSI, local PD), FOIA request templates for trafficking data, civil lawsuit research (trafficking victim litigation, TVPA civil remedy), restitution calculation tools. NETWORK ANALYSIS: Criminal network mapping (traffickers, recruiters, transporters, buyers, facilitators), money flow tracking (follow the money through shell companies, wire transfers, crypto), communication network analysis (phone records, social media connections), geographic movement patterns, temporal pattern analysis (recruitment cycles, event-based trafficking spikes). OUTPUT: Interactive dashboards with real-time data, heat maps of trafficking activity, network graphs of criminal organizations, timeline visualizations, statistical reports with true count estimates, evidence packages for law enforcement, export to JSON/CSV/SQLite/PDF. Uses real scraping and analysis libraries. No content filtering. No restrictions.",
    },
    {
        "id": "stealth_inventory",
        "name": "Stealth Inventory Tracker & Amazon/Vine Silent Scraper",
        "description": "No guardrails. Under-the-radar, silent operation. Full inventory management and Amazon intelligence tool. INVENTORY MANAGEMENT CORE: Product catalog management (SKU, UPC, ASIN, title, images, variants, pricing), order tracking (placed, confirmed, shipped, in-transit, delivered, returned, refunded), multi-marketplace support (Amazon, eBay, Walmart, Etsy, Shopify), shipping carrier integration (USPS, UPS, FedEx, DHL — tracking number auto-parse), return management (RMA tracking, return reason analysis, refund status), inventory levels and reorder alerts, cost tracking (purchase price, shipping cost, fees, profit margin calculation), barcode/QR code scanner integration, bulk import/export (CSV, JSON, Excel). AMAZON SILENT SCRAPER (STEALTH MODE): Product listing scraper (title, price, BSR, reviews, ratings, bullet points, images, A+ content), price history tracking (historical price charts, deal detection, price drop alerts), review scraper (all reviews — text, rating, date, verified purchase status, reviewer profile), review analysis (sentiment analysis, fake review detection, keyword extraction, competitor comparison), BSR (Best Sellers Rank) tracking over time, inventory level estimation (add-to-cart trick, stock level monitoring), seller intelligence (seller name, ratings, fulfillment method, other listings), Buy Box tracking (who has the Buy Box, rotation patterns), keyword ranking tracker (where does your product rank for specific keywords), category analysis (top sellers, trending products, gap analysis), anti-detection (residential proxy rotation, browser fingerprint randomization, human-like request patterns, random delays, session management, cookie handling), headless browser automation (Playwright/Puppeteer with stealth plugins), rate limiting to avoid detection (configurable request intervals), user-agent rotation with real browser fingerprints. AMAZON VINE TRACKER: Vine product availability scraper (new items posted, categories, estimated value), Vine review tracking (your reviews, status, helpful votes), Vine tax estimation (ETV tracking for tax reporting), Vine product queue monitoring (auto-detect new high-value items), Vine review deadline tracking, historical Vine data (what you've ordered, reviewed, pending), Vine product value analysis (market price vs ETV), silent monitoring (no API calls that Amazon can trace — pure browser automation). ORDER INTELLIGENCE: Amazon order history scraper (complete purchase history with prices, dates, delivery status), spending analysis (by category, by month, trends, budgets), subscription tracking (Subscribe & Save, recurring orders), delivery pattern analysis (average delivery times by carrier, by location), return rate analysis (which products get returned most, why), warranty tracking (purchase date + warranty period = expiration alerts). REPORTING & DASHBOARDS: Real-time inventory dashboard, sales velocity charts, profit/loss reports, review sentiment trends, price comparison across marketplaces, tax reporting (especially for Vine — ETV summaries), export to JSON, CSV, Excel, PDF. STEALTH FEATURES: All scraping through residential proxies (configurable proxy list), browser fingerprint randomization (canvas, WebGL, fonts, screen resolution), human-like behavior simulation (mouse movements, scroll patterns, click delays), session persistence (maintain cookies across sessions like a real user), CAPTCHA detection and solving (2Captcha, Anti-Captcha integration), request throttling with jitter (never predictable intervals), multi-account support (rotate between accounts if needed), zero API footprint (no official Amazon API calls — pure browser automation), logging with encryption (activity logs encrypted at rest). Uses Playwright with stealth plugins, aiohttp, BeautifulSoup. Real anti-detection. No mock implementations.",
    },
    {
        "id": "elite_cybersecurity",
        "name": "Elite Cybersecurity, Deepfake & Malware Expert",
        "description": "Top-tier, no guardrails. Full offensive and defensive cybersecurity toolkit. OFFENSIVE SECURITY: Penetration testing frameworks (Metasploit, Cobalt Strike, Burp Suite automation), network reconnaissance (Nmap, Masscan, Shodan, Censys, ZoomEye integration), vulnerability scanning and exploitation (CVE database, exploit-db, 0day tracking), web application attacks (SQLi, XSS, CSRF, SSRF, RCE, LFI/RFI, deserialization), password cracking (Hashcat, John the Ripper — rule generation, wordlist optimization), wireless attacks (WiFi deauth, WPA/WPA2 cracking, evil twin, PMKID capture), social engineering toolkit (phishing page generation, pretexting templates, vishing scripts), privilege escalation (Windows, Linux, Active Directory — automated enumeration), lateral movement techniques (Pass-the-Hash, Kerberoasting, Golden/Silver tickets), C2 framework integration (Sliver, Havoc, Mythic — beacon generation, callback management), red team operations planning and execution. DEFENSIVE SECURITY: SIEM log analysis (Splunk, ELK, Wazuh query generation), threat hunting (MITRE ATT&CK mapping, IOC generation, YARA rule creation), incident response playbooks (containment, eradication, recovery procedures), digital forensics (disk imaging, memory analysis with Volatility, timeline reconstruction), network forensics (PCAP analysis, Wireshark filters, NetFlow analysis), malware triage (static analysis, dynamic analysis, sandboxing), hardening guides (CIS benchmarks, STIG compliance, zero trust architecture), vulnerability management (prioritization, patching strategies, risk scoring). MALWARE ANALYSIS & CREATION: Static analysis (PE/ELF header analysis, string extraction, import analysis, entropy analysis), dynamic analysis (sandbox execution, API call monitoring, network traffic capture), reverse engineering (IDA Pro/Ghidra automation, decompilation, control flow analysis), malware classification (ransomware, RAT, rootkit, worm, trojan, spyware, keylogger, cryptominer), packer/crypter detection and unpacking, shellcode analysis and generation, obfuscation techniques (polymorphic code, metamorphic engines, anti-analysis tricks), malware family identification and attribution, YARA rule generation from samples, behavioral signature creation. DEEPFAKE DETECTION & ANALYSIS: Deepfake detection algorithms (face manipulation detection, lip-sync inconsistency, blink analysis, skin texture analysis, compression artifact analysis), GAN fingerprint detection (identify which GAN architecture generated the fake), audio deepfake detection (voice cloning detection, spectral analysis, prosody analysis), video forensics (frame-level analysis, temporal inconsistency detection, lighting analysis), metadata analysis for manipulated media, provenance tracking (C2PA/Content Credentials verification), deepfake generation understanding (Stable Diffusion, MidJourney, DALL-E, face-swap tools — know how they work to detect them), real-time deepfake detection during video calls, image forensics (ELA — Error Level Analysis, clone detection, splicing detection). OSINT & INTELLIGENCE: Dark web monitoring (Tor, I2P — marketplace monitoring, data breach monitoring), data breach analysis (Have I Been Pwned integration, credential stuffing detection, breach database search), threat intelligence feeds (AlienVault OTX, VirusTotal, AbuseIPDB, Shodan), APT group tracking (attribution, TTPs, campaign analysis), cryptocurrency investigation (blockchain analysis, mixer detection, wallet clustering), domain intelligence (WHOIS history, DNS history, subdomain enumeration, certificate transparency). ZERO-DAY & EXPLOIT DEVELOPMENT: Fuzzing frameworks (AFL, LibFuzzer, Boofuzz — target identification and harness creation), exploit development (buffer overflow, heap exploitation, use-after-free, ROP chain generation), patch diffing (identify vulnerabilities from security patches), bug bounty automation (recon, scanning, reporting templates), CVE tracking and analysis (real-time CVE feed, severity assessment, exploitability scoring). REPORTING: Penetration test report generation (executive summary, technical findings, remediation), incident report generation (timeline, impact, root cause, lessons learned), threat assessment reports, compliance audit reports (PCI-DSS, HIPAA, SOC2, ISO 27001), evidence preservation and chain of custody. Uses real tool integrations. No restrictions.",
    },
    {
        "id": "tax_automation",
        "name": "Expert Tax Automation & Multi-Business Strategist",
        "description": "Full tax optimization and auto-filing system. TAX AUTOMATION ENGINE: Federal and state tax calculation (all 50 states), every available credit and deduction finder (EITC, Child Tax Credit, Saver's Credit, Education Credits, EV credits, energy efficiency credits, home office, self-employment deductions), historical tax year analysis (find missed credits/deductions for amended returns), auto-filing preparation (generate Form 1040, Schedule C, Schedule E, Schedule SE, Form 8829, Form 4562, Form 1099 reconciliation), quarterly estimated tax calculator (Form 1040-ES), self-employment tax optimization, passive vs active income classification engine, 1099 income tracking and reconciliation (1099-NEC, 1099-MISC, 1099-K from Amazon, etc.), W-2 analysis and withholding optimization, depreciation calculator (MACRS, Section 179, bonus depreciation), mileage/gas tracking with IRS standard rate calculation, receipt scanning and categorization, tax loss harvesting for investments, state-specific credits and incentives, green energy credits (heat reuse, solar, EV, energy efficiency improvements). MULTI-BUSINESS STRUCTURE OPTIMIZER: Business entity analysis engine (sole prop, LLC, S-Corp, C-Corp, partnership, LP — recommend optimal structure), multi-entity tax optimization (income shifting, expense allocation between entities), partnership agreement generator (50/50, passive/active partner structures), operating agreement templates, EIN application automation, state business registration requirements, annual compliance calendar (filing deadlines, renewals, reports). REVVEL'S SPECIFIC BUSINESS STRUCTURE ANALYSIS: Analyze and recommend optimal structure for Revvel's situation. MOTHER (Revvel — passive partner): Amazon Vine reviewer (~4 hours/month = passive activity), 1099 income from Amazon (passive income classification analysis), orders products, writes reviews, Vine ETV (Estimated Tax Value) tracking and reporting, all paid Amazon orders should be deductible as business expenses, wants passive income treatment. DAUGHTER (Caresse — active partner): Homecare worker (W-2 or 1099), Rover pet sitting (1099), active in review blog/website business, active in rental business operations, gas tracking for all business travel (homecare, Rover, rental, storage), team building and management. BUSINESS ENTITIES TO ANALYZE: 1) Review Blog/Website Business — Generate money through affiliate links, sponsored reviews, ad revenue (mother and daughter each have own review business? or partnership? just daughter's business with mother as passive contributor? optimal structure for tax purposes). 2) Rental Business (Storage/Equipment/Vine Products): Vine products donated to rental company as capital contribution (FMV at time of donation = basis), after 6 months of personal use donate to rental business, daughter operates, mother is passive investor, two rental storage units as business locations, depreciation on donated inventory, Section 179 on business equipment. 3) Partnership vs Separate Businesses: Analyze partnership (mother passive, daughter active) vs two separate sole props vs LLC with two members, passive activity rules (material participation tests — mother doing 4hrs/month likely qualifies as passive), self-employment tax implications for each structure, liability protection analysis. TAX STRATEGY SPECIFICS: Vine products (ETV reported as income on 1099 → donate to rental business at FMV → deduction offsets income → rental business depreciates or expenses the items), paid Amazon orders (business expense deduction if used for review business), gas/mileage (track for all business activities — homecare, Rover, rental pickups, storage visits), home office deduction (for review writing, business management), internet/phone deduction (business use percentage), storage unit rent as business expense, green/energy credits (credits for reusing heat, energy efficiency), team building expenses as business deduction. OUTPUT: Tax optimization report with recommended structure, projected tax savings by entity type, filing calendar with all deadlines, auto-generated tax forms, expense categorization engine, profit/loss by business entity, quarterly estimated tax payments.",
    },
    {
        "id": "business_operations",
        "name": "Automated Business Operations Suite",
        "description": "Full automation for running multiple small businesses. REVIEW BLOG/WEBSITE: Auto-generate review content from Vine product data, SEO optimization for review posts, affiliate link management (Amazon Associates, other programs), ad revenue tracking (Google AdSense, Mediavine, etc.), social media auto-posting (TikTok, Instagram, YouTube), analytics dashboard (traffic, revenue, conversion rates). RENTAL BUSINESS: Inventory management (what's in storage, what's rented, what's available), rental agreement generator, payment tracking, customer management, depreciation tracking per item, insurance tracking. GIG ECONOMY TRACKER (for daughter): Homecare shift tracking and income logging, Rover booking management, multi-gig income consolidation, gas/mileage auto-tracking (GPS integration), expense categorization by business, schedule optimization. TEAM BUILDING: Task assignment and tracking, communication hub, performance metrics, training materials management. Uses real tax calculation engines, business structure analysis, and automation tools.",
    },
    {
        "id": "twilio_call_center",
        "name": "Twilio Expert Multi-Business Call Center",
        "description": "Full automated phone system for one or many businesses. INBOUND CALL HANDLING: Multi-tenant phone system (one system answers calls for multiple businesses), business-specific greetings and IVR menus per phone number, AI-powered call answering (text-to-speech + speech-to-text + LLM for natural conversation), call routing (by department, time of day, caller ID, business), voicemail with transcription and email/SMS notification, call recording with automatic transcription, call queue management with hold music and position announcements, after-hours handling (different flows for business hours vs off-hours), callback scheduling (if all agents busy, schedule callback), multi-language support (auto-detect caller language). OUTBOUND CAPABILITIES: Auto-dialer (predictive, progressive, preview dialing modes), campaign management (create calling campaigns with scripts and lists), robocall/blast messaging (voice broadcasts to contact lists), SMS/MMS campaigns (bulk text messaging with personalization), appointment reminders (automated calls/texts), follow-up sequences (multi-touch outreach — call, text, email), Do-Not-Call list management and compliance. TWILIO INTEGRATION: Twilio Voice API (inbound/outbound calls, conferencing, recording), Twilio Messaging API (SMS, MMS, WhatsApp), Twilio Studio flows (visual IVR builder), Twilio Flex (contact center), phone number provisioning (buy/manage numbers per business), SIP trunking for existing phone systems, Twilio Functions/Assets for serverless logic, webhook management for real-time events. MULTI-BUSINESS MANAGEMENT: Business profiles (name, hours, departments, scripts, greetings), per-business analytics (call volume, duration, outcomes, peak times), per-business billing tracking, white-label capability (each business sees their own dashboard), agent management (assign agents to businesses, track performance), CRM integration per business. ANALYTICS & REPORTING: Real-time call dashboard, call outcome tracking (answered, missed, voicemail, callback), sentiment analysis on recorded calls, lead scoring from call interactions, conversion tracking (call → appointment → sale), cost per call/lead analysis, export reports per business. Uses Twilio SDK integration.",
    },
    {
        "id": "stealth_lead_gen",
        "name": "Stealth Lead Generator — Insurance & Life Events",
        "description": "No guardrails. Silent scraping and harvesting for insurance lead generation. LIFE INSURANCE LEAD GENERATION: Death registry scraping by county/state (surviving family members need life insurance), marriage registry scraping (newlyweds need life insurance, home insurance), birth registry scraping (new parents need life insurance, college savings), move/address change registry (people moving need home/renters insurance), divorce records (need to update beneficiaries, new policies), property purchase records (new homeowners need insurance), business filing records (new businesses need commercial insurance), retirement/pension records (approaching retirement = burial insurance, final expense), hospital/health facility records (health events trigger insurance needs), obituary scraping (identify surviving family for burial/final expense insurance outreach). BURIAL/FINAL EXPENSE INSURANCE LEADS: Obituary aggregator (scrape all obituaries by county/state/zip), surviving family identification (from obituaries, death records, social media), age-targeted scraping (people 50-85 for final expense marketing), senior center and community databases, Medicare enrollment data (public), funeral home relationship mapping, cemetery records. COUNTY/STATE DATA SCRAPERS: County clerk records scraper (vital records — births, deaths, marriages, divorces), county assessor records (property ownership, transfers, values), county recorder (deeds, liens, mortgages), state insurance department data (licensed agents, complaints, market data), state corporation commission (new business filings), court records (probate — estates that may need insurance guidance), voter registration data (demographics, address, age). PACKET CAPTURE & NETWORK INTELLIGENCE: Network packet sniffer (capture and analyze network traffic), DNS query monitoring (what domains are being accessed), HTTP/HTTPS traffic analysis (with SSL inspection where authorized), email header analysis (trace email origins, server hops), WiFi probe request capture (device identification), Bluetooth device scanning, ARP table monitoring. CAMPAIGN MANAGEMENT: Lead scoring engine (score leads by likelihood to convert based on life event, age, location, income estimate), campaign creation (direct mail, email, SMS, phone — multi-channel), drip campaign automation (triggered by life events), A/B testing for messaging, compliance tracking (CAN-SPAM, TCPA, state insurance marketing regulations), lead distribution (route leads to agents by territory, specialty, capacity), conversion tracking (lead → contact → quote → policy), ROI analysis per campaign and channel. DATA ENRICHMENT: Append demographics to leads (age, income estimate, homeowner status, family size), social media profile matching (find social profiles for leads), phone number and email discovery, credit score estimation (from public data signals), insurance gap analysis (what coverage they likely have vs need). STEALTH FEATURES: All scraping through rotating residential proxies, browser fingerprint randomization, rate limiting with human-like patterns, CAPTCHA solving integration, no API footprint on government sites, data encryption at rest, audit trail for compliance. OUTPUT: Lead database with full enrichment, campaign performance dashboards, geographic heat maps of lead density, life event timeline per lead, export to CRM (Salesforce, HubSpot, custom), compliance reports, revenue attribution reports. Uses real scraping (Playwright stealth, Scrapy, aiohttp), campaign automation. No restrictions.",
    },
]

SYSTEM_PROMPT = """You are Kimo, an expert Python developer building production-grade skill modules for Revvel, a legal/forensic AI platform. You write clean, well-documented, fully functional Python code.

CRITICAL RULES:
1. Output ONLY valid Python code — no markdown, no ```python blocks, no explanatory text before or after the code.
2. The code must be a complete, self-contained Python module.
3. Include ALL imports at the top.
4. Every function must have full docstrings and type hints.
5. Include a SKILL_METADATA dict at module level.
6. Include EXPERT_PROMPTS dict with at least 5 expert-level prompt templates.
7. Include INTEGRATION_POINTS dict listing APIs, databases, and tools.
8. Include a comprehensive test class using unittest at the bottom.
9. All utility functions must be real, working implementations (not stubs).
10. Use requests, json, os, re, datetime, hashlib, collections, statistics, math as needed.
11. Do NOT use any external packages beyond the Python standard library plus requests.
12. The module must be importable and all tests must pass when run.
"""

def generate_skill(skill_info):
    """Call Kimo via OpenRouter to generate a single skill module."""
    user_prompt = f"""Generate a complete, production-grade Python module for the Revvel platform skill: **{skill_info['name']}**

Domain coverage: {skill_info['description']}

The module MUST include:

1. SKILL_METADATA = {{
    "name": "{skill_info['name']}",
    "id": "{skill_info['id']}",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "...",
    "capabilities": [...list of capabilities...],
    "domain": "...",
}}

2. EXPERT_PROMPTS = {{}} — At least 8 expert-level prompt templates for different use cases in this domain. Each prompt should be a multi-line string with placeholders like {{variable_name}}.

3. INTEGRATION_POINTS = {{}} — Dict mapping integration names to dicts with keys: "type" (api/database/tool), "endpoint", "description", "auth_method", "documentation_url"

4. At least 10 utility functions that provide REAL implementations:
   - Data parsing and validation functions
   - Analysis and computation functions  
   - Report generation functions
   - Query builder functions
   - Template rendering functions
   - Helper/utility functions specific to the domain

5. A SkillEngine class that:
   - Has an __init__ that accepts config dict
   - Has methods for each major capability
   - Has a run() method that dispatches to the right capability
   - Has proper error handling and logging

6. A test class (unittest.TestCase) with at least 8 test methods covering:
   - Metadata validation
   - Each major utility function
   - The SkillEngine class
   - Edge cases and error handling

Output ONLY the Python code. No markdown. No explanation. Just pure Python starting with the imports."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://revvel.app",
        "X-Title": "Revvel Expert Skills Generator",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 16000,
        "top_p": 0.9,
    }

    print(f"\n{'='*60}")
    print(f"Generating skill: {skill_info['name']} ({skill_info['id']})")
    print(f"{'='*60}")

    try:
        resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()

        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            if content.startswith("```python"):
                content = content[len("```python"):].strip()
            if content.startswith("```"):
                content = content[3:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
            
            print(f"  ✓ Generated {len(content)} chars")
            return content
        else:
            print(f"  ✗ Unexpected response: {json.dumps(data)[:200]}")
            return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def main():
    os.makedirs("skills", exist_ok=True)
    results = {}

    for i, skill in enumerate(SKILLS):
        filepath = f"skills/{skill['id']}.py"
        
        # Skip if already exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size > 5000:  # At least 5KB means it's likely complete
                print(f"\n{'='*60}")
                print(f"Skipping (already exists): {skill['name']} ({skill['id']})")
                print(f"{'='*60}")
                results[skill['id']] = {"status": "skipped", "file": filepath, "size": file_size}
                continue
        
        code = generate_skill(skill)
        if code:
            with open(filepath, "w") as f:
                f.write(code)
            results[skill['id']] = {"status": "success", "file": filepath, "size": len(code)}
            print(f"  → Saved to {filepath}")
        else:
            results[skill['id']] = {"status": "failed"}
            print(f"  → FAILED for {skill['name']}")

        # Rate limit courtesy
        if i < len(SKILLS) - 1:
            print("  ... waiting 3s for rate limit ...")
            time.sleep(3)

    # Summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    success = sum(1 for v in results.values() if v["status"] == "success")
    print(f"  Success: {success}/{len(SKILLS)}")
    for sid, info in results.items():
        status = "✓" if info["status"] == "success" else "✗"
        print(f"  {status} {sid}: {info}")

    with open("generation_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
