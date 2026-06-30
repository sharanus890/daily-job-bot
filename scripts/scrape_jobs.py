#!/usr/bin/env python3
"""
Daily Job Scraper - v7.0 (Fixed Company Names + Indeed + Freshersworld)
Scrapes 13 job platforms for:
  - Python Developer fresher jobs
  - Tech Support fresher jobs
  - Data Analyst fresher jobs
  - Cloud Computing fresher jobs
in Bengaluru
"""

import requests, json, time, re, urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup

OUTPUT_FILE = "jobs_found.json"

# -- HEADERS - rotate to avoid blocks -----------------------------------------
HEADERS_CHROME = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

HEADERS_MOZ = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) "
                  "Gecko/20100101 Firefox/115.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.naukri.com/",
    "appid": "109",
    "systemid": "Naukri",
    "x-requested-with": "XMLHttpRequest",
}

HEADERS_INDEED = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://in.indeed.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# -- ATS SCORER ----------------------------------------------------------------
PRIMARY_SKILLS = [
    "python", "django", "flask", "fastapi", "pandas", "numpy",
    "data analysis", "data analytics", "sql", "mysql", "postgresql",
    "power bi", "tableau", "excel", "matplotlib", "seaborn",
    "aws", "azure", "gcp", "cloud computing", "devops", "docker",
    "kubernetes", "linux", "terraform", "jenkins", "ci/cd",
    "technical support", "it support", "helpdesk", "troubleshooting",
    "networking", "api", "rest api", "git", "github",
]
SECONDARY_SKILLS = [
    "javascript", "html", "css", "react", "vue", "node.js",
    "mongodb", "sqlite", "redis", "kafka", "airflow", "dbt",
    "machine learning", "deep learning", "nlp", "data visualization",
    "statistics", "etl", "data mining", "web scraping", "selenium",
    "ansible", "prometheus", "grafana", "nginx", "apache",
    "windows server", "active directory", "office 365", "saas",
    "agile", "scrum", "jira", "communication", "customer service",
]
TITLE_KW = [
    "python", "django", "flask", "data analyst", "data analysis",
    "business analyst", "data analytics", "tech support", "technical support",
    "it support", "helpdesk", "desktop support", "cloud", "aws", "azure",
    "devops", "site reliability", "sre", "python developer",
    "software developer", "software engineer", "backend developer",
    "full stack", "fullstack", "web developer", "developer",
    "programmer", "data engineer", "data scientist", "ml engineer",
    "system administrator", "network engineer", "cloud engineer",
    "support engineer", "customer support", "it fresher",
]

def ats_score(title, desc="", skills=""):
    combined = f"{title} {desc} {skills}".lower()
    t = title.lower()
    score = 40 if any(k in t for k in TITLE_KW) else 0
    for s in PRIMARY_SKILLS:
        if s in combined: score += 5
    for s in SECONDARY_SKILLS:
        if s in combined: score += 2
    return min(score, 100)

# -- CLASSIFY ------------------------------------------------------------------
MNC_LIST = ["IBM","Accenture","Capgemini","Wipro","Infosys","TCS","HCL",
            "Cognizant","Tech Mahindra","Mphasis","LTIMindtree","Hexaware",
            "Oracle","SAP","Microsoft","Amazon","Deloitte","Persistent",
            "Zensar","Birlasoft","DXC","GlobalLogic","EPAM","ThoughtWorks",
            "Mindtree","Tata Consultancy","Publicis","NTT","Fujitsu",
            "Google","Meta","Adobe","VMware","Intel","Qualcomm","NVIDIA",
            "Dell","HP","Cisco","Juniper","ServiceNow","Salesforce",
            "PayPal","Flipkart","Swiggy","Zomato","Myntra","Ola",
            "Infosys BPM","WNS","Firstsource","Webhelp","Concentrix"]
STARTUP_LIST = ["Razorpay","PhonePe","CRED","Meesho","Groww","Zepto",
                "BrowserStack","Freshworks","Zoho","Chargebee","Scaler",
                "upGrad","Darwinbox","Leadsquared","Cutshort","Unacademy",
                "BYJU","Rapido","Porter","Delhivery","Navi","Slice",
                "Udaan","Dunzo","Lenskart","Nykaa"," cure.fit","Practo",
                "HackerEarth","InterviewBit","HashedIn","SquadStack",
                "Zerodha","Smallcase","Postman","Inshorts","Dailyhunt"]

def classify_co(name):
    n = (name or "").upper()
    if any(m.upper() in n for m in MNC_LIST):    return "MNC"
    if any(s.upper() in n for s in STARTUP_LIST): return "Startup"
    return "Company"

# -- COMPANY NAME FIX - Completely rewritten for robust extraction ------------
BAD_COMPANY_NAMES = {
    "n/a", "na", "company name n/a", "unknown", "not mentioned",
    "confidential", "confidential company", "", "-", "null", "none", ".",
    "not disclosed", "undisclosed", "company not disclosed", " hiring",
    "job expired", "expired", "jobs", "job",
}

