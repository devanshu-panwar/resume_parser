import re
import spacy
from collections import defaultdict
import dateparser

nlp = spacy.load("en_core_web_lg")  # Use the larger model


def extract_contact_info(text):
    """Extracts name, email, phone number, and address from text."""

    info = {"name": extract_name(text), "email": None, "phone": None, "address": None, "linkedin": None, "skills": None,
            "experience": None}

    # Extract Name (using spaCy NER)
    # Use the improved name extraction

    # Extract Email
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        info["email"] = email_match.group(0)

    # Extract Phone Number (US and common international formats)
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if phone_match:
        info["phone"] = phone_match.group(0)

    # Extract Address (using spaCy GPE and other location entities)
    # Use the improved address extraction
    info["address"] = extract_address(text)

    # Extract LinkedIn Profile
    linkedin_match = re.search(r"(https?://|www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", text)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(0)
    # else: #try to find linkedin profile by name.
    #     if info["name"]:
    #         info["linkedin"] = find_linkedin_profile_by_name(info["name"])

    # Extract Skills (using the provided function)
    info["skills"] = extract_skills(text, skills_list)

    # Extract Experience (basic keyword-based extraction)
    info["experience"] = extract_experience(text)
    # experience_keywords = ["experience", "work history", "employment", "professional experience"]
    # for keyword in experience_keywords:
    #     match = re.search(keyword, text, re.IGNORECASE)
    #     if match:
    #         start_index = match.start()
    #         info["experience"] = text[start_index:]
    #         break

    return info


# def extract_name(text):
#     """Extracts name from resume text using an LLM (locally)."""

#     nlp = pipeline("question-answering", model="distilbert-base-cased-distilled-squad",force_download=True)
#     question = "What is the person's name?"
#     result = nlp(question=question, context=text)
#     return result["answer"]

def extract_name(text):
    """Extracts name with advanced regex and contextual scoring."""

    name = None
    name_score = 0

    # 1. SpaCy and Regex (Prioritized)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            regex_patterns = [
                r"([A-Z][a-z]+(?:-[A-Z][a-z]+)? [A-Z][a-z]+(?: [A-Z][a-z]+)?)",
                r"([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)",
                r"([A-Z][a-z]+ [A-Z] [A-Z][a-z]+)"
            ]
            for pattern in regex_patterns:
                match = re.search(pattern, ent.text)
                if match:
                    name = match.group(0)
                    name_score = 10  # high score for spaCy match
                    break
            if name:
                break

    # 2. Contextual Scoring
    if not name:
        name_keywords = ["name", "contact", "profile", "summary", "personal", "about me", "introduction"]
        for keyword in name_keywords:
            for match in re.finditer(r"\b" + re.escape(keyword) + r"\b", text.lower()):
                keyword_index = match.start()
                search_range = text[max(0, keyword_index - 200):min(len(text), keyword_index + 200)]
                regex_patterns = [
                    r"([A-Z][a-z]+(?:-[A-Z][a-z]+)? [A-Z][a-z]+(?: [A-Z][a-z]+)?)",
                    r"([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)",
                    r"([A-Z][a-z]+ [A-Z] [A-Z][a-z]+)"
                ]
                for pattern in regex_patterns:
                    name_match = re.search(pattern, search_range)
                    if name_match:
                        current_score = 5  # base score
                        if keyword.lower() in ["name", "contact"]:
                            current_score += 3  # boost score for key keywords
                        if name_match.start() < 50:
                            current_score += 2  # boost score if near the top of the context.

                        if current_score > name_score:
                            name = name_match.group(0)
                            name_score = current_score

    # 3. Improved Fallback
    if not name:
        top_text = text[:500]
        regex_patterns = [
            r"([A-Z][a-z]+(?:-[A-Z][a-z]+)? [A-Z][a-z]+(?: [A-Z][a-z]+)?)",
            r"([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)",
            r"([A-Z][a-z]+ [A-Z] [A-Z][a-z]+)"
        ]
        for pattern in regex_patterns:
            match = re.search(pattern, top_text)
            if match:
                name = match.group(0)
                name_score = 1  # very low score.
                break

    # 4. Post-processing
    if name:
        name = re.sub(r"^(Mr\.|Ms\.|Dr\.|Prof\.|Mrs\.|Miss)\s*", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"\s+", " ", name).strip()

    return name


def parse_address(text):
    pass


