#!/usr/bin/env python3
"""
Daily Job Scraper - v6.0 (Multi-Profile Edition)
Scrapes 11 job platforms for:
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

def clean_co(name):
    """Clean company name - try harder to get actual names."""
    n = (name or "").strip()
    bad = {"n/a","na","company name n/a","unknown","not mentioned","confidential","confidential company","","-","null","none","."}
    n_lower = n.lower()
    # Remove common prefixes/suffixes
    n = re.sub(r'^(at|with|by|for)\s+', '', n, flags=re.IGNORECASE)
    n = re.sub(r'\s+(private\s+limited|pvt\.?\s+ltd\.?|limited|ltd\.?|inc\.?|corp\.?|corporation)$', '', n, flags=re.IGNORECASE)
    n = n.strip()
    if n_lower in bad or not n or len(n) < 2:
        return ""
    return n

def fallback_company_name(soup, default=""):
    """Try multiple methods to extract company name from page."""
    # Method 1: ld+json schema
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
            lst = data if isinstance(data, list) else [data]
            for jb in lst:
                if isinstance(jb, dict):
                    org = jb.get("hiringOrganization", {})
                    if isinstance(org, dict):
                        name = org.get("name", "")
                        if name and clean_co(name):
                            return clean_co(name)
        except:
            pass
    # Method 2: Meta tags
    for meta in soup.find_all("meta", property=["og:site_name", "twitter:site"]):
        name = meta.get("content", "")
        if name and clean_co(name):
            return clean_co(name)
    # Method 3: Common company elements
    for sel in ['a[href*="company"]', 'a[href*="employer"]',
                '[class*="company"]', '[class*="employer"]', '[class*="org"]']:
        try:
            el = soup.select_one(sel)
            if el:
                name = el.get_text(strip=True)
                if name and clean_co(name):
                    return clean_co(name)
        except:
            pass
    return default

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
    co    = clean_co(company)
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


def extract_company_name(element, soup=None):
    """Robust company name extraction with multiple fallbacks."""
    if element:
        text = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element).strip()
        cleaned = clean_co(text)
        if cleaned:
            return cleaned
    # Try to find company name from nearby elements or soup
    if soup:
        return fallback_company_name(soup, "")
    return ""


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
                        # Also check nested JobPosting
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
                    if not ce:
                        link_a = card.find("a", class_=re.compile(r"hidden|screen-reader"))
                        if link_a:
                            aria = link_a.get("aria-label","")
                            m = re.search(r'at\s+([A-Za-z0-9\s&.,]+)', aria)
                            if m:
                                company = clean_co(m.group(1).strip())
                            else:
                                company = ""
                        else:
                            company = ""
                    else:
                        company = extract_company_name(ce, soup)

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
                    # Try multiple company selectors
                    ce = None
                    for sel_pattern in [r"company-name", r"company", r"employer", r"organization", r"org-name"]:
                        for tag in ["p", "a", "span", "div", "h4"]:
                            ce = card.find(tag, class_=re.compile(sel_pattern))
                            if ce: break
                        if ce: break
                    se = card.find("span", class_=re.compile(r"stipend|salary|cta"))
                    ae = card.find("a", href=re.compile(r"/jobs/detail/|/internships/detail/"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
                    if not title or not is_relevant(title): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://internshala.com{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        # Try to get from the job link or page title
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
                        jobs.append(make_job("Foundit", title, company or "Company Not Disclosed",
                                             "Bengaluru, India", link,
                                             description=desc, walkin=is_walkin(desc)))
                except: pass

            cards = (soup.find_all("div", class_=re.compile(r"card-apply-content|job-tittle|jobCard|cardContainer")) or
                     soup.find_all("article", class_=re.compile(r"jobCard|job-card|cardContainer")) or
                     soup.find_all("div", class_=re.compile(r"jobCard")))
            for card in cards[:12]:
                try:
                    te = card.find(["h3","h2","a"], class_=re.compile(r"title|jobTitle|job-title"))
                    ce = None
                    for tag in ["span", "a", "p", "div"]:
                        ce = card.find(tag, class_=re.compile(r"company|companyName|employer|org-name"))
                        if ce: break
                    ae = card.find("a", href=re.compile(r"/job-detail/|/jobs/"))
                    ee = card.find(["span","div"], class_=re.compile(r"exp|experience"))
                    se = card.find(["span"], class_=re.compile(r"sal|salary"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
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
# SCRAPER 5 - INSTAHIRE
# =============================================================================
def scrape_instahire():
    jobs = []
    print("  Instahire...")
    searches = [
        "python+developer",
        "data+analyst",
        "technical+support",
        "cloud+engineer",
        "aws+devops",
        "software+developer",
        "data+science",
        "it+support",
    ]
    for kw in searches:
        try:
            url = f"https://instahire.app/jobs?q={kw}&location=bangalore&exp=0-2"
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
                        jobs.append(make_job("Instahire", title, company,
                                             "Bengaluru, India", link))
                except: pass

            cards = (soup.find_all("div", class_=re.compile(r"job.?card|jobcard|job-item|listing")) or
                     soup.find_all("li",  class_=re.compile(r"job|listing")) or
                     soup.find_all("article"))
            for card in cards[:12]:
                try:
                    te = card.find(["h2","h3","a"], class_=re.compile(r"title|role|heading|job"))
                    ce = None
                    for tag in ["span", "p", "a", "div"]:
                        ce = card.find(tag, class_=re.compile(r"company|org|employer"))
                        if ce: break
                    ae = card.find("a", href=True)
                    ee = card.find(["span","div"], class_=re.compile(r"exp|experience"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
                    exp_txt = (ee.get_text(strip=True) if ee else "")
                    if not title or not is_relevant(title): continue
                    if not is_fresher(exp_txt): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://instahire.app{href}"
                            if href.startswith("/") else href) or url
                    ct   = card.get_text()
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Instahire", title, company,
                                         "Bengaluru, India", link,
                                         experience=exp_txt or "0-2 years (Fresher)",
                                         **extract_contact(ct)))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Instahire err: {e}")
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
                    ce = None
                    for tag in ["span", "p", "div"]:
                        ce = card.find(tag, class_=re.compile(r"company|startup|employer"))
                        if ce: break
                    ae = card.find("a", href=True)
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
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
# SCRAPER 7 - HIRIST
# =============================================================================
def scrape_hirist():
    jobs = []
    print("  Hirist...")
    urls = [
        "https://www.hirist.tech/j/python-developer-jobs-in-bangalore/38?experience=0-2",
        "https://www.hirist.tech/j/data-analyst-jobs-in-bangalore/38?experience=0-2",
        "https://www.hirist.tech/j/technical-support-jobs-in-bangalore/38?experience=0-2",
        "https://www.hirist.tech/j/cloud-engineer-jobs-in-bangalore/38?experience=0-2",
        "https://www.hirist.tech/j/data-science-jobs-in-bangalore/38?experience=0-2",
        "https://www.hirist.tech/j/software-developer-jobs-in-bangalore/38?experience=0-2",
    ]
    for url in urls:
        try:
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
                        jobs.append(make_job("Hirist", title, company,
                                             "Bengaluru, India", link,
                                             experience=exp_txt or "0-2 years"))
                except: pass

            cards = (soup.find_all(["div","li"], class_=re.compile(r"job-listing|job-card|jobCard")) or
                     soup.find_all("div", class_=re.compile(r"card")))
            for card in cards[:10]:
                try:
                    te = card.find(["h2","h3","a"], class_=re.compile(r"title|job-title"))
                    ce = None
                    for tag in ["span", "div", "p"]:
                        ce = card.find(tag, class_=re.compile(r"company|employer|org"))
                        if ce: break
                    ae = card.find("a", href=True)
                    ee = card.find(["span","div"], class_=re.compile(r"exp|experience|year"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
                    exp_txt = (ee.get_text(strip=True) if ee else "")
                    if not title or not is_relevant(title): continue
                    if not is_fresher(exp_txt): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://www.hirist.tech{href}"
                            if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Hirist", title, company,
                                         "Bengaluru, India", link,
                                         experience=exp_txt or "0-2 years"))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Hirist err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 8 - WELLFOUND (AngelList)
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
                    ce = None
                    for tag in ["span", "div", "a"]:
                        ce = card.find(tag, class_=re.compile(r"company|startup"))
                        if ce: break
                    ae = card if card.name=="a" else card.find("a", href=re.compile(r"/jobs/|/role/"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
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
# SCRAPER 9 - NAUKRICITY / iimjobs
# =============================================================================
def scrape_naukricity():
    jobs = []
    print("  Naukricity / iimjobs...")
    urls = [
        "https://www.naukricity.com/jobs/python-developer-jobs-in-bengaluru-0-2-years/",
        "https://www.naukricity.com/jobs/data-analyst-jobs-in-bengaluru-0-2-years/",
        "https://www.naukricity.com/jobs/technical-support-jobs-in-bengaluru-0-2-years/",
        "https://www.naukricity.com/jobs/cloud-engineer-jobs-in-bengaluru-0-2-years/",
        "https://www.naukricity.com/jobs/software-engineer-jobs-in-bengaluru-freshers/",
        "https://www.iimjobs.com/j/software-engineer-0-2-yrs-1.html?industryId=37&locationId=3",
        "https://www.iimjobs.com/j/data-analyst-0-2-yrs-1.html?industryId=37&locationId=3",
    ]
    for url in urls:
        try:
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
                        src = "iimjobs" if "iimjobs" in url else "Naukricity"
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job(src, title, company,
                                             "Bengaluru, India", link))
                except: pass

            cards = soup.find_all(["div","li"], class_=re.compile(r"job|listing|result"))
            for card in cards[:10]:
                try:
                    te = card.find(["h2","h3","h4","a"], class_=re.compile(r"title|job|role"))
                    ce = None
                    for tag in ["span", "p", "div"]:
                        ce = card.find(tag, class_=re.compile(r"company|employer"))
                        if ce: break
                    ae = card.find("a", href=True)
                    ee = card.find(["span"], class_=re.compile(r"exp|experience|year"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
                    exp_txt = (ee.get_text(strip=True) if ee else "")
                    if not title or not is_relevant(title): continue
                    if not is_fresher(exp_txt): continue
                    href = ae["href"] if ae else ""
                    base = "https://www.iimjobs.com" if "iimjobs" in url else "https://www.naukricity.com"
                    link = (f"{base}{href}" if href.startswith("/") else href) or url
                    src  = "iimjobs" if "iimjobs" in url else "Naukricity"
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job(src, title, company,
                                         "Bengaluru, India", link,
                                         experience=exp_txt or "0-2 years (Fresher)"))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Naukricity/iimjobs err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 10 - APNA.CO
# =============================================================================
def scrape_apna():
    jobs = []
    print("  Apna.co...")
    searches = [
        "python-developer",
        "data-analyst",
        "technical-support",
        "cloud-engineer",
        "software-developer",
        "data-science",
        "it-support",
    ]
    for kw in searches:
        try:
            url = f"https://apna.co/job/all-jobs/{kw}-jobs-in-bengaluru"
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
                        sal     = str(jb.get("baseSalary",{}).get("value",""))
                        if not title or not is_relevant(title): continue
                        company = clean_co(company) or fallback_company_name(soup) or "Company Not Disclosed"
                        jobs.append(make_job("Apna.co", title, company,
                                             "Bengaluru, India", link,
                                             salary=sal,
                                             experience="Fresher / 0-1 year"))
                except: pass

            cards = (soup.find_all("div", class_=re.compile(r"job-card|jobCard|job_card")) or
                     soup.find_all("div", class_=re.compile(r"card")))
            for card in cards[:10]:
                try:
                    te = card.find(["h2","h3","span"], class_=re.compile(r"title|role|job"))
                    ce = None
                    for tag in ["span", "p"]:
                        ce = card.find(tag, class_=re.compile(r"company|employer"))
                        if ce: break
                    ae = card.find("a", href=True)
                    se = card.find(["span","div"], class_=re.compile(r"sal|salary"))
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
                    if not title or not is_relevant(title): continue
                    href = ae["href"] if ae else ""
                    link = (f"https://apna.co{href}" if href.startswith("/") else href) or url
                    if not company:
                        company = fallback_company_name(soup) or "Company Not Disclosed"
                    jobs.append(make_job("Apna.co", title, company,
                                         "Bengaluru, India", link,
                                         salary=se.get_text(strip=True) if se else "",
                                         experience="Fresher / 0-1 year"))
                except: continue
            time.sleep(2)
        except Exception as e:
            print(f"    Apna err: {e}")
    r = dedup(jobs)
    print(f"    {len(r)} jobs")
    return r


# =============================================================================
# SCRAPER 11 - WORKINDIA
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
                    ce = None
                    for tag in ["span", "p"]:
                        ce = card.find(tag, class_=re.compile(r"company|employer"))
                        if ce: break
                    ae = card.find("a", href=True)
                    title   = (te.get_text(strip=True) if te else "").strip()
                    company = extract_company_name(ce, soup)
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
# MAIN
# =============================================================================
def scrape_all_jobs():
    print(f"\n{'='*60}")
    print(f"  JOB SCRAPER v6.0 - Multi-Profile Edition")
    print(f"  {datetime.now().strftime('%d %b %Y %I:%M %p')}")
    print(f"  Platforms: 11 (GitHub Actions compatible)")
    print(f"  Profiles: Python Dev | Data Analyst | Tech Support | Cloud Computing")
    print(f"  0-2 YOE | Bengaluru ONLY")
    print(f"{'='*60}\n")

    all_jobs = []
    scrapers = [
        ("LinkedIn",         scrape_linkedin),
        ("Internshala",      scrape_internshala),
        ("Foundit",          scrape_foundit),
        ("Naukri",           scrape_naukri),
        ("Instahire",        scrape_instahire),
        ("Cutshort",         scrape_cutshort),
        ("Hirist",           scrape_hirist),
        ("Wellfound",        scrape_wellfound),
        ("Naukricity/iimjobs",scrape_naukricity),
        ("Apna.co",          scrape_apna),
        ("WorkIndia",        scrape_workindia),
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