def clean_co(name):
    """Clean company name - extract actual company name from text."""
    if not name:
        return ""
    
    n = str(name).strip()
    
    # Remove HTML entities
    n = re.sub(r'<[^>]+>', '', n)
    
    # Remove common prefixes like "at ", "with ", "by ", "for " only if at start
    n = re.sub(r'^(at|with|by|for)\s+', '', n, flags=re.IGNORECASE)
    
    # Remove suffixes like "Private Limited", "Pvt Ltd" etc.
    n = re.sub(r'\s+(private\s+limited|pvt\.?\s+ltd\.?|limited|ltd\.?|inc\.?|corp\.?|corporation|llp|llc)\s*$', '', n, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    n = re.sub(r'\s+', ' ', n).strip()
    
    # Remove trailing punctuation
    n = n.strip('.,;:|-')
    
    n_lower = n.lower()
    
    # Check against bad names
    if n_lower in BAD_COMPANY_NAMES or not n or len(n) < 2:
        return ""
    
    # Filter out generic non-company strings that are just job-related words
    generic_words = {"hiring", "apply", "job", "jobs", "career", "careers", 
                     "vacancy", "vacancies", "opening", "openings", "recruitment",
                     "immediate", "urgent", "walkin", "walk-in", "fresher",
                     "experience", "years", "year", "bengaluru", "bangalore",
                     "hyderabad", "chennai", "mumbai", "pune", "delhi", "gurgaon",
                     "noida", "remote", "hybrid", "work from home", "wfh"}
    
    # If the entire name is just generic words, reject it
    words_only = set(re.findall(r'[a-z]+', n_lower))
    if words_only and words_only.issubset(generic_words):
        return ""
    
    # Must have at least one alphabetic character
    if not re.search(r'[a-zA-Z]', n):
        return ""
    
    return n


def fallback_company_name(soup, default=""):
    """Try multiple methods to extract company name from page - ENHANCED."""
    
    # Method 1: ld+json schema - JobPosting
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
            lst = data if isinstance(data, list) else [data]
            for jb in lst:
                if isinstance(jb, dict):
                    # Try hiringOrganization
                    org = jb.get("hiringOrganization", {})
                    if isinstance(org, dict):
                        name = org.get("name", "")
                        cleaned = clean_co(name)
                        if cleaned:
                            return cleaned
                    # Try employerName
                    name = jb.get("employerName", "")
                    cleaned = clean_co(name)
                    if cleaned:
                        return cleaned
                    # Try identifier/name
                    org = jb.get("identifier", {})
                    if isinstance(org, dict):
                        name = org.get("name", "")
                        cleaned = clean_co(name)
                        if cleaned:
                            return cleaned
        except:
            pass
    
    # Method 2: Meta tags
    for meta in soup.find_all("meta", property=["og:site_name", "twitter:site"]):
        name = meta.get("content", "")
        cleaned = clean_co(name)
        if cleaned:
            return cleaned
    
    # Method 3: data-company, data-employer attributes
    for attr in ["data-company", "data-employer", "data-company-name", 
                 "data-org", "data-organization", "company", "employer"]:
        el = soup.find(attrs={attr: True})
        if el:
            val = el.get(attr, "").strip()
            cleaned = clean_co(val)
            if cleaned:
                return cleaned
    
    # Method 4: Common CSS selectors for company names
    selectors = [
        '[class*="company"] span', '[class*="employer"] span',
        '[class*="company"] a', '[class*="employer"] a',
        '[class*="company"] div', '[class*="employer"] div',
        '[class*="company"] h4', '[class*="employer"] h4',
        '[class*="company"] p', '[class*="employer"] p',
        '[class*="org"] span', '[class*="org"] a',
        'a[href*="company"]', 'a[href*="employer"]', 
        'a[href*="/company/"]', 'a[href*="/companies/"]',
        '[itemtype*="Organization"] [itemprop="name"]',
        '[itemprop="hiringOrganization"]',
        '.company-name', '.employer-name', '.org-name',
        '.companyName', '.employerName',
        '[data-testid*="company"]', '[data-testid*="employer"]',
        '[class*="job-card"] [class*="company"]',
        '[class*="jobCard"] [class*="company"]',
        '[class*="result"] [class*="company"]',
        'h3[class*="company"]', 'h4[class*="company"]',
        'span[class*="company-name"]', 'div[class*="company-name"]',
    ]
    for sel in selectors:
        try:
            els = soup.select(sel)
            for el in els:
                text = el.get_text(strip=True)
                cleaned = clean_co(text)
                if cleaned:
                    return cleaned
        except:
            pass
    
    # Method 5: Look for text patterns like "at CompanyName" or "CompanyName Pvt Ltd"
    page_text = soup.get_text()
    patterns = [
        r'at\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s+(?:Private\s+Limited|Pvt\.?\s+Ltd\.?|Ltd\.?|Inc\.?|LLP))?(?:\s*[\n\r,|]|\s+in\s)',
        r'hiring\s+by\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[\n\r,|])',
        r'company:\s*([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[\n\r,|])',
        r'employer:\s*([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[\n\r,|])',
        r'([A-Z][A-Za-z0-9\s&.,]+?(?:Private\s+Limited|Pvt\.?\s+Ltd\.?|Ltd\.?|Inc\.?|LLP))',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            cleaned = clean_co(match.group(1))
            if cleaned:
                return cleaned
    
    return default


def extract_company_from_card(card, soup=None):
    """Extract company name from a job card element with multiple strategies."""
    if not card:
        return ""
    
    # Strategy 1: Direct element with company-related class
    company_tags = ["span", "div", "a", "p", "h4", "h3", "h5", "strong", "em"]
    company_classes = [
        r"company", r"employer", r"organization", r"org", r"org-name",
        r"company-name", r"employer-name", r"companyName", r"employerName",
        r"comp-name", r"compName", r"hiring-org",
    ]
    
    for tag in company_tags:
        for cls_pattern in company_classes:
            el = card.find(tag, class_=re.compile(cls_pattern, re.IGNORECASE))
            if el:
                text = el.get_text(strip=True)
                cleaned = clean_co(text)
                if cleaned:
                    return cleaned
    
    # Strategy 2: data-* attributes on the card or children
    for attr in ["data-company", "data-employer", "data-company-name", 
                 "data-org", "data-organization"]:
        el = card.find(attrs={attr: True})
        if el:
            cleaned = clean_co(el.get(attr, ""))
            if cleaned:
                return cleaned
    
    # Strategy 3: Look for aria-label containing company info
    for el in card.find_all(attrs={"aria-label": True}):
        aria = el.get("aria-label", "")
        m = re.search(r'(?:at|by|with)\s+([A-Za-z0-9\s&.,]+)', aria, re.IGNORECASE)
        if m:
            cleaned = clean_co(m.group(1))
            if cleaned:
                return cleaned
    
    # Strategy 4: Subtitle / secondary text that looks like a company name
    subtitle = card.find(class_=re.compile(r"subtitle|secondary|muted|info-meta|detail"))
    if subtitle:
        text = subtitle.get_text(strip=True)
        # If it looks like a company (not location, not salary)
        if text and not any(x in text.lower() for x in ["bengaluru", "bangalore", "hyderabad", "chennai", "pune", "mumbai", "salary", "lpa", "years", "year exp"]):
            cleaned = clean_co(text)
            if cleaned and len(cleaned) > 2:
                return cleaned
    
    # Strategy 5: Use soup-level fallback
    if soup:
        return fallback_company_name(soup, "")
    
    return ""


def safe_get(url, headers=None, timeout=15, retries=2):
    h = headers or HEADERS_CHROME
    for attempt in range(retries):
        try:
            sess = requests.Session()
            sess.headers.update(h)
            r = sess.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 200:
                return r
            if r.status_code == 403:
                print(f"    403 blocked: {url[:55]}")
                return None
            time.sleep(2)
        except Exception as e:
            if attempt == retries - 1:
                print(f"    Error: {url[:50]} -> {e}")
    return None

def dedup(jobs):
    seen, out = set(), []
    for j in jobs:
        k = (j["title"].lower()[:30], j["company"].lower()[:20])
        if k not in seen:
            seen.add(k); out.append(j)
    return out


# -- FILTERS -------------------------------------------------------------------
RELEVANT_TITLES = [
    "python","django","flask","fastapi","data analyst","data analysis",
    "business analyst","data analytics","tech support","technical support",
    "it support","helpdesk","desktop support","cloud","aws","azure",
    "gcp","devops","site reliability","sre","python developer",
    "software developer","software engineer","backend developer",
    "full stack","fullstack","web developer","developer","programmer",
    "data engineer","data scientist","ml engineer","machine learning",
    "system administrator","network engineer","cloud engineer",
    "support engineer","it fresher","graduate engineer","trainee engineer",
    "associate engineer","junior developer","entry level",
    "customer support","technical associate","it associate",
]
SENIOR_EXCLUDE = [
    "senior", "sr.", "sr ", "lead", "manager", "architect","principal",
    "staff","director","head of","vp ","cto","tech lead","5+ years",
    "6+ years","7+ years","8+ years","10+ years",
]
NON_IT_EXCLUDE = [
    "sales executive","marketing manager","bpo","call center","voice process",
    "data entry","telecalling","hr recruiter","accountant","ca ",
    "chartered accountant","finance manager","banking relationship",
    "insurance agent","field executive","driver","teacher","nurse",
    "chef","delivery","security guard","logistics","warehouse","packing",
    "civil engineer","mechanical engineer","electrical engineer",
    "construction","real estate","digital marketing","content writer",
    "seo ","social media","hr manager","recruiter",
]
BENGALURU = ["bengaluru","bangalore","bengalore","blr"]
WALKIN_KW = ["walk-in","walkin","walk in","direct interview","spot offer",
             "spot selection","campus drive","hiring drive","open interview"]
EMAIL_RE  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE  = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")

def is_relevant(title):
    t = title.lower()
    if any(e in t for e in NON_IT_EXCLUDE): return False
    if any(e in t for e in SENIOR_EXCLUDE): return False
    return any(k in t for k in RELEVANT_TITLES)

def is_bengaluru(loc):
    return any(b in (loc or "").lower() for b in BENGALURU)

def is_fresher(exp):
    if not exp: return True
    t = exp.lower()
    if any(w in t for w in ["fresher","0 year","0-1","0-2","entry","graduate","trainee"]):
        return True
    for p in [r"[3-9]\d*\s*[-\u2013]\s*\d+\s*year", r"[3-9]\d*\+\s*year", r"minimum\s*[3-9]"]:
        if re.search(p, t): return False
    nums = re.findall(r"\d+", t)
    if nums and max(int(n) for n in nums) > 2: return False
    return True

def is_walkin(text):
    return any(w in (text or "").lower() for w in WALKIN_KW)

def extract_contact(text):
    emails = [e for e in EMAIL_RE.findall(text or "")
              if not any(b in e.lower() for b in ["noreply","no-reply","support@","info@"])]
    phones = PHONE_RE.findall(text or "")
    return {"recruiter_email": emails[0] if emails else "",
            "recruiter_phone": phones[0] if phones else ""}

def make_job(source, title, company, location, link,
             posted="Today", experience="0-2 years (Fresher)",
             skills="", salary="", walkin=False, walkin_info="",
             recruiter_email="", recruiter_phone="", description=""):
    co = clean_co(company)
    if not co:
        co = "Company Not Disclosed"
    score = ats_score(title, description, skills)
    return {
        "source": source, "title": title.strip(),
        "company": co, "company_type": classify_co(co),
        "location": location or "Bengaluru, India",
        "link": link, "posted": posted, "experience": experience,
        "skills": skills, "salary": salary,
        "is_walkin": walkin, "walkin_info": walkin_info,
        "recruiter_email": recruiter_email,
        "recruiter_phone": recruiter_phone,
        "ats_score": score,
    }


# =============================================================================
# SCRAPER 1 - LINKEDIN
# =============================================================================
def scrape_linkedin():
    jobs = []
    print("  LinkedIn...")
    searches = [
        "python developer fresher Bengaluru",
        "data analyst fresher Bengaluru",
        "technical support fresher Bengaluru",
        "cloud computing fresher Bengaluru",
        "python django developer fresher Bengaluru",
        "data analytics fresher Bengaluru",
        "it support fresher Bengaluru",
        "aws devops fresher Bengaluru",
    ]
    for kw in searches:
        try:
            url = (f"https://www.linkedin.com/jobs/search/"
                   f"?keywords={urllib.parse.quote(kw)}"
                   f"&location={urllib.parse.quote('Bengaluru, Karnataka, India')}"
                   f"&f_TPR=r604800&f_E=1,2&sortBy=DD")
            resp = safe_get(url, HEADERS_CHROME)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract all ld+json schemas first for company name fallback
            all_schemas = []
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(s.string or "")
                    lst = data if isinstance(data, list) else [data]
                    all_schemas.extend(lst)
                except: pass

            for jb in all_schemas:
                try:
                    if not isinstance(jb, dict): continue
                    if jb.get("@type") != "JobPosting":
                        continue
                    title   = jb.get("title","")
                    org = jb.get("hiringOrganization", {}) or {}
                    if isinstance(org, dict):
                        company = org.get("name","")
                    else:
                        company = ""
                    company = clean_co(company) or clean_co(jb.get("employerName",""))
                    link    = jb.get("url","") or jb.get("sameAs","")
                    desc    = jb.get("description","")
                    loc_data = jb.get("jobLocation", {})
                    loc = "Bengaluru, India"
                    if isinstance(loc_data, dict):
                        addr = loc_data.get("address", {})
                        if isinstance(addr, dict):
                            city = addr.get("addressLocality","")
                            state = addr.get("addressRegion","")
                            if city: loc = f"{city}, {state}, India" if state else f"{city}, India"
                    exp_txt = str(jb.get("experienceRequirements",""))
                    date_posted = jb.get("datePosted", "Today")
                    if not title or not is_relevant(title): continue
                    if not is_fresher(exp_txt): continue
                    jobs.append(make_job("LinkedIn", title, company or "Company Not Disclosed",
                                         loc, link, posted=date_posted,
                                         description=desc, walkin=is_walkin(desc)))
                except: pass

            # HTML card fallback with improved selectors
            cards = (soup.find_all("div", class_=re.compile(r"job-search-card")) or
                     soup.find_all("li", class_=re.compile(r"jobs-search-results__list-item")) or
                     soup.find_all("div", class_=re.compile(r"base-card")) or
                     soup.find_all("div", class_=re.compile(r"job-result-card")) or
                     soup.find_all("div", attrs={"data-entity-urn": re.compile(r"urn:li:fs_normalized_job:")}))
            for card in cards[:15]:
                try:
                    te = (card.find(["h3","a","span"], class_=re.compile(r"job-search-card__title|base-card__full-link|screen-reader-text")) or
                          card.find("a", class_=re.compile(r"disabled[!]*emphasis[!]*")))
                    # Try multiple company selectors
                    ce = None
                    for sel in ["h4", "a", "span", "div", "p"]:
                        ce = card.find(sel, class_=re.compile(r"job-search-card__company|base-card__subtitle|artdeco-entity-lockup__subtitle|company-name|employer-name"))
                        if ce: break
                    # LinkedIn sometimes puts company name in hidden aria-label
                    company = ""
                    if not ce:
                        link_a = card.find("a", class_=re.compile(r"hidden|screen-reader"))
                        if link_a:
                            aria = link_a.get("aria-label","")
                            m = re.search(r'at\s+([A-Za-z0-9\s&.,]+)', aria)
                            if m:
                                company = clean_co(m.group(1).strip())
                    else:
                        company = extract_company_from_card(card, soup)

                    le = card.find("span", class_=re.compile(r"job-search-card__location"))
                    ae = card.find("a", href=re.compile(r"/jobs/view/"))
                    de = card.find("time")
                    title   = (te.get_text(strip=True) if te else "").strip()
                    loc     = (le.get_text(strip=True) if le else "Bengaluru, India")
                    if not title or not is_relevant(title): continue
                    if not is_bengaluru(loc): continue
                    href = ae["href"] if ae else ""
                    link = ("https://www.linkedin.com"+href.split("?")[0]
                            if href.startswith("/") else href)
                    posted = de.get("datetime","Today") if de else "Today"
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("LinkedIn", title, company, loc, link, posted=posted))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    LinkedIn err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 2 - INTERNSHALA
# =============================================================================
def scrape_internshala():
    jobs = []
    print("  Internshala...")
    urls = [
        "https://internshala.com/jobs/python-jobs-in-bengaluru/",
        "https://internshala.com/jobs/data-analytics-jobs-in-bengaluru/",
        "https://internshala.com/jobs/data-science-jobs-in-bengaluru/",
        "https://internshala.com/jobs/software-development-jobs-in-bengaluru/",
        "https://internshala.com/jobs/it-jobs-in-bengaluru/",
        "https://internshala.com/jobs/backend-development-jobs-in-bengaluru/",
        "https://internshala.com/jobs/full-stack-development-jobs-in-bengaluru/",
        "https://internshala.com/jobs/web-development-jobs-in-bengaluru/",
    ]
    for url in urls:
        try:
            resp = safe_get(url, HEADERS_CHROME)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # ld+json schema extraction with improved company handling
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(s.string or "")
                    lst  = data if isinstance(data,list) else [data]
                    for jb in lst:
                        if not isinstance(jb,dict): continue
                        title   = jb.get("title","")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name","") if isinstance(org, dict) else ""
                        link    = jb.get("url","")
                        sal     = str(jb.get("baseSalary",""))
                        if not title or not is_relevant(title): continue
                        jobs.append(make_job("Internshala", title, company or "Company Not Disclosed",
                                             "Bengaluru, India", link,
                                             experience="Fresher / 0-1 year",
                                             salary=sal))
                except: pass

            # Improved HTML card parsing
            cards = (soup.find_all("div", class_=re.compile(r"individual_internship")) or
                     soup.find_all("div", class_=re.compile(r"job-internship-card")) or
                     soup.find_all("div", class_=re.compile(r"internship_meta")) or
                     soup.find_all("div", class_=re.compile(r"job_listing")))
            for card in cards[:12]:
                try:
                    te = (card.find(["h3","a"], class_=re.compile(r"profile|job-title|title")) or
                          card.find("a", href=re.compile(r"/jobs/detail/|/internships/detail/")) or
                          card.find("div", class_=re.compile(r"heading")))
                    company = extract_company_from_card(card, soup)
                    se = card.find("span", class_=re.compile(r"stipend|salary|cta"))
                    ae = card.find("a", href=re.compile(r"/jobs/detail/|/internships/detail/"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    if not title or not is_relevant(title): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://internshala.com{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Internshala", title, company,
                                         "Bengaluru, India", link,
                                         experience="Fresher / 0-1 year",
                                         salary=se.get_text(strip=True) if se else ""))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Internshala err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 3 - FOUNDIT (Monster India)
# =============================================================================
def scrape_foundit():
    jobs = []
    print("  Foundit (Monster India)...")
    searches = [
        "python-developer-jobs-in-bengaluru?experienceRanges=0~2",
        "data-analyst-jobs-in-bengaluru?experienceRanges=0~2",
        "technical-support-jobs-in-bengaluru?experienceRanges=0~2",
        "cloud-engineer-jobs-in-bengaluru?experienceRanges=0~2",
        "software-developer-fresher-jobs-in-bengaluru?experienceRanges=0~1",
        "data-science-jobs-in-bengaluru?experienceRanges=0~2",
        "aws-devops-jobs-in-bengaluru?experienceRanges=0~2",
    ]
    for s in searches:
        try:
            url = f"https://www.foundit.in/srp/results?query={s}"
            resp = safe_get(url, HEADERS_CHROME)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            for scr in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(scr.string or "")
                    lst  = data if isinstance(data,list) else [data]
                    for jb in lst:
                        if not isinstance(jb,dict): continue
                        title   = jb.get("title","")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name","") if isinstance(org, dict) else ""
                        link    = jb.get("url","")
                        desc    = jb.get("description","")
                        exp_txt = str(jb.get("experienceRequirements",""))
                        if not title or not is_relevant(title): continue
                        if not is_fresher(exp_txt): continue
                        company = clean_co(company) or "Company Not Disclosed"
                        jobs.append(make_job("Foundit", title, company,
                                             "Bengaluru, India", link,
                                             description=desc, walkin=is_walkin(desc)))
                except: pass

            cards = (soup.find_all("div", class_=re.compile(r"card-apply-content|job-tittle|jobCard|cardContainer")) or
                     soup.find_all("article", class_=re.compile(r"jobCard|job-card|cardContainer")) or
                     soup.find_all("div", class_=re.compile(r"jobCard")))
            for card in cards[:12]:
                try:
                    te = card.find(["h3","h2","a"], class_=re.compile(r"title|jobTitle|job-title"))
                    company = extract_company_from_card(card, soup)
                    ae = card.find("a", href=re.compile(r"/job-detail/|/jobs/"))
                    ee = card.find(["span","div"], class_=re.compile(r"exp|experience"))
                    se = card.find(["span"], class_=re.compile(r"sal|salary"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    exp_txt = (ee.get_text(strip=True) if ee else "")
                    if not title or not is_relevant(title): continue
                    if not is_fresher(exp_txt): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://www.foundit.in{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Foundit", title, company,
                                         "Bengaluru, India", link,
                                         experience=exp_txt or "0-2 years (Fresher)",
                                         salary=se.get_text(strip=True) if se else ""))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Foundit err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 4 - NAUKRI (API + HTML fallback)
# =============================================================================
def scrape_naukri():
    jobs = []
    print("  Naukri...")
    api_searches = [
        "python+developer",
        "data+analyst",
        "technical+support",
        "cloud+computing",
        "aws+devops",
        "data+science",
        "python+django",
        "it+support",
        "python+fresher",
    ]
    for kw in api_searches:
        try:
            api_url = (f"https://www.naukri.com/jobapi/v3/search?"
                       f"noOfResults=20&urlType=search_by_keyword&searchType=adv"
                       f"&keyword={kw}&location=bengaluru"
                       f"&experience=0&experienceDD=2&jobAge=1&src=jobsearchDesk")
            resp = safe_get(api_url, HEADERS_API)
            if not resp: continue
            try:
                data = resp.json()
            except: continue
            for jb in data.get("jobDetails", [])[:15]:
                title   = jb.get("title","")
                company = (jb.get("companyName","") or jb.get("fCompanyName",""))
                link    = (jb.get("jdURL","") or
                           f"https://www.naukri.com{jb.get('staticUrl','')}")
                exp_txt = jb.get("experienceText","")
                skills  = jb.get("tagsAndSkills","")
                salary  = jb.get("salary","")
                desc    = jb.get("jobDescription","")
                walkin  = is_walkin(title+desc)
                if not title or not is_relevant(title): continue
                if not is_fresher(exp_txt): continue
                company = clean_co(company) or "Company Not Disclosed"
                jobs.append(make_job("Naukri", title, company,
                                     "Bengaluru, India", link,
                                     experience=exp_txt or "0-2 years (Fresher)",
                                     skills=skills, salary=salary,
                                     walkin=walkin, description=desc,
                                     **extract_contact(desc)))
            time.sleep(2)
        except Exception as e:
            print(f"    Naukri API err ({kw}): {e}")

    html_pages = [
        "https://www.naukri.com/python-developer-jobs-in-bengaluru?experience=0&jobAge=1",
        "https://www.naukri.com/data-analyst-jobs-in-bengaluru?experience=0&jobAge=1",
        "https://www.naukri.com/technical-support-jobs-in-bengaluru?experience=0&jobAge=1",
        "https://www.naukri.com/cloud-computing-jobs-in-bengaluru?experience=0&jobAge=1",
        "https://www.naukri.com/software-developer-fresher-jobs-in-bengaluru",
    ]
    naukri_h = {**HEADERS_CHROME, "Referer":"https://www.naukri.com/", "appid":"109","systemid":"Naukri"}
    for url in html_pages:
        try:
            resp = safe_get(url, naukri_h)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for scr in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(scr.string or "")
                    lst  = data if isinstance(data,list) else [data]
                    for jb in lst:
                        if not isinstance(jb,dict): continue
                        title   = jb.get("title","")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name","") if isinstance(org, dict) else ""
                        link    = jb.get("url","")
                        exp_txt = str(jb.get("experienceRequirements",""))
                        desc    = jb.get("description","")
                        if not title or not is_relevant(title): continue
                        if not is_fresher(exp_txt): continue
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job("Naukri", title, company,
                                             "Bengaluru, India", link,
                                             experience=exp_txt or "0-2 years (Fresher)",
                                             description=desc, walkin=is_walkin(desc)))
                except: pass
            time.sleep(3)
        except Exception as e:
            print(f"    Naukri HTML err: {e}")

    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 5 - INDEED (NEW)
