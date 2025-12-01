import json
import re

def extract_skills_from_profile(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    profile = data[0] if isinstance(data, list) else data

    # Combine headline and summary
    headline = profile.get("Headline", "")
    summary = profile.get("Summary", "")
    combined = f"{headline} {summary}".lower()

    # List of common tech skills and keywords to look for
    skill_keywords = [
        "UI/UX", "Web", "Innovation", "C#", "Microsoft SQL", "SQL", "Ms Office",
        "database management system", "networking", "Photoshop", "graphics designing", ".NET", "PHP", "WAMP", "LAMP",
        "C", "C++", "Java", "Python", "HTML", "JavaScript", "logical programming", "debugging", "cloud", 
        "AWS", "Azure", "GCP", "machine learning", "AI", "artificial intelligence", "deep learning", "NLP", "natural language processing", "data science",
        "data engineering", "data analytics", "data mining", "data warehousing", "ETL", "big data", "Hadoop", "Spark",
        "data visualization", "Tableau", "Power BI", "Excel", "statistics", "data modeling", "data governance", "data quality", "data security", "data privacy", "data compliance",
        "business intelligence", "BI", "SQL Server", "MySQL", "PostgreSQL", "MongoDB", "NoSQL", "GraphQL",
        "mobile development", "iOS", "Android", "React Native", "Flutter",  "Swift", "Kotlin", "Java for Android","Agile", "Scrum", "Kanban", "DevOps", "CI/CD", "continuous integration", "continuous deployment",
        "version control", "Git", "GitHub", "GitLab", "Bitbucket", 
        "API", "REST", "GraphQL", "microservices", "Docker", "Kubernetes", "containerization", "orchestration",
        "testing", "QA", "quality assurance", "automation testing", "manual testing", 
        "data analysis", "data visualization", "statistics", "R", "MATLAB", "TensorFlow", "Keras", "PyTorch", "scikit-learn",
        "data science", "big data", "DevOps", "Agile", "Scrum", "Kanban", "CI/CD", "continuous integration", "continuous deployment",
        "REST", "API", "microservices", "Docker", "Kubernetes", "Git", "version control",
        "testing", "QA", "quality assurance", "automation", "manual testing", "selenium", "Jenkins",
        "performance testing", "load testing", "security testing", "penetration testing", "vulnerability assessment", 
        "compliance", "GDPR", "HIPAA", "PCI DSS", "ISO 27001", "ITIL", "ITSM", "ITIL4", "IT service management", "service desk", "incident management", "problem management", "change management",
        "networking", "TCP/IP", "DNS", "DHCP", "firewall", "VPN", "LAN", "WAN", "network security",
        "cloud computing", "AWS", "Azure", "Google Cloud", "GCP", "cloud architecture", "cloud security", "cloud migration", "cloud deployment",
        "cybersecurity", "information security", "data protection", "encryption", "firewall", "threat intelligence", "vulnerability management",
    ]

    found_skills = []
    for skill in skill_keywords:
        if skill.lower() in combined and skill not in found_skills:
            found_skills.append(skill)

    return found_skills