def extract_address(text):
    """Extracts address from text with improved date range handling."""

    address = None

    # Contextual Analysis
    address_section = None
    address_keywords = ["address", "location", "residence", "contact information", "mailing address",
                        "place of residence", "current location"]

    for keyword in address_keywords:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE):
            keyword_index = text.lower().find(keyword.lower())
            address_section = text[max(0, keyword_index - 300):min(len(text), keyword_index + 300)]
            break

    if address_section:
        text = address_section

    # libpostal Parsing
    try:
        parsed_address = parse_address(text)
        if parsed_address:
            address_components = [component[0] for component in parsed_address]
            address = ", ".join(address_components)
    except:
        pass

    # spaCy Enhancement
    if not address:
        doc = nlp(text)
        address_parts = []
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC", "FAC"]:
                address_parts.append(ent.text)
        if address_parts:
            address = ", ".join(address_parts)
            address_patterns = [
                r"\d+\s+[\w\s.-]+(?:(?:apt|suite|#)\s*\d+)?,\s*[\w\s.-]+(?:,\s*[A-Z]{2})?(?:,\s*[A-Za-z]+)?\s*\d{5}(?:-\d{4})?",
                r"\d+\s+[\w\s.-]+(?:(?:apt|suite|#)\s*\d+)?,\s*[\w\s.-]+(?:,\s*[A-Z]{2})?(?:,\s*[A-Za-z]+)?",
                r"[\w\s.-]+,\s*[A-Z]{2}\s*\d{5}(?:,\s*[A-Za-z]+)?",
                r"[\w\s.-]+,\s*[A-Z]{2}(?:,\s*[A-Za-z]+)?",
                r"\d+\s+[\w\s.-]+(?:(?:apt|suite|#)\s*\d+)?",
                r"\d{5}",
                r"[A-Za-z]+(?:,\s*[A-Za-z]+)?"
            ]
            for pattern in address_patterns:
                match = re.search(pattern, address, re.IGNORECASE)
                if match:
                    address = match.group(0)
                    break

    # Post-processing (Date Range Removal)
    if address:
        address = re.sub(r"\s+", " ", address).strip()
        address = re.sub(r"[,.]+$", "", address).strip()

        # Remove date ranges
        address = re.sub(r"\d{4}\s*-\s*[A-Za-z]+\s*\d{4}", "", address).strip()  # YYYY - Month YYYY
        address = re.sub(r"\d{4}\s*-\s*\d{4}", "", address).strip()  # YYYY - YYYY
        address = re.sub(r"[A-Za-z]+\s*\d{4}", "", address).strip()  # Month YYYY
        address = re.sub(r"\d{4}", "", address).strip()  # YYYY

        address_list = address.split(", ")
        seen = set()
        address_list_filtered = [x for x in address_list if not (x in seen or seen.add(x))]
        address = ", ".join(address_list_filtered)

    return address.strip()


skills_list = [
    # AI & Machine Learning
    "Machine Learning", "Deep Learning", "Natural Language Processing", "NLP",
    "Computer Vision", "Reinforcement Learning", "TensorFlow", "PyTorch", "Keras",
    "Scikit-learn", "OpenCV", "Hugging Face Transformers", "LLaMA Models", "Generative AI",
    "LangChain", "AutoML", "ONNX", "Speech Recognition", "Chatbots", "Prompt Engineering",
    # Data Science & Data Engineering
    "Python", "R", "SQL", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Scipy",
    "Data Visualization", "Big Data", "Apache Spark", "Hadoop", "Airflow",
    "Snowflake", "Databricks", "Power BI", "Tableau", "Data Warehousing",
    "ETL Pipelines", "Feature Engineering", "Statistical Analysis", "Bayesian Inference",
    "Time Series Analysis",
    # Web Development (Frontend)
    "HTML", "CSS", "JavaScript", "React.js", "Next.js", "Vue.js", "Angular", "Svelte",
    "TypeScript", "Bootstrap", "Tailwind CSS", "jQuery",
    # Web Development (Backend)
    "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Ruby on Rails",
    "Laravel", "Spring Boot", ".NET Core",
    # Databases & APIs
    "MySQL", "PostgreSQL", "MongoDB", "Firebase", "REST APIs", "GraphQL", "WebSockets",
    # DevOps & Cloud
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Jenkins",
    "GitHub Actions", "Terraform",
    # Mobile App Development (Native)
    "Java", "Kotlin", "Swift", "Objective-C",
    # Mobile App Development (Cross-Platform)
    "Flutter", "Dart", "React Native", "Xamarin", "Ionic", "Unity",
    # Salesforce
    "Salesforce", "Salesforce Lightning", "Apex Programming", "Visualforce",
    "Salesforce Flow", "Salesforce API Integration", "SOQL", "SOSL",
    "Einstein AI", "Marketing Cloud", "Service Cloud", "Sales Cloud",
    # Additional Skills
    "Git", "GitHub", "Agile", "Scrum", "JIRA", "Linux", "Shell Scripting", "Cybersecurity"
]


def extract_skills(text, skills_list):
    # Convert text to lowercase for case-insensitive matching
    text = text.lower()
    # Extract words from text using regex
    words = re.findall(r'\b[a-zA-Z0-9+#.]+\b', text)
    # Find matching skills
    found_skills = set(skill for skill in skills_list if skill.lower() in words)
    return list(found_skills)


# Predefined common job titles for better accuracy
COMMON_JOB_TITLES = [
    "Software Engineer", "Web Developer", "Data Scientist", "Product Manager", "Consultant",
    "Intern", "Manager", "Analyst", "Administrator", "Developer", "Lead", "Director", "Technician",
    "Architect", "Specialist", "Engineer", "Designer", "Researcher"
]


def extract_experience(text):
    """Extracts company, title, and dates from resume text, focusing on the first line."""

    experience_sections = []
    experience_pattern = re.compile(
        r"(WORK EXPERIENCE|Professional Experience|Employment History|Employment)(.*?)(?=(EDUCATION|SKILLS|PROJECTS|REFERENCES|\Z))",
        re.DOTALL | re.IGNORECASE
    )

    experience_matches = experience_pattern.finditer(text)

    for match in experience_matches:
        experience_text = match.group(2).strip()
        job_entries = experience_text.split('\n\n')  # Split into job entries

        for job_entry in job_entries:
            lines = job_entry.split('\n')
            if lines:
                first_line = lines[0].strip()  # Get the first line
                experience_sections.append(first_line)

    return experience_sections


def parse_dates(dates_text):
    """Parses date ranges with enhanced handling."""
    dates = []
    date_parts = dates_text.split(" - ")
    for date_str in date_parts:
        parsed_date = dateparser.parse(date_str, settings={'STRICT_PARSING': True})
        if parsed_date:
            dates.append(parsed_date.strftime("%Y-%m-%d"))
        else:
            dates.append(date_str.strip())  # If date is not parsed, return the original string.
    return dates