# =============================================================================
def scrape_indeed():
    jobs = []
    print("  Indeed...")
    searches = [
        ("python+developer+fresher", "python developer fresher"),
        ("data+analyst+fresher", "data analyst fresher"),
        ("technical+support+fresher", "technical support fresher"),
        ("cloud+computing+fresher", "cloud computing fresher"),
        ("software+developer+fresher", "software developer fresher"),
        ("aws+devops+fresher", "aws devops fresher"),
        ("it+support+fresher", "it support fresher"),
        ("python+django+fresher", "python django fresher"),
    ]
    for kw, display_kw in searches:
        try:
            url = (f"https://in.indeed.com/jobs?"
                   f"q={kw}&l=Bengaluru%2C+Karnataka"
                   f"&fromage=7&sort=date")
            resp = safe_get(url, HEADERS_INDEED)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # ld+json schema extraction
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(s.string or "")
                    lst  = data if isinstance(data, list) else [data]
                    for jb in lst:
                        if not isinstance(jb, dict): continue
                        if jb.get("@type") != "JobPosting":
                            continue
                        title   = jb.get("title", "")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name", "") if isinstance(org, dict) else ""
                        link    = jb.get("url", "")
                        desc    = jb.get("description", "")
                        loc_data = jb.get("jobLocation", {})
                        loc = "Bengaluru, India"
                        if isinstance(loc_data, dict):
                            addr = loc_data.get("address", {})
                            if isinstance(addr, dict):
                                city = addr.get("addressLocality", "")
                                state = addr.get("addressRegion", "")
                                if city: loc = f"{city}, {state}, India" if state else f"{city}, India"
                        exp_txt = str(jb.get("experienceRequirements", ""))
                        date_posted = jb.get("datePosted", "Today")
                        if not title or not is_relevant(title): continue
                        if not is_fresher(exp_txt): continue
                        company = clean_co(company) or "Company Not Disclosed"
                        jobs.append(make_job("Indeed", title, company,
                                             loc, link, posted=date_posted,
                                             description=desc, walkin=is_walkin(desc)))
                except: pass

            # Indeed-specific card selectors
            cards = (soup.find_all("div", class_=re.compile(r"job_seen_beacon|slider_container|slider|jobsearch-SerpJobCard")) or
                     soup.find_all("div", class_=re.compile(r"result")) or
                     soup.find_all("div", attrs={"data-jk": True}) or
                     soup.find_all("td", class_=re.compile(r"result")) or
                     soup.find_all("div", class_=re.compile(r"job")))
            
            for card in cards[:15]:
                try:
                    # Indeed title selector
                    te = (card.find(["h2", "a", "span"], class_=re.compile(r"jobTitle|title")) or
                          card.find("a", attrs={"data-jk": True}) or
                          card.find("a", id=re.compile(r"job_")) or
                          card.find("h2", class_=re.compile(r"jobTitle")))
                    
                    company = extract_company_from_card(card, soup)
                    
                    # Indeed-specific company extraction
                    if not company:
                        for sel_tag in ["span", "div", "a"]:
                            ce = card.find(sel_tag, class_=re.compile(r"companyName|company-name|company"))
                            if ce:
                                company = clean_co(ce.get_text(strip=True))
                                break
                    
                    # Indeed location
                    le = card.find(["div", "span"], class_=re.compile(r"companyLocation|location"))
                    # Indeed salary
                    se = card.find(["div", "span"], class_=re.compile(r"salary-snippet-container|estimated-salary|salary"))
                    # Indeed date posted
                    de = card.find(["span", "div"], class_=re.compile(r"date"))
                    # Indeed link
                    ae = (card.find("a", attrs={"data-jk": True}) or
                          card.find("a", href=re.compile(r"/rc/clk|/viewjob")) or
                          card.find("a", id=re.compile(r"job_")))
                    
                    title = (te.get_text(strip=True) if te else "").strip()
                    loc = (le.get_text(strip=True) if le else "Bengaluru, India")
                    if not title or not is_relevant(title): continue
                    
                    href = ae["href"] if ae else ""
                    if href.startswith("/"):
                        link = f"https://in.indeed.com{href}"
                    elif href.startswith("http"):
                        link = href
                    else:
                        link = f"https://in.indeed.com/viewjob?jk={card.get('data-jk', '')}" if card.get('data-jk') else url
                    
                    posted = "Today"
                    if de:
                        posted_text = de.get_text(strip=True)
                        posted = posted_text if posted_text else "Today"
                    
                    salary = se.get_text(strip=True) if se else ""
                    
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    
                    jobs.append(make_job("Indeed", title, company, loc, link,
                                         posted=posted, salary=salary,
                                         experience="Fresher / 0-2 years"))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Indeed err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 6 - CUTSHORT (startup jobs)
# =============================================================================
def scrape_cutshort():
    jobs = []
    print("  Cutshort...")
    searches = [
        "python-developer",
        "data-analyst",
        "technical-support",
        "cloud-engineer",
        "data-science",
        "backend-developer",
        "software-engineer",
        "it-support",
    ]
    for kw in searches:
        try:
            url = f"https://cutshort.io/jobs?keywords={kw}&location=bengaluru&experience=0-2"
            resp = safe_get(url, HEADERS_MOZ)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            for scr in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(scr.string or "")
                    lst  = data if isinstance(data,list) else [data]
                    for jb in lst:
                        if not isinstance(jb,dict): continue
                        title   = jb.get("title","")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name","") if isinstance(org, dict) else ""
                        link    = jb.get("url","")
                        exp_txt = str(jb.get("experienceRequirements",""))
                        if not title or not is_relevant(title): continue
                        if not is_fresher(exp_txt): continue
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job("Cutshort", title, company,
                                             "Bengaluru, India", link))
                except: pass

            cards = (soup.find_all(["div","article"], class_=re.compile(r"job-card|jobCard|listing")) or
                     soup.find_all("div", class_=re.compile(r"card")))
            for card in cards[:10]:
                try:
                    te = card.find(["h2","h3","a"], class_=re.compile(r"title|role"))
                    company = extract_company_from_card(card, soup)
                    ae = card.find("a", href=True)
                    title   = (te.get_text(strip=True) if te else "").strip()
                    if not title or not is_relevant(title): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://cutshort.io{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Cutshort", title, company,
                                         "Bengaluru, India", link))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Cutshort err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 7 - WELLFOUND (AngelList)
# =============================================================================
def scrape_wellfound():
    jobs = []
    print("  Wellfound...")
    urls = [
        "https://wellfound.com/jobs?role=software-engineer&location=bengaluru&experience=0-2",
        "https://wellfound.com/jobs?role=data-analyst&location=bengaluru&experience=0-2",
        "https://wellfound.com/jobs?role=devops-engineer&location=bengaluru&experience=0-2",
        "https://wellfound.com/role/r/python-developer/bengaluru",
        "https://wellfound.com/role/r/data-scientist/bengaluru",
    ]
    for url in urls:
        try:
            resp = safe_get(url, HEADERS_CHROME)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            for scr in soup.find_all("script", id="__NEXT_DATA__"):
                try:
                    data  = json.loads(scr.string or "")
                    props = data.get("props",{}).get("pageProps",{})
                    jbs   = (props.get("jobs",[]) or
                             props.get("jobListings",[]) or
                             props.get("results",[]))
                    for jb in jbs[:10]:
                        title   = jb.get("title","") or jb.get("role","")
                        startup = jb.get("startup", {}) or {}
                        company = startup.get("name","") if isinstance(startup, dict) else ""
                        link    = (f"https://wellfound.com/jobs/{jb.get('id','')}"
                                   if jb.get("id") else url)
                        if not title or not is_relevant(title): continue
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job("Wellfound", title, company,
                                             "Bengaluru, India", link))
                except: pass

            for scr in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(scr.string or "")
                    lst  = data if isinstance(data,list) else [data]
                    for jb in lst:
                        if not isinstance(jb,dict): continue
                        title   = jb.get("title","")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name","") if isinstance(org, dict) else ""
                        link    = jb.get("url","")
                        if not title or not is_relevant(title): continue
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job("Wellfound", title, company,
                                             "Bengaluru, India", link))
                except: pass

            cards = soup.find_all(["div","a"], class_=re.compile(r"job|role|listing|card"))
            for card in cards[:10]:
                try:
                    te = card.find(["h2","h3","span"], class_=re.compile(r"title|role|job"))
                    company = extract_company_from_card(card, soup)
                    ae = card if card.name=="a" else card.find("a", href=re.compile(r"/jobs/|/role/"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    if not title or not is_relevant(title): continue
                    href = ae["href"] if ae and ae.get("href") else ""
                    link = (f"https://wellfound.com{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Wellfound", title, company,
                                         "Bengaluru, India", link))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Wellfound err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 8 - WORKINDIA
# =============================================================================
def scrape_workindia():
    jobs = []
    print("  WorkIndia...")
    urls = [
        "https://www.workindia.in/job-listing/python-developer-jobs-in-bangalore",
        "https://www.workindia.in/job-listing/data-analyst-jobs-in-bangalore",
        "https://www.workindia.in/job-listing/technical-support-jobs-in-bangalore",
        "https://www.workindia.in/job-listing/software-developer-jobs-in-bangalore",
        "https://www.workindia.in/job-listing/cloud-computing-jobs-in-bangalore",
    ]
    for url in urls:
        try:
            resp = safe_get(url, HEADERS_CHROME)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            for scr in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(scr.string or "")
                    lst  = data if isinstance(data,list) else [data]
                    for jb in lst:
                        if not isinstance(jb,dict): continue
                        title   = jb.get("title","")
                        org = jb.get("hiringOrganization", {}) or {}
                        company = org.get("name","") if isinstance(org, dict) else ""
                        link    = jb.get("url","")
                        if not title or not is_relevant(title): continue
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job("WorkIndia", title, company,
                                             "Bengaluru, India", link,
                                             experience="Fresher / 0-1 year"))
                except: pass

            cards = (soup.find_all("div", class_=re.compile(r"job|card|listing")) or
                     soup.find_all("li",  class_=re.compile(r"job|listing")))
            for card in cards[:10]:
                try:
                    te = card.find(["h2","h3","a"], class_=re.compile(r"title|job|role"))
                    company = extract_company_from_card(card, soup)
                    ae = card.find("a", href=True)
                    title   = (te.get_text(strip=True) if te else "").strip()
                    if not title or not is_relevant(title): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://www.workindia.in{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("WorkIndia", title, company,
                                         "Bengaluru, India", link,
                                         experience="Fresher / 0-1 year"))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    WorkIndia err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 9 - FRESHERSWORLD (NEW)
# =============================================================================
def scrape_freshersworld():
    jobs = []
    print("  Freshersworld...")
    urls = [
        "https://www.freshersworld.com/jobs/jobsearch/python-developer-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/data-analyst-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/technical-support-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/software-developer-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/cloud-computing-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/aws-devops-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/data-science-jobs-in-bangalore",
        "https://www.freshersworld.com/jobs/jobsearch/it-support-jobs-in-bangalore",
    ]
    for url in urls:
        try:
            resp = safe_get(url, HEADERS_CHROME)
            if not resp: continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # ld+json schema extraction
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(s.string or "")
                    lst  = data if isinstance(data, list) else [data]
                    for jb in lst:
                        if not isinstance(jb, dict): continue
                        if jb.get("@type") == "JobPosting":
                            title   = jb.get("title", "")
                            org = jb.get("hiringOrganization", {}) or {}
                            company = org.get("name", "") if isinstance(org, dict) else ""
                            link    = jb.get("url", "")
                            desc    = jb.get("description", "")
                            loc_data = jb.get("jobLocation", {})
                            loc = "Bengaluru, India"
                            if isinstance(loc_data, dict):
                                addr = loc_data.get("address", {})
                                if isinstance(addr, dict):
                                    city = addr.get("addressLocality", "")
                                    state = addr.get("addressRegion", "")
                                    if city: loc = f"{city}, {state}, India" if state else f"{city}, India"
                            date_posted = jb.get("datePosted", "Today")
                            if not title or not is_relevant(title): continue
                            company = clean_co(company) or "Company Not Disclosed"
                            jobs.append(make_job("Freshersworld", title, company,
                                                 loc, link, posted=date_posted,
                                                 description=desc, walkin=is_walkin(desc)))
                        # Freshersworld sometimes wraps jobs differently
                        elif "job" in str(jb).lower():
                            title = jb.get("title", "")
                            company = clean_co(jb.get("company", "")) or clean_co(jb.get("hiringOrganization", {}).get("name", "")) if isinstance(jb.get("hiringOrganization", {}), dict) else ""
                            link = jb.get("url", "")
                            if not title or not is_relevant(title): continue
                            company = company or "Company Not Disclosed"
                            jobs.append(make_job("Freshersworld", title, company,
                                                 "Bengaluru, India", link))
                except: pass

            # Freshersworld HTML card selectors
            cards = (soup.find_all("div", class_=re.compile(r"job-container|job-listing|job_item|opening-card")) or
                     soup.find_all("div", class_=re.compile(r"job-card|jobCard")) or
                     soup.find_all("li", class_=re.compile(r"job|listing")) or
                     soup.find_all("div", attrs={"data-job-id": True}) or
                     soup.find_all("div", class_=re.compile(r"result")))
            
            for card in cards[:12]:
                try:
                    te = (card.find(["h2", "h3", "a", "span"], class_=re.compile(r"title|job-title|heading")) or
                          card.find("a", href=re.compile(r"/jobs/|/job/")))
                    
                    company = extract_company_from_card(card, soup)
                    
                    # Freshersworld-specific company extraction
                    if not company:
                        for sel_tag in ["span", "div", "a", "h4"]:
                            ce = card.find(sel_tag, class_=re.compile(r"company-name|companyName|company|employer|org-name"))
                            if ce:
                                company = clean_co(ce.get_text(strip=True))
                                break
                        # Try next sibling of title
                        if not company and te:
                            parent = te.find_parent()
                            if parent:
                                for sibling in parent.find_all(["span", "div", "a"], recursive=False):
                                    text = sibling.get_text(strip=True)
                                    cleaned = clean_co(text)
                                    if cleaned and cleaned.lower() not in {"bengaluru", "bangalore", "hyderabad", "chennai", "pune", "mumbai"}:
                                        company = cleaned
                                        break
                    
                    ae = (card.find("a", href=re.compile(r"/jobs/|/job/")) or
                          card.find("a", href=True))
                    le = card.find(["span", "div"], class_=re.compile(r"location|loc"))
                    se = card.find(["span", "div"], class_=re.compile(r"salary|sal|ctc|lpa"))
                    
                    title = (te.get_text(strip=True) if te else "").strip()
                    loc = (le.get_text(strip=True) if le else "Bengaluru, India")
                    if not title or not is_relevant(title): continue
                    
                    href = ae["href"] if ae else ""
                    base = "https://www.freshersworld.com"
                    link = (f"{base}{href}" if href.startswith("/") else href) or url
                    
                    salary = se.get_text(strip=True) if se else ""
                    
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    
                    jobs.append(make_job("Freshersworld", title, company, loc, link,
                                         salary=salary, experience="Fresher / 0-1 year"))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Freshersworld err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# MAIN
# =============================================================================
def scrape_all_jobs():
    print(f"\n{'='*60}")
    print(f"  JOB SCRAPER v7.0 - Fixed Company Names + Indeed + Freshersworld")
    print(f"  {datetime.now().strftime('%d %b %Y %I:%M %p')}")
    print(f"  Platforms: 9 (GitHub Actions compatible)")
    print(f"  Profiles: Python Dev | Data Analyst | Tech Support | Cloud Computing")
    print(f"  0-2 YOE | Bengaluru ONLY | Startup & Mid-range Companies")
    print(f"{'='*60}\n")

    all_jobs = []
    scrapers = [
        ("LinkedIn",       scrape_linkedin),
        ("Internshala",    scrape_internshala),
        ("Foundit",        scrape_foundit),
        ("Naukri",         scrape_naukri),
        ("Indeed",         scrape_indeed),
        ("Cutshort",       scrape_cutshort),
        ("Wellfound",      scrape_wellfound),
        ("WorkIndia",      scrape_workindia),
        ("Freshersworld",  scrape_freshersworld),
    ]
    source_counts = {}
    for name, fn in scrapers:
        try:
            result = fn()
            source_counts[name] = len(result)
            all_jobs.extend(result)
        except Exception as e:
            print(f"    {name} crashed: {e}")
            source_counts[name] = 0

    unique = dedup(all_jobs)
    unique.sort(key=lambda x: x.get("ats_score",0), reverse=True)

    walkin_jobs  = [j for j in unique if j.get("is_walkin")]
    regular      = [j for j in unique if not j.get("is_walkin")]
    mnc_jobs     = [j for j in regular if j.get("company_type") == "MNC"]
    startup_jobs = [j for j in regular if j.get("company_type") == "Startup"]
    other_jobs   = [j for j in regular if j.get("company_type") == "Company"]

    result = {
        "scraped_at":    datetime.now().isoformat(),
        "ats_threshold": 0,
        "total_found":   len(unique),
        "walkin_count":  len(walkin_jobs),
        "mnc_count":     len(mnc_jobs),
        "startup_count": len(startup_jobs),
        "other_count":   len(other_jobs),
        "walkin_jobs":   walkin_jobs,
        "mnc_jobs":      mnc_jobs,
        "startup_jobs":  startup_jobs,
        "other_jobs":    other_jobs,
        "all_jobs":      unique,
        "source_counts": source_counts,
        "filter_stats": {
            "total_scraped":      len(all_jobs),
            "duplicates_removed": len(all_jobs) - len(unique),
            "inactive_removed":   0,
            "final_sent":         len(unique),
        }
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  TOTAL: {len(unique)} unique jobs from {len([s for s in source_counts if source_counts[s]>0])} platforms")
    print(f"  MNC: {len(mnc_jobs)} | Startup: {len(startup_jobs)} | Other: {len(other_jobs)} | Walk-in: {len(walkin_jobs)}")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    scrape_all_jobs()
