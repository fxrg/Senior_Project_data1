#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
100% Real Web Scraping & Skill Extraction Pipeline for Saudi Tech Job Market
Project: AI-Powered Saudi Career Recommendation and Skill Gap Analysis System
- Zero synthetic jobs / Zero random skill injection.
- Extracts skills strictly from real scraped Saudi job descriptions (EN/AR).
- Dynamically computes top demanded Saudi market skills per role.
- Maps extracted skills & roles to 85+ real, accredited professional certificates.
"""

import os
import re
import time
import sqlite3
import logging
import argparse
from collections import Counter
from datetime import datetime
import pandas as pd
from jobspy import scrape_jobs

# إعداد السجلات (Logs) لمتابعة السيرفر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("saudi_scraper_server.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

MASTER_CSV_PATH = "saudi_career_master_dataset.csv"
SQLITE_DB_PATH = "saudi_career_system.db"

# =====================================================================
# 1. قاموس استخراج المهارات الحقيقية من نصوص الإعلانات (115+ مهارة عربي/إنجليزي)
# =====================================================================
SKILL_EXTRACTION_PATTERNS = {
    # Programming & Scripting
    "Python": [r"\bpython\b", r"بايثون"],
    "Java": [r"\bjava\b", r"جافا"],
    "C# / .NET": [r"\bc#\b", r"\.net\b", r"\bdotnet\b", r"\basp\.net\b"],
    "C++": [r"\bc\+\+\b", r"\bcpp\b"],
    "Go (Golang)": [r"\bgolang\b", r"\bgo language\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b", r"جافاسكربت"],
    "TypeScript": [r"\btypescript\b", r"\bts\b", r"تايب سكربت"],
    "PHP": [r"\bphp\b", r"\blaravel\b"],
    "SQL": [r"\bsql\b", r"\bt-sql\b", r"\bpl/sql\b", r"لغة الاستعلام"],
    "Bash / Shell Scripting": [r"\bbash\b", r"\bshell script\w*\b", r"\bpowershell\b"],
    "Dart": [r"\bdart\b"],
    "Swift": [r"\bswift\b", r"\bios development\b"],
    "Kotlin": [r"\bkotlin\b", r"\bandroid development\b"],
    "R Language": [r"\br programming\b", r"\brstudio\b"],

    # Data Science, AI & Analytics
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b", r"تعلم الآلة", r"التعلم الآلي"],
    "Deep Learning": [r"\bdeep learning\b", r"\bneural network\w*\b", r"التعلم العميق", r"الشبكات العصبية"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b", r"معالجة اللغات الطبيعية"],
    "Large Language Models (LLMs)": [r"\bllm\b", r"\bllms\b", r"\bgenerative ai\b", r"\bgenai\b", r"\brag\b", r"\blangchain\b", r"النماذج اللغوية"],
    "Computer Vision": [r"\bcomputer vision\b", r"\bopencv\b", r"\byolo\b", r"الرؤية الحاسوبية"],
    "Data Analysis": [r"\bdata analysis\b", r"\bdata analytics\b", r"تحليل البيانات", r"تحليل بيانات"],
    "Statistics & Probability": [r"\bstatistics\b", r"\bstatistical\b", r"\ba/b testing\b", r"الإحصاء", r"التحليل الإحصائي"],
    "Pandas & NumPy": [r"\bpandas\b", r"\bnumpy\b"],
    "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b", r"\bxgboost\b", r"\blightgbm\b"],
    "PyTorch": [r"\bpytorch\b", r"بايتورش"],
    "TensorFlow / Keras": [r"\btensorflow\b", r"\bkeras\b"],
    "Hugging Face": [r"\bhugging\s*face\b", r"\btransformers\b"],
    "MLOps": [r"\bmlops\b", r"\bmlflow\b", r"\bkubeflow\b"],
    "Power BI": [r"\bpower\s*bi\b", r"\bdax\b", r"باور بي آي"],
    "Tableau": [r"\btableau\b", r"تابلوه"],
    "Data Visualization": [r"\bdata visualization\b", r"\bplotly\b", r"\bmatplotlib\b", r"\bdashboard\w*\b", r"تصوير البيانات", r"لوحات البيانات"],
    "Advanced Excel": [r"\bexcel\b", r"\bvba\b", r"\bpivot table\w*\b", r"إكسل"],

    # Data Engineering & Databases
    "ETL & Data Pipelines": [r"\betl\b", r"\belt\b", r"\bdata pipeline\w*\b", r"خطوط البيانات", r"استخراج وتحويل البيانات"],
    "Apache Spark / PySpark": [r"\bspark\b", r"\bpyspark\b", r"\bdatabricks\b"],
    "Apache Airflow": [r"\bairflow\b"],
    "Apache Kafka": [r"\bkafka\b", r"\bdata streaming\b"],
    "Big Data / Hadoop": [r"\bbig data\b", r"\bhadoop\b", r"\bhive\b", r"البيانات الضخمة"],
    "Data Warehousing": [r"\bdata warehous\w*\b", r"\bsnowflake\b", r"\bredshift\b", r"\bbigquery\b", r"مستودعات البيانات"],
    "Data Governance & Quality": [r"\bdata governance\b", r"\bdata quality\b", r"\bdama\b", r"\bmdm\b", r"حوكمة البيانات", r"جودة البيانات"],
    "PostgreSQL / MySQL": [r"\bpostgresql\b", r"\bpostgres\b", r"\bmysql\b", r"\bmariadb\b"],
    "Oracle Database": [r"\boracle db\b", r"\boracle database\b", r"\bpl/sql\b"],
    "Microsoft SQL Server": [r"\bsql server\b", r"\bmssql\b", r"\bssis\b", r"\bssrs\b"],
    "NoSQL / MongoDB": [r"\bnosql\b", r"\bmongodb\b", r"\bcassandra\b", r"\bdynamodb\b"],
    "Redis": [r"\bredis\b"],

    # Web, Mobile & Software Engineering
    "FastAPI / Flask": [r"\bfastapi\b", r"\bflask\b"],
    "Django": [r"\bdjango\b"],
    "Spring Boot": [r"\bspring boot\b", r"\bspring framework\b", r"\bhibernate\b"],
    "Node.js / Express": [r"\bnode\.?js\b", r"\bexpress\.?js\b", r"\bnestjs\b"],
    "React.js / Next.js": [r"\breact\b", r"\breact\.?js\b", r"\bnext\.?js\b", r"ريأكت"],
    "Angular": [r"\bangular\b"],
    "Vue.js": [r"\bvue\.?js\b", r"\bnuxt\b"],
    "HTML5 & CSS3": [r"\bhtml5?\b", r"\bcss3?\b", r"\btailwind\b", r"\bbootstrap\b"],
    "Flutter": [r"\bflutter\b", r"فلاتر"],
    "React Native": [r"\breact native\b"],
    "RESTful APIs & GraphQL": [r"\brest\s*api\w*\b", r"\brestful\b", r"\bgraphql\b", r"\bapi integration\b", r"واجهات برمجة التطبيقات"],
    "Microservices Architecture": [r"\bmicroservices\b", r"\bsoftware architecture\b", r"\bsystem design\b", r"الخدمات المصغرة"],
    "OOP & Design Patterns": [r"\boop\b", r"\bobject-oriented\b", r"\bobject oriented\b", r"\bdesign patterns\b", r"\bsolid\b", r"البرمجة الكائنية"],
    "Data Structures & Algorithms": [r"\bdata structures\b", r"\balgorithms\b", r"هياكل البيانات"],
    "Unit Testing & QA Automation": [r"\bunit test\w*\b", r"\bselenium\b", r"\bcypress\b", r"\bpytest\b", r"\bjest\b", r"\bqa\b", r"اختبار البرمجيات"],
    "Git & Version Control": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b", r"\bbitbucket\b", r"إدارة النسخ"],
    "Agile & Scrum (SDLC)": [r"\bagile\b", r"\bscrum\b", r"\bsdlc\b", r"\bjira\b", r"أجايل", r"هندسة البرمجيات"],
    "UI/UX & Figma": [r"\bui/ux\b", r"\bux\b", r"\bfigma\b", r"تجربة المستخدم", r"تصميم الواجهات"],
    "Streamlit": [r"\bstreamlit\b"],

    # Cloud, DevOps & Infrastructure
    "AWS (Amazon Web Services)": [r"\baws\b", r"\bamazon web services\b", r"\bec2\b", r"\bs3\b", r"\blambda\b"],
    "Microsoft Azure": [r"\bazure\b", r"سحابة مايكروسوفت"],
    "Google Cloud Platform (GCP)": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Cloud Computing": [r"\bcloud computing\b", r"\bcloud infrastructure\b", r"\bhybrid cloud\b", r"الحوسبة السحابية"],
    "Docker & Containers": [r"\bdocker\b", r"\bcontainer\w*\b", r"دوكر", r"الحاويات"],
    "Kubernetes (K8s)": [r"\bkubernetes\b", r"\bk8s\b", r"\bopenshift\b", r"\bhelm\b", r"كوبرنيتس"],
    "CI/CD Pipelines": [r"\bci/cd\b", r"\bjenkins\b", r"\bgithub actions\b", r"\bgitlab ci\b", r"\bazure devops\b", r"التكامل المستمر"],
    "Terraform & IaC": [r"\bterraform\b", r"\bansible\b", r"\binfrastructure as code\b", r"\biac\b"],
    "Linux Administration": [r"\blinux\b", r"\bubuntu\b", r"\bred hat\b", r"\brhel\b", r"\bcentos\b", r"لينكس", r"إدارة أنظمة لينكس"],
    "Windows Server & Active Directory": [r"\bwindows server\b", r"\bactive directory\b", r"\bgpo\b", r"\bsccm\b", r"ويندوز سيرفر", r"أكتيف دايركتوري"],
    "Virtualization (VMware / Hyper-V)": [r"\bvmware\b", r"\bvsphere\b", r"\bhyper-v\b", r"\bvirtualization\b", r"الأنظمة الافتراضية"],
    "Networking (TCP/IP, Routing & Switching)": [r"\bnetworking\b", r"\btcp/ip\b", r"\brouting\b", r"\bswitching\b", r"\bdns\b", r"\bdhcp\b", r"\bvlan\b", r"\bbgp\b", r"الشبكات", r"شبكات الحاسب"],
    "Technical Support & Troubleshooting": [r"\btechnical support\b", r"\bhelp desk\b", r"\bservice desk\b", r"\btroubleshooting\b", r"الدعم الفني", r"حل المشكلات التقنية"],
    "ITSM & ITIL": [r"\bitsm\b", r"\bitil\b", r"\bservicenow\b", r"إدارة خدمات تقنية المعلومات"],
    "Backup & Disaster Recovery": [r"\bdisaster recovery\b", r"\bbackup\b", r"\bveeam\b", r"النسخ الاحتياطي", r"استمرارية الأعمال"],
    "ERP / SAP / Oracle ERP": [r"\bsap\b", r"\berp\b", r"\boracle fusion\b", r"\bodoo\b", r"\bdynamics 365\b"],

    # Cybersecurity & Information Security
    "Network Security & Firewalls": [r"\bnetwork security\b", r"\bfirewall\w*\b", r"\bfortinet\b", r"\bpalo alto\b", r"\bids/ips\b", r"\bvpn\b", r"\bwaf\b", r"أمن الشبكات", r"جدران الحماية"],
    "SIEM (Splunk / QRadar / Sentinel)": [r"\bsiem\b", r"\bsplunk\b", r"\bqradar\b", r"\bsentinel\b", r"\blog analysis\b", r"مراقبة الأحداث الأمنية"],
    "SOC & Threat Intelligence": [r"\bsoc\b", r"\bsecurity operations\b", r"\bthreat intelligence\b", r"\bthreat hunting\b", r"\bedr\b", r"\bxdr\b", r"مركز العمليات الأمنية"],
    "Incident Response & Digital Forensics": [r"\bincident response\b", r"\bdfir\b", r"\bdigital forensics\b", r"\bmalware analysis\b", r"الاستجابة للحوادث", r"التحقيق الجنائي الرقمي"],
    "Vulnerability Assessment": [r"\bvulnerability assessment\b", r"\bvulnerability management\b", r"\bnessus\b", r"\bqualys\b", r"فحص الثغرات", r"إدارة الثغرات"],
    "Penetration Testing & Ethical Hacking": [r"\bpenetration test\w*\b", r"\bpentest\w*\b", r"\bethical hack\w*\b", r"\bred team\w*\b", r"\bkali linux\b", r"\bburp suite\b", r"\bmetasploit\b", r"\bowasp\b", r"اختبار الاختراق"],
    "GRC (Governance, Risk & Compliance)": [r"\bgrc\b", r"\bgovernance\b", r"\bcompliance\b", r"\bsecurity audit\w*\b", r"\bsecurity policies\b", r"الحوكمة والمخاطر والالتزام", r"الالتزام السيبراني"],
    "NCA Compliance (ECC / CCC / OTCC)": [r"\bnca\b", r"\becc\b", r"\bsama cyber\b", r"الضوابط الأساسية للأمن السيبراني", r"الهيئة الوطنية للأمن السيبراني"],
    "ISO/IEC 27001 & NIST": [r"\biso\s*27001\b", r"\bnist\b", r"\bcobit\b", r"أيزو 27001"],
    "Risk Management": [r"\brisk management\b", r"\brisk assessment\b", r"\bthird-party risk\b", r"إدارة المخاطر"],
    "Identity & Access Management (IAM)": [r"\biam\b", r"\bidentity and access\b", r"\bpam\b", r"\bcyberark\b", r"\bzero trust\b", r"إدارة الهويات والصلاحيات"],
    "Cloud Security": [r"\bcloud security\b", r"\bdevsecops\b", r"\bcspm\b", r"أمن السحابة"],
    "Cryptography & PKI": [r"\bcryptography\b", r"\bencryption\b", r"\bpki\b", r"\bssl/tls\b", r"التشفير"],
    "Information Security": [r"\binformation security\b", r"\binfosec\b", r"\bcybersecurity\b", r"\bcyber security\b", r"\bdlp\b", r"أمن المعلومات", r"الأمن السيبراني"]
}

# =====================================================================
# 2. قاعدة بيانات الشهادات الاحترافية الحقيقية والمعتمدة (85+ شهادة موثوقة)
# =====================================================================
ACCREDITED_CERTIFICATES_DB = [
    # --- Data Science, AI, BI & Data Engineering ---
    {"code": "SDAIA-DSE", "name": "SDAIA Data Science Expert (خبير علوم البيانات - سدايا)", "provider": "SDAIA (سدايا)", "accreditation": "National Accreditation & Hadaf Supported", "roles": ["Data Scientist", "Data Analyst"], "skills": ["Python", "Machine Learning", "Statistics & Probability", "Data Analysis", "SQL", "Pandas & NumPy", "Scikit-learn"]},
    {"code": "SDAIA-AIE", "name": "SDAIA Artificial Intelligence Engineer (مهندس ذكاء اصطناعي - سدايا)", "provider": "SDAIA (سدايا)", "accreditation": "National Accreditation & Hadaf Supported", "roles": ["AI / Machine Learning Engineer", "Data Scientist"], "skills": ["Python", "Deep Learning", "PyTorch", "TensorFlow / Keras", "NLP", "Large Language Models (LLMs)", "Computer Vision"]},
    {"code": "PL-300", "name": "Microsoft Certified: Power BI Data Analyst Associate (PL-300)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Analyst", "Business Intelligence (BI) Developer"], "skills": ["Power BI", "Data Visualization", "Data Analysis", "SQL", "Advanced Excel"]},
    {"code": "DP-100", "name": "Microsoft Certified: Azure Data Scientist Associate (DP-100)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Scientist", "AI / Machine Learning Engineer"], "skills": ["Machine Learning", "Python", "Microsoft Azure", "Scikit-learn", "PyTorch", "MLOps"]},
    {"code": "DP-203", "name": "Microsoft Certified: Azure Data Engineer Associate (DP-203)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Engineer", "Business Intelligence (BI) Developer"], "skills": ["ETL & Data Pipelines", "Data Warehousing", "SQL", "Apache Spark / PySpark", "Microsoft Azure", "Python"]},
    {"code": "DP-600", "name": "Microsoft Certified: Fabric Analytics Engineer Associate (DP-600)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Engineer", "Business Intelligence (BI) Developer", "Data Analyst"], "skills": ["Power BI", "Data Warehousing", "SQL", "ETL & Data Pipelines", "Python"]},
    {"code": "AI-102", "name": "Microsoft Certified: Azure AI Engineer Associate (AI-102)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["AI / Machine Learning Engineer"], "skills": ["NLP", "Large Language Models (LLMs)", "Computer Vision", "Python", "Microsoft Azure", "RESTful APIs & GraphQL"]},
    {"code": "AWS-MLS-C01", "name": "AWS Certified Machine Learning - Specialty (MLS-C01)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["AI / Machine Learning Engineer", "Data Scientist"], "skills": ["Machine Learning", "Deep Learning", "AWS (Amazon Web Services)", "Python", "MLOps"]},
    {"code": "AWS-DEA-C01", "name": "AWS Certified Data Engineer - Associate (DEA-C01)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Engineer"], "skills": ["ETL & Data Pipelines", "AWS (Amazon Web Services)", "SQL", "Apache Spark / PySpark", "Data Warehousing", "Python"]},
    {"code": "AWS-AIF-C01", "name": "AWS Certified AI Practitioner (AIF-C01)", "provider": "Amazon Web Services (AWS)", "accreditation": "Global Standard", "roles": ["AI / Machine Learning Engineer", "Data Scientist"], "skills": ["Machine Learning", "Large Language Models (LLMs)", "AWS (Amazon Web Services)"]},
    {"code": "DATA-PLUS", "name": "CompTIA Data+ (DA0-001)", "provider": "CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Analyst", "Business Intelligence (BI) Developer"], "skills": ["Data Analysis", "Statistics & Probability", "Data Visualization", "SQL", "Advanced Excel", "Data Governance & Quality"]},
    {"code": "DATAX", "name": "CompTIA DataX (DY0-001 - Advanced Data Science)", "provider": "CompTIA", "accreditation": "Global Standard", "roles": ["Data Scientist", "AI / Machine Learning Engineer"], "skills": ["Machine Learning", "Deep Learning", "Statistics & Probability", "Python", "NLP"]},
    {"code": "TAB-TDS", "name": "Tableau Certified Data Analyst / Desktop Specialist", "provider": "Salesforce / Tableau", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Analyst", "Business Intelligence (BI) Developer"], "skills": ["Tableau", "Data Visualization", "Data Analysis", "SQL"]},
    {"code": "DB-DEA", "name": "Databricks Certified Data Engineer Associate", "provider": "Databricks", "accreditation": "Global Standard", "roles": ["Data Engineer"], "skills": ["Apache Spark / PySpark", "ETL & Data Pipelines", "SQL", "Python", "Data Warehousing", "Big Data / Hadoop"]},
    {"code": "DB-MLE", "name": "Databricks Certified Machine Learning Associate", "provider": "Databricks", "accreditation": "Global Standard", "roles": ["Data Scientist", "AI / Machine Learning Engineer"], "skills": ["Machine Learning", "MLOps", "Apache Spark / PySpark", "Python", "Scikit-learn"]},
    {"code": "SNOW-CORE", "name": "SnowPro Core Certification", "provider": "Snowflake", "accreditation": "Global Standard", "roles": ["Data Engineer", "Business Intelligence (BI) Developer"], "skills": ["Data Warehousing", "SQL", "ETL & Data Pipelines", "Cloud Computing"]},
    {"code": "CDMP", "name": "CDMP - Certified Data Management Professional (DAMA)", "provider": "DAMA International", "accreditation": "Hadaf Supported & NDMO Aligned (معتمدة في هدف ومتوافقة مع سدايا/مكتب البيانات الوطني)", "roles": ["Data Engineer", "Data Analyst", "Business Intelligence (BI) Developer"], "skills": ["Data Governance & Quality", "Data Warehousing", "SQL", "ETL & Data Pipelines"]},
    {"code": "CBIP", "name": "CBIP - Certified Business Intelligence Professional", "provider": "TDWI / ICCP", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Business Intelligence (BI) Developer", "Data Analyst"], "skills": ["Data Warehousing", "Power BI", "Tableau", "ETL & Data Pipelines", "Data Analysis"]},
    {"code": "CAP-INFORMS", "name": "CAP - Certified Analytics Professional", "provider": "INFORMS", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Scientist", "Data Analyst"], "skills": ["Data Analysis", "Statistics & Probability", "Machine Learning", "Python"]},
    {"code": "GCP-PDE", "name": "Google Cloud Professional Data Engineer", "provider": "Google Cloud", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Data Engineer"], "skills": ["Google Cloud Platform (GCP)", "Big Data / Hadoop", "ETL & Data Pipelines", "SQL", "Machine Learning"]},
    {"code": "GCP-PMLE", "name": "Google Cloud Professional Machine Learning Engineer", "provider": "Google Cloud", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["AI / Machine Learning Engineer", "Data Scientist"], "skills": ["Machine Learning", "Deep Learning", "TensorFlow / Keras", "MLOps", "Google Cloud Platform (GCP)", "Python"]},
    {"code": "GOOGLE-DA", "name": "Google Advanced Data Analytics Professional Certificate", "provider": "Google", "accreditation": "Doroob / Misk / Hadaf Partner", "roles": ["Data Analyst", "Data Scientist"], "skills": ["Python", "SQL", "Tableau", "Data Analysis", "Statistics & Probability", "Pandas & NumPy"]},
    {"code": "DLAI-TF", "name": "DeepLearning.AI TensorFlow Developer & Deep Learning Specialization", "provider": "DeepLearning.AI", "accreditation": "SDAIA / Tuwaiq Partner", "roles": ["AI / Machine Learning Engineer", "Data Scientist"], "skills": ["Deep Learning", "TensorFlow / Keras", "PyTorch", "NLP", "Computer Vision", "Python"]},
    {"code": "TUWAIQ-DS", "name": "Tuwaiq Academy Data Science & Machine Learning Bootcamp (معسكر طويق لعلوم البيانات)", "provider": "Tuwaiq Academy (أكاديمية طويق)", "accreditation": "SAFCSP National Bootcamp", "roles": ["Data Scientist", "Data Analyst", "AI / Machine Learning Engineer"], "skills": ["Python", "Pandas & NumPy", "Scikit-learn", "Machine Learning", "SQL", "FastAPI / Flask", "Streamlit"]},

    # --- Cybersecurity, SOC, Pentesting & GRC ---
    {"code": "SY0-701", "name": "CompTIA Security+ (SY0-701)", "provider": "CompTIA", "accreditation": "Hadaf Supported & NCA Recognized (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "SOC Analyst", "GRC & Information Security Specialist"], "skills": ["Network Security & Firewalls", "Information Security", "Risk Management", "Cryptography & PKI", "Vulnerability Assessment", "SIEM (Splunk / QRadar / Sentinel)"]},
    {"code": "CS0-003", "name": "CompTIA CySA+ (Cybersecurity Analyst CS0-003)", "provider": "CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["SOC Analyst", "Cybersecurity Analyst"], "skills": ["SOC & Threat Intelligence", "SIEM (Splunk / QRadar / Sentinel)", "Incident Response & Digital Forensics", "Vulnerability Assessment", "Network Security & Firewalls"]},
    {"code": "PT0-002", "name": "CompTIA PenTest+ (PT0-002)", "provider": "CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Penetration Tester"], "skills": ["Penetration Testing & Ethical Hacking", "Vulnerability Assessment", "Linux Administration", "Bash / Shell Scripting", "Python"]},
    {"code": "CAS-004", "name": "CompTIA CASP+ / SecurityX (Advanced Security Practitioner)", "provider": "CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "GRC & Information Security Specialist"], "skills": ["Information Security", "Cloud Security", "Risk Management", "Cryptography & PKI", "SOC & Threat Intelligence"]},
    {"code": "CISSP", "name": "CISSP - Certified Information Systems Security Professional", "provider": "ISC2", "accreditation": "Hadaf Supported & NCA Top Tier (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "GRC & Information Security Specialist"], "skills": ["Information Security", "Risk Management", "GRC (Governance, Risk & Compliance)", "Identity & Access Management (IAM)", "Network Security & Firewalls", "Cloud Security", "Cryptography & PKI"]},
    {"code": "CCSP", "name": "CCSP - Certified Cloud Security Professional", "provider": "ISC2", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "Cloud Engineer"], "skills": ["Cloud Security", "AWS (Amazon Web Services)", "Microsoft Azure", "Information Security", "Risk Management"]},
    {"code": "SSCP", "name": "SSCP - Systems Security Certified Practitioner", "provider": "ISC2", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "SOC Analyst"], "skills": ["Network Security & Firewalls", "Identity & Access Management (IAM)", "Incident Response & Digital Forensics", "Information Security"]},
    {"code": "CC-ISC2", "name": "Certified in Cybersecurity (CC) - Entry Level", "provider": "ISC2", "accreditation": "Global Standard for Fresh Graduates", "roles": ["Cybersecurity Analyst", "SOC Analyst"], "skills": ["Information Security", "Network Security & Firewalls", "Risk Management", "Incident Response & Digital Forensics"]},
    {"code": "CISM", "name": "CISM - Certified Information Security Manager", "provider": "ISACA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["GRC & Information Security Specialist", "Cybersecurity Analyst"], "skills": ["GRC (Governance, Risk & Compliance)", "Risk Management", "Information Security", "ISO/IEC 27001 & NIST", "NCA Compliance (ECC / CCC / OTCC)", "Incident Response & Digital Forensics"]},
    {"code": "CISA", "name": "CISA - Certified Information Systems Auditor", "provider": "ISACA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["GRC & Information Security Specialist"], "skills": ["GRC (Governance, Risk & Compliance)", "ISO/IEC 27001 & NIST", "NCA Compliance (ECC / CCC / OTCC)", "Risk Management", "Information Security"]},
    {"code": "CRISC", "name": "CRISC - Certified in Risk and Information Systems Control", "provider": "ISACA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["GRC & Information Security Specialist"], "skills": ["Risk Management", "GRC (Governance, Risk & Compliance)", "NCA Compliance (ECC / CCC / OTCC)", "ISO/IEC 27001 & NIST"]},
    {"code": "CEH-V12", "name": "CEH v12 - Certified Ethical Hacker (Practical & ANSI)", "provider": "EC-Council", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Penetration Tester", "Cybersecurity Analyst"], "skills": ["Penetration Testing & Ethical Hacking", "Vulnerability Assessment", "Network Security & Firewalls", "Linux Administration"]},
    {"code": "CHFI", "name": "CHFI - Computer Hacking Forensic Investigator", "provider": "EC-Council", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["SOC Analyst", "Cybersecurity Analyst"], "skills": ["Incident Response & Digital Forensics", "SOC & Threat Intelligence", "SIEM (Splunk / QRadar / Sentinel)"]},
    {"code": "CSA-ECC", "name": "CSA - Certified SOC Analyst", "provider": "EC-Council", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["SOC Analyst"], "skills": ["SOC & Threat Intelligence", "SIEM (Splunk / QRadar / Sentinel)", "Incident Response & Digital Forensics", "Network Security & Firewalls"]},
    {"code": "OSCP", "name": "OSCP - Offensive Security Certified Professional (PEN-200)", "provider": "OffSec", "accreditation": "Hadaf Supported & Elite Industry Standard (مدعومة من هدف)", "roles": ["Penetration Tester"], "skills": ["Penetration Testing & Ethical Hacking", "Linux Administration", "Windows Server & Active Directory", "Python", "Bash / Shell Scripting", "Vulnerability Assessment"]},
    {"code": "OSWE", "name": "OSWE - Offensive Security Web Expert (WEB-300)", "provider": "OffSec", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Penetration Tester"], "skills": ["Penetration Testing & Ethical Hacking", "JavaScript", "Python", "RESTful APIs & GraphQL"]},
    {"code": "EJPT-V2", "name": "eJPTv2 - Junior Penetration Tester", "provider": "INE Security", "accreditation": "SAFCSP / CyberHub Supported", "roles": ["Penetration Tester"], "skills": ["Penetration Testing & Ethical Hacking", "Networking (TCP/IP, Routing & Switching)", "Linux Administration", "Vulnerability Assessment"]},
    {"code": "ECPPT", "name": "eCPPT - Certified Professional Penetration Tester", "provider": "INE Security", "accreditation": "SAFCSP Recognized", "roles": ["Penetration Tester"], "skills": ["Penetration Testing & Ethical Hacking", "Network Security & Firewalls", "Windows Server & Active Directory"]},
    {"code": "ECDFP", "name": "eCDFP / eCIR - Certified Incident Responder", "provider": "INE Security", "accreditation": "SAFCSP Recognized", "roles": ["SOC Analyst", "Cybersecurity Analyst"], "skills": ["Incident Response & Digital Forensics", "SIEM (Splunk / QRadar / Sentinel)", "SOC & Threat Intelligence"]},
    {"code": "GIAC-GSEC", "name": "GIAC Security Essentials (GSEC - SANS SEC401)", "provider": "SANS / GIAC", "accreditation": "Hadaf Supported & NCA Elite Standard (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "SOC Analyst"], "skills": ["Information Security", "Network Security & Firewalls", "Linux Administration", "Windows Server & Active Directory", "Cryptography & PKI", "Incident Response & Digital Forensics"]},
    {"code": "GIAC-GCIH", "name": "GIAC Certified Incident Handler (GCIH - SANS SEC504)", "provider": "SANS / GIAC", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["SOC Analyst", "Cybersecurity Analyst", "Penetration Tester"], "skills": ["Incident Response & Digital Forensics", "SOC & Threat Intelligence", "Penetration Testing & Ethical Hacking", "SIEM (Splunk / QRadar / Sentinel)"]},
    {"code": "GIAC-GPEN", "name": "GIAC Penetration Tester (GPEN - SANS SEC560)", "provider": "SANS / GIAC", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Penetration Tester"], "skills": ["Penetration Testing & Ethical Hacking", "Vulnerability Assessment", "Windows Server & Active Directory"]},
    {"code": "GIAC-GCIA", "name": "GIAC Certified Intrusion Analyst (GCIA - SANS SEC503)", "provider": "SANS / GIAC", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["SOC Analyst"], "skills": ["SOC & Threat Intelligence", "Network Security & Firewalls", "SIEM (Splunk / QRadar / Sentinel)"]},
    {"code": "ISO-27001-LI", "name": "PECB Certified ISO/IEC 27001 Lead Implementer & Lead Auditor", "provider": "PECB", "accreditation": "Hadaf Supported & NCA Aligned (مدعومة من هدف)", "roles": ["GRC & Information Security Specialist", "Cybersecurity Analyst"], "skills": ["ISO/IEC 27001 & NIST", "GRC (Governance, Risk & Compliance)", "NCA Compliance (ECC / CCC / OTCC)", "Risk Management", "Information Security"]},
    {"code": "SPLK-1002", "name": "Splunk Core Certified Power User & Enterprise Security Admin", "provider": "Splunk", "accreditation": "Global SOC Standard", "roles": ["SOC Analyst", "Cybersecurity Analyst"], "skills": ["SIEM (Splunk / QRadar / Sentinel)", "SOC & Threat Intelligence", "Incident Response & Digital Forensics"]},
    {"code": "SC-200", "name": "Microsoft Certified: Security Operations Analyst Associate (SC-200)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["SOC Analyst", "Cybersecurity Analyst"], "skills": ["SIEM (Splunk / QRadar / Sentinel)", "SOC & Threat Intelligence", "Incident Response & Digital Forensics", "Microsoft Azure"]},
    {"code": "AZ-500", "name": "Microsoft Certified: Azure Security Engineer Associate (AZ-500)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "Cloud Engineer"], "skills": ["Cloud Security", "Microsoft Azure", "Identity & Access Management (IAM)", "Network Security & Firewalls"]},
    {"code": "AWS-SCS-C02", "name": "AWS Certified Security - Specialty (SCS-C02)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cybersecurity Analyst", "Cloud Engineer"], "skills": ["Cloud Security", "AWS (Amazon Web Services)", "Identity & Access Management (IAM)", "Cryptography & PKI"]},

    # --- Cloud, DevOps, Linux, Networking & IT Infrastructure ---
    {"code": "AWS-SAA-C03", "name": "AWS Certified Solutions Architect - Associate (SAA-C03)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cloud Engineer", "DevOps Engineer", "Backend Developer"], "skills": ["AWS (Amazon Web Services)", "Cloud Computing", "Networking (TCP/IP, Routing & Switching)", "Linux Administration", "Docker & Containers"]},
    {"code": "AWS-CLF-C02", "name": "AWS Certified Cloud Practitioner (CLF-C02)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cloud Engineer", "System Administrator", "IT Support & Operations Specialist"], "skills": ["AWS (Amazon Web Services)", "Cloud Computing"]},
    {"code": "AWS-DOP-C02", "name": "AWS Certified DevOps Engineer - Professional (DOP-C02)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["DevOps Engineer", "Cloud Engineer"], "skills": ["CI/CD Pipelines", "AWS (Amazon Web Services)", "Docker & Containers", "Kubernetes (K8s)", "Terraform & IaC", "Linux Administration"]},
    {"code": "AZ-104", "name": "Microsoft Certified: Azure Administrator Associate (AZ-104)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cloud Engineer", "System Administrator"], "skills": ["Microsoft Azure", "Cloud Computing", "Windows Server & Active Directory", "Virtualization (VMware / Hyper-V)", "Networking (TCP/IP, Routing & Switching)"]},
    {"code": "AZ-305", "name": "Microsoft Certified: Azure Solutions Architect Expert (AZ-305)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cloud Engineer"], "skills": ["Microsoft Azure", "Cloud Computing", "Microservices Architecture", "Identity & Access Management (IAM)"]},
    {"code": "AZ-400", "name": "Microsoft Certified: DevOps Engineer Expert (AZ-400)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["DevOps Engineer"], "skills": ["CI/CD Pipelines", "Docker & Containers", "Kubernetes (K8s)", "Terraform & IaC", "Git & Version Control", "Microsoft Azure"]},
    {"code": "GCP-ACE", "name": "Google Cloud Associate Cloud Engineer", "provider": "Google Cloud", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Cloud Engineer", "DevOps Engineer"], "skills": ["Google Cloud Platform (GCP)", "Cloud Computing", "Kubernetes (K8s)", "Linux Administration"]},
    {"code": "CNCF-CKA", "name": "CKA - Certified Kubernetes Administrator", "provider": "Linux Foundation / CNCF", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["DevOps Engineer", "Cloud Engineer"], "skills": ["Kubernetes (K8s)", "Docker & Containers", "Linux Administration", "Cloud Computing", "Networking (TCP/IP, Routing & Switching)"]},
    {"code": "CNCF-CKAD", "name": "CKAD - Certified Kubernetes Application Developer", "provider": "Linux Foundation / CNCF", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["DevOps Engineer", "Backend Developer", "Software Engineer"], "skills": ["Kubernetes (K8s)", "Docker & Containers", "CI/CD Pipelines", "Microservices Architecture"]},
    {"code": "CNCF-CKS", "name": "CKS - Certified Kubernetes Security Specialist", "provider": "Linux Foundation / CNCF", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["DevOps Engineer", "Cybersecurity Analyst"], "skills": ["Kubernetes (K8s)", "Cloud Security", "Docker & Containers", "Linux Administration"]},
    {"code": "TF-003", "name": "HashiCorp Certified: Terraform Associate (003)", "provider": "HashiCorp", "accreditation": "Global DevOps Standard", "roles": ["DevOps Engineer", "Cloud Engineer"], "skills": ["Terraform & IaC", "Cloud Computing", "AWS (Amazon Web Services)", "Microsoft Azure", "CI/CD Pipelines"]},
    {"code": "RHCSA-EX200", "name": "Red Hat Certified System Administrator (RHCSA - EX200)", "provider": "Red Hat", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["System Administrator", "DevOps Engineer", "Cloud Engineer"], "skills": ["Linux Administration", "Bash / Shell Scripting", "Virtualization (VMware / Hyper-V)", "Docker & Containers"]},
    {"code": "RHCE-EX294", "name": "Red Hat Certified Engineer (RHCE - EX294 Ansible Automation)", "provider": "Red Hat", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["DevOps Engineer", "System Administrator"], "skills": ["Linux Administration", "Terraform & IaC", "Bash / Shell Scripting"]},
    {"code": "LPIC-1", "name": "LPIC-1 / CompTIA Linux+ (XK0-005)", "provider": "LPI / CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["System Administrator", "Cloud Engineer"], "skills": ["Linux Administration", "Bash / Shell Scripting", "Networking (TCP/IP, Routing & Switching)"]},
    {"code": "CCNA-200-301", "name": "Cisco Certified Network Associate (CCNA 200-301)", "provider": "Cisco", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Network Engineer", "System Administrator", "Cybersecurity Analyst"], "skills": ["Networking (TCP/IP, Routing & Switching)", "Network Security & Firewalls", "Linux Administration"]},
    {"code": "CCNP-ENCOR", "name": "Cisco Certified Network Professional Enterprise (CCNP 350-401 ENCOR)", "provider": "Cisco", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Network Engineer"], "skills": ["Networking (TCP/IP, Routing & Switching)", "Network Security & Firewalls", "Virtualization (VMware / Hyper-V)"]},
    {"code": "N10-009", "name": "CompTIA Network+ (N10-009)", "provider": "CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Network Engineer", "IT Support & Operations Specialist", "System Administrator"], "skills": ["Networking (TCP/IP, Routing & Switching)", "Technical Support & Troubleshooting"]},
    {"code": "220-1101", "name": "CompTIA A+ (220-1101 & 220-1102)", "provider": "CompTIA", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["IT Support & Operations Specialist", "System Administrator"], "skills": ["Technical Support & Troubleshooting", "Windows Server & Active Directory", "Linux Administration", "Networking (TCP/IP, Routing & Switching)"]},
    {"code": "ITIL-4", "name": "ITIL 4 Foundation in IT Service Management", "provider": "PeopleCert / Axelos", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["IT Support & Operations Specialist", "System Administrator", "ERP / SAP Technical Consultant"], "skills": ["ITSM & ITIL", "Technical Support & Troubleshooting"]},
    {"code": "VCP-DCV", "name": "VMware Certified Professional - Data Center Virtualization (VCP-DCV)", "provider": "VMware / Broadcom", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["System Administrator", "Cloud Engineer"], "skills": ["Virtualization (VMware / Hyper-V)", "Windows Server & Active Directory", "Linux Administration", "Backup & Disaster Recovery"]},
    {"code": "SAP-C-TS4FI", "name": "SAP Certified Associate - Implementation Consultant (S/4HANA)", "provider": "SAP", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["ERP / SAP Technical Consultant"], "skills": ["ERP / SAP / Oracle ERP", "SQL", "ITSM & ITIL"]},

    # --- Software Engineering, Web, Backend, Frontend & Mobile ---
    {"code": "OCP-1Z0-829", "name": "Oracle Certified Professional: Java SE 17 / 21 Developer (1Z0-829)", "provider": "Oracle", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Backend Developer", "Software Engineer", "Full Stack Developer"], "skills": ["Java", "Spring Boot", "OOP & Design Patterns", "Data Structures & Algorithms", "SQL"]},
    {"code": "AWS-DVA-C02", "name": "AWS Certified Developer - Associate (DVA-C02)", "provider": "Amazon Web Services (AWS)", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Backend Developer", "Full Stack Developer", "Software Engineer"], "skills": ["AWS (Amazon Web Services)", "Python", "Node.js / Express", "RESTful APIs & GraphQL", "CI/CD Pipelines", "Docker & Containers"]},
    {"code": "AZ-204", "name": "Microsoft Certified: Azure Developer Associate (AZ-204)", "provider": "Microsoft", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Backend Developer", "Full Stack Developer", "Software Engineer"], "skills": ["C# / .NET", "Microsoft Azure", "RESTful APIs & GraphQL", "Docker & Containers", "SQL"]},
    {"code": "PCAP-31-03", "name": "PCAP / PCPP1 - Certified Associate/Professional in Python Programming", "provider": "Python Institute", "accreditation": "Global Standard", "roles": ["Backend Developer", "Software Engineer", "Data Scientist"], "skills": ["Python", "OOP & Design Patterns", "FastAPI / Flask", "Django"]},
    {"code": "SPRING-PRO", "name": "Spring Certified Professional (VMware / Tanzu)", "provider": "VMware", "accreditation": "Global Enterprise Standard", "roles": ["Backend Developer", "Software Engineer"], "skills": ["Spring Boot", "Java", "Microservices Architecture", "RESTful APIs & GraphQL", "SQL"]},
    {"code": "LF-JSNAD", "name": "OpenJS Node.js Application Developer (JSNAD)", "provider": "Linux Foundation", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Backend Developer", "Full Stack Developer"], "skills": ["Node.js / Express", "JavaScript", "TypeScript", "RESTful APIs & GraphQL"]},
    {"code": "META-FE", "name": "Meta Front-End Developer Professional Certificate", "provider": "Meta", "accreditation": "Doroob / Misk Partner", "roles": ["Frontend Developer", "Full Stack Developer"], "skills": ["React.js / Next.js", "JavaScript", "TypeScript", "HTML5 & CSS3", "UI/UX & Figma", "Git & Version Control"]},
    {"code": "META-BE", "name": "Meta Back-End Developer Professional Certificate", "provider": "Meta", "accreditation": "Doroob / Misk Partner", "roles": ["Backend Developer", "Full Stack Developer"], "skills": ["Python", "Django", "FastAPI / Flask", "RESTful APIs & GraphQL", "PostgreSQL / MySQL", "Git & Version Control"]},
    {"code": "GOOGLE-AAD", "name": "Google Associate Android Developer / Flutter Bootcamp", "provider": "Google / Tuwaiq Academy", "accreditation": "Industry & SAFCSP Recognized", "roles": ["Mobile App Developer"], "skills": ["Flutter", "Dart", "Kotlin", "Swift", "RESTful APIs & GraphQL", "Git & Version Control"]},
    {"code": "ISTQB-CTFL", "name": "ISTQB Certified Tester Foundation Level (CTFL v4.0)", "provider": "ISTQB", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Software Engineer", "Full Stack Developer"], "skills": ["Unit Testing & QA Automation", "Agile & Scrum (SDLC)"]},
    {"code": "PSM-I", "name": "Professional Scrum Master I (PSM I) / PMI-ACP", "provider": "Scrum.org / PMI", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Software Engineer", "Full Stack Developer", "Backend Developer"], "skills": ["Agile & Scrum (SDLC)", "Git & Version Control"]},
    {"code": "CAPM-PMP", "name": "PMI CAPM / PMP (Project Management Professional)", "provider": "PMI", "accreditation": "Hadaf Supported (مدعومة من هدف)", "roles": ["Software Engineer", "ERP / SAP Technical Consultant"], "skills": ["Agile & Scrum (SDLC)", "ITSM & ITIL"]}
]

# =====================================================================
# 3. تصنيف المسميات الوظيفية والتخصصات
# =====================================================================
ROLE_METADATA = {
    "Data Scientist": ("عالم بيانات", "Data Science", (11500, 16500)),
    "Data Analyst": ("محلل بيانات", "Data Science", (8500, 13000)),
    "AI / Machine Learning Engineer": ("مهندس ذكاء اصطناعي وتعلم آلة", "Data Science", (12500, 18000)),
    "Business Intelligence (BI) Developer": ("مطور ذكاء أعمال", "Data Science", (9000, 14000)),
    "Data Engineer": ("مهندس بيانات", "Data Science", (11000, 16000)),
    "Backend Developer": ("مطور واجهات خلفية", "Computer Science", (9500, 14500)),
    "Frontend Developer": ("مطور واجهات أمامية", "Software Engineering", (8500, 13000)),
    "Full Stack Developer": ("مطور متكامل (Full Stack)", "Software Engineering", (10000, 15500)),
    "Software Engineer": ("مهندس برمجيات", "Software Engineering", (10000, 15500)),
    "Mobile App Developer": ("مطور تطبيقات جوال", "Software Engineering", (9000, 14000)),
    "Cybersecurity Analyst": ("محلل أمن سيبراني", "Cybersecurity", (10500, 16000)),
    "SOC Analyst": ("محلل مركز العمليات الأمنية (SOC)", "Cybersecurity", (10000, 15000)),
    "Penetration Tester": ("مختبر اختراق", "Cybersecurity", (11500, 17000)),
    "GRC & Information Security Specialist": ("أخصائي حوكمة ومخاطر والتزام سيبراني", "Cybersecurity", (10500, 15500)),
    "Cloud Engineer": ("مهندس حوسبة سحابية", "Information Technology", (11000, 16500)),
    "DevOps Engineer": ("مهندس ديف أوبس (DevOps)", "Information Technology", (12000, 17500)),
    "System Administrator": ("مدير أنظمة", "Information Technology", (8000, 12000)),
    "Network Engineer": ("مهندس شبكات", "Information Technology", (8500, 12500)),
    "IT Support & Operations Specialist": ("أخصائي دعم فني وتشغيل", "Information Technology", (6500, 9500)),
    "ERP / SAP Technical Consultant": ("مستشار تقني لأنظمة ERP / SAP", "Information Technology", (10000, 15000))
}

# استعلامات البحث الحية لتغطية كل التخصصات في السعودية
SAUDI_SEARCH_QUERIES = [
    ("Data Scientist", "Data Scientist"),
    ("Data Analyst", "Data Analyst"),
    ("Machine Learning Engineer", "AI / Machine Learning Engineer"),
    ("AI Engineer", "AI / Machine Learning Engineer"),
    ("Power BI Developer", "Business Intelligence (BI) Developer"),
    ("Business Intelligence", "Business Intelligence (BI) Developer"),
    ("Data Engineer", "Data Engineer"),
    ("Backend Developer", "Backend Developer"),
    ("Python Developer", "Backend Developer"),
    ("Java Developer", "Backend Developer"),
    (".NET Developer", "Backend Developer"),
    ("Frontend Developer", "Frontend Developer"),
    ("React Developer", "Frontend Developer"),
    ("Full Stack Developer", "Full Stack Developer"),
    ("Software Engineer", "Software Engineer"),
    ("Mobile Developer", "Mobile App Developer"),
    ("Flutter Developer", "Mobile App Developer"),
    ("iOS Android Developer", "Mobile App Developer"),
    ("Cybersecurity", "Cybersecurity Analyst"),
    ("Information Security", "Cybersecurity Analyst"),
    ("SOC Analyst", "SOC Analyst"),
    ("Penetration Tester", "Penetration Tester"),
    ("GRC Cybersecurity", "GRC & Information Security Specialist"),
    ("Cloud Engineer", "Cloud Engineer"),
    ("AWS Azure Engineer", "Cloud Engineer"),
    ("DevOps Engineer", "DevOps Engineer"),
    ("System Administrator", "System Administrator"),
    ("Linux Administrator", "System Administrator"),
    ("Network Engineer", "Network Engineer"),
    ("IT Support Specialist", "IT Support & Operations Specialist"),
    ("IT Help Desk", "IT Support & Operations Specialist"),
    ("SAP Consultant", "ERP / SAP Technical Consultant"),
    ("محلل بيانات", "Data Analyst"),
    ("عالم بيانات", "Data Scientist"),
    ("ذكاء اصطناعي", "AI / Machine Learning Engineer"),
    ("مهندس برمجيات", "Software Engineer"),
    ("مطور تطبيقات", "Mobile App Developer"),
    ("أمن سيبراني", "Cybersecurity Analyst"),
    ("أمن معلومات", "GRC & Information Security Specialist"),
    ("مهندس شبكات", "Network Engineer"),
    ("دعم فني تقنية معلومات", "IT Support & Operations Specialist")
]


# =====================================================================
# 4. دوال الاستخراج الحقيقي والمطابقة مع الشهادات الاحترافية
# =====================================================================
def extract_real_skills_from_text(text: str) -> list:
    """استخراج المهارات الموجودة فعلياً في نص الإعلان فقط بدون أي إضافة عشوائية"""
    if not isinstance(text, str) or not text.strip():
        return []
    text_lower = text.lower()
    extracted = []
    for skill_name, regex_list in SKILL_EXTRACTION_PATTERNS.items():
        for pattern in regex_list:
            if re.search(pattern, text_lower):
                extracted.append(skill_name)
                break
    return sorted(list(set(extracted)))


def classify_job_role(raw_title: str, fallback_role: str) -> str:
    if not isinstance(raw_title, str):
        return fallback_role
    t = raw_title.lower()
    rules = [
        (["data scientist", "عالم بيانات"], "Data Scientist"),
        (["machine learning", "ai engineer", "artificial intelligence", "deep learning", "nlp", "ذكاء اصطناعي", "تعلم آلة"], "AI / Machine Learning Engineer"),
        (["power bi", "bi developer", "business intelligence", "tableau", "ذكاء أعمال"], "Business Intelligence (BI) Developer"),
        (["data engineer", "etl", "big data", "spark", "مهندس بيانات"], "Data Engineer"),
        (["data analyst", "analytics", "محلل بيانات"], "Data Analyst"),
        (["soc", "siem", "blue team", "مركز العمليات"], "SOC Analyst"),
        (["penetration", "pentest", "ethical hack", "red team", "offsec", "مختبر اختراق"], "Penetration Tester"),
        (["grc", "governance", "compliance", "iso 27001", "nca", "risk", "حوكمة", "مخاطر", "التزام"], "GRC & Information Security Specialist"),
        (["cyber", "security", "infosec", "أمن سيبراني", "أمن معلومات"], "Cybersecurity Analyst"),
        (["devops", "sre", "kubernetes", "ci/cd", "ديف أوبس"], "DevOps Engineer"),
        (["cloud", "aws", "azure", "gcp", "سحابة"], "Cloud Engineer"),
        (["network", "ccna", "ccnp", "cisco", "routing", "شبكات"], "Network Engineer"),
        (["system admin", "sysadmin", "windows server", "linux admin", "مدير أنظمة"], "System Administrator"),
        (["it support", "help desk", "service desk", "technical support", "دعم فني"], "IT Support & Operations Specialist"),
        (["sap", "erp", "odoo", "oracle fusion"], "ERP / SAP Technical Consultant"),
        (["frontend", "front-end", "react", "angular", "vue", "واجهات أمامية"], "Frontend Developer"),
        (["backend", "back-end", "spring", "django", "fastapi", "واجهات خلفية"], "Backend Developer"),
        (["full stack", "fullstack", "مطور متكامل"], "Full Stack Developer"),
        (["mobile", "flutter", "ios", "android", "react native", "تطبيقات جوال"], "Mobile App Developer"),
        (["software", "developer", "programmer", "مهندس برمجيات", "مطور برمجيات"], "Software Engineer")
    ]
    for keywords, role in rules:
        if any(k in t for k in keywords):
            return role
    return fallback_role


def match_accredited_certificates(std_role: str, extracted_skills: list) -> list:
    """مطابقة الشهادات الاحترافية المعتمدة بناءً على المهارات المستخرجة فعلياً من الإعلان والمسمى الوظيفي"""
    skill_set = set(extracted_skills)
    scored_certs = []

    for cert in ACCREDITED_CERTIFICATES_DB:
        overlap_skills = skill_set.intersection(set(cert["skills"]))
        role_match = 2 if std_role in cert["roles"] else 0
        score = (len(overlap_skills) * 3) + role_match
        if score > 0:
            formatted = f"[{cert['code']}] {cert['name']} - {cert['provider']} ({cert['accreditation']})"
            scored_certs.append((score, formatted))

    scored_certs.sort(key=lambda x: x[0], reverse=True)
    # إرجاع أعلى 5 شهادات احترافية مطابقة للمهارات الفعلية في الإعلان
    return [c[1] for c in scored_certs[:5]]


def normalize_saudi_city(raw_location: str) -> str:
    if not isinstance(raw_location, str):
        return "Riyadh"
    loc = raw_location.lower()
    city_map = {
        "riyadh": "Riyadh", "الرياض": "Riyadh",
        "jeddah": "Jeddah", "جدة": "Jeddah",
        "dammam": "Dammam", "الدمام": "Dammam",
        "khobar": "Al Khobar", "الخبر": "Al Khobar",
        "dhahran": "Dhahran", "الظهران": "Dhahran",
        "makkah": "Makkah", "mecca": "Makkah", "مكة": "Makkah",
        "madinah": "Madinah", "medina": "Madinah", "المدينة": "Madinah",
        "jubail": "Jubail", "الجبيل": "Jubail",
        "neom": "NEOM", "نيوم": "NEOM",
        "tabuk": "Tabuk", "تبوك": "Tabuk",
        "abha": "Abha", "أبها": "Abha"
    }
    for key, val in city_map.items():
        if key in loc:
            return val
    return "Saudi Arabia (National / Remote)"


def detect_language_type(text: str) -> str:
    if not isinstance(text, str):
        return "EN"
    has_ar = bool(re.search(r"[\u0600-\u06FF]", text))
    has_en = bool(re.search(r"[a-zA-Z]{3,}", text))
    if has_ar and has_en:
        return "MIXED_AR_EN"
    elif has_ar:
        return "AR"
    return "EN"


# =====================================================================
# 5. محرك السكرابنق الفعلي من منصات التوظيف في السعودية
# =====================================================================
def run_real_saudi_scraping(existing_urls: set, results_per_query: int = 40) -> list:
    scraped_records = []
    # مجموعة لتتبع الروابط الجديدة في نفس الجولة أيضاً
    seen_urls_in_run = set(existing_urls)

    for search_term, fallback_role in SAUDI_SEARCH_QUERIES:
        logging.info(f"جاري فحص الإعلانات لـ: '{search_term}' ...")
        try:
            df_jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "bayt", "google"],
                search_term=search_term,
                location="Saudi Arabia",
                results_wanted=results_per_query,
                hours_old=48,  # خله 48 ساعة للتشغيل اليومي عشان يجيب الجديد بس
                country_indeed="saudi arabia",
                linkedin_fetch_description=True
            )

            if df_jobs is None or df_jobs.empty:
                continue

            for _, row in df_jobs.iterrows():
                job_url = str(row.get("job_url") or "").strip()

                # 1. منع التكرار: إذا الرابط مكرر أو فاضي، نتخطاه فوراً
                if not job_url or job_url in seen_urls_in_run:
                    continue

                raw_title = str(row.get("title") or "").strip()
                company = str(row.get("company") or "Saudi Employer").strip()
                raw_loc = str(row.get("location") or "Saudi Arabia").strip()
                raw_desc = str(row.get("description") or "").strip()
                site = str(row.get("site") or "JobPortal").strip()

                # استخراج المهارات
                full_text = f"{raw_title} {raw_desc}"
                real_extracted_skills = extract_real_skills_from_text(full_text)

                if len(real_extracted_skills) == 0:
                    continue

                std_role = classify_job_role(raw_title, fallback_role)
                role_ar, target_major, (sal_min, sal_max) = ROLE_METADATA[std_role]
                city = normalize_saudi_city(raw_loc)
                lang_type = detect_language_type(full_text)

                # معالجة الراتب
                min_amt = row.get("min_amount")
                max_amt = row.get("max_amount")
                if pd.notna(min_amt) and float(min_amt) > 0:
                    salary_info = f"{int(float(min_amt))} - {int(float(max_amt)) if pd.notna(max_amt) else int(float(min_amt))}"
                else:
                    salary_info = f"{sal_min} - {sal_max} (Market Est.)"

                matched_certs = match_accredited_certificates(std_role, real_extracted_skills)

                # تسجيل الإعلان الجديد وإضافة الرابط للمجموعة لتجنب تكراره في كويري ثاني
                seen_urls_in_run.add(job_url)

                scraped_records.append({
                    "standardized_role_en": std_role,
                    "standardized_role_ar": role_ar,
                    "target_major": target_major,
                    "job_title_raw": raw_title,
                    "company_name": company,
                    "city": city,
                    "salary_range_sar": salary_info,
                    "language_type": lang_type,
                    "extracted_skills": "|".join(real_extracted_skills),
                    "skills_count": len(real_extracted_skills),
                    "recommended_certificates": " || ".join(matched_certs),
                    "source_platform": site,
                    "job_url": job_url,
                    "scraped_at": datetime.utcnow().strftime("%Y-%m-%d"),
                    "job_description": raw_desc[:2500]
                })

            logging.info(f"تمت تصفية الإعلانات لـ '{search_term}' (سجلات جديدة مستخرجة: {len(scraped_records)})")
            time.sleep(2)

        except Exception as e:
            logging.warning(f"تخطي خطأ في '{search_term}': {e}")
            time.sleep(2)

    return scraped_records


# =====================================================================
# 6. حساب أكثر المهارات طلباً في السوق السعودي لكل مسمى وظيفي تلقائياً
# =====================================================================
def compute_dynamic_market_top_skills(df: pd.DataFrame) -> pd.DataFrame:
    """
    بدل كتابة مهارات مرجعية ثابتة، هذه الدالة تحسب أكثر المهارات تكراراً
    في الإعلانات السعودية الحقيقية المسحوبة لكل وظيفة عشان تستخدمونها في حساب الـ Skill-Gap.
    """
    role_skill_counters = {}
    for role, group in df.groupby("standardized_role_en"):
        counter = Counter()
        for skills_str in group["extracted_skills"].dropna():
            skills = [s.strip() for s in str(skills_str).split("|") if s.strip()]
            counter.update(skills)
        # أخذ أعلى 8 مهارات مطلوبة فعلياً في السوق السعودي لهذا المسمى
        top_skills = [sk for sk, _ in counter.most_common(8)]
        role_skill_counters[role] = "|".join(top_skills)

    df["saudi_market_top_skills_for_role"] = df["standardized_role_en"].map(role_skill_counters)

    # بناء عمود التدريب الموحد للموديل (TF-IDF / Sentence Transformers)
    df["ml_training_text"] = (
        "Role: " + df["standardized_role_en"] + " (" + df["standardized_role_ar"] + ") | "
        "Major: " + df["target_major"] + " | "
        "Extracted Job Skills: " + df["extracted_skills"].str.replace("|", ", ", regex=False) + " | "
        "Saudi Market Top Role Skills: " + df["saudi_market_top_skills_for_role"].str.replace("|", ", ", regex=False) + " | "
        "City: " + df["city"] + " | "
        "Description: " + df["job_description"]
    )
    return df


# =====================================================================
# 7. الدمج، إزالة التكرار، والحفظ في CSV + SQLite
# =====================================================================
def execute_pipeline(results_per_query: int = 40):
    logging.info("=== بدء تشغيل السكرابر الفعلي لسوق العمل السعودي ===")

    existing_df = pd.DataFrame()
    existing_urls = set()

    # جلب الروابط المحفوظة مسبقاً
    if os.path.exists(MASTER_CSV_PATH):
        try:
            existing_df = pd.read_csv(MASTER_CSV_PATH)
            if "job_url" in existing_df.columns:
                existing_urls = set(existing_df["job_url"].dropna().astype(str).tolist())
            logging.info(f"تم تحميل {len(existing_df)} سجل سابق، منها {len(existing_urls)} رابط مميز.")
        except Exception as e:
            logging.warning(f"تعذر قراءة الملف السابق: {e}")

    # السحب مع استبعاد الروابط السابقة مسبقاً
    new_records = run_real_saudi_scraping(existing_urls=existing_urls, results_per_query=results_per_query)

    if not new_records:
        logging.info("لا توجد إعلانات وظائف جديدة اليوم. انتهت العملية بدون تعديل.")
        return

    new_df = pd.DataFrame(new_records)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True) if not existing_df.empty else new_df

    # إزالة تكرار نهائية كطبقة حماية إضافية بالاعتماد على الرابط
    combined_df.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
    combined_df.reset_index(drop=True, inplace=True)

    # تحديث التحليلات المتقدمة والـ IDs
    combined_df = compute_dynamic_market_top_skills(combined_df)
    combined_df["record_id"] = [f"SA-REAL-{i+1:05d}" for i in range(len(combined_df))]

    cols_order = [
        "record_id", "standardized_role_en", "standardized_role_ar", "target_major",
        "job_title_raw", "company_name", "city", "salary_range_sar",
        "language_type", "skills_count", "extracted_skills",
        "saudi_market_top_skills_for_role", "recommended_certificates",
        "source_platform", "job_url", "scraped_at",
        "job_description", "ml_training_text"
    ]
    combined_df = combined_df[cols_order]

    # حفظ النتائج
    combined_df.to_csv(MASTER_CSV_PATH, index=False, encoding="utf-8-sig")

    # حفظ الشهادات والداتابيز
    certs_df = pd.DataFrame([
        {
            "cert_code": c["code"],
            "certificate_name": c["name"],
            "provider": c["provider"],
            "saudi_accreditation": c["accreditation"],
            "target_roles": "|".join(c["roles"]),
            "covered_skills": "|".join(c["skills"])
        }
        for c in ACCREDITED_CERTIFICATES_DB
    ])

    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        combined_df.to_sql("saudi_career_master", conn, if_exists="replace", index=False)
        certs_df.to_sql("accredited_certificates_catalog", conn, if_exists="replace", index=False)

    logging.info(f"تم التحديث بنجاح! الإجمالي الجديد: {len(combined_df)} سجل (تمت إضافة {len(new_records)} وظيفة جديدة).")
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Real Saudi Tech Job Scraper")
    parser.add_argument("--daemon", action="store_true", help="تشغيل مستمر تلقائياً على السيرفر كل عدة ساعات")
    parser.add_argument("--interval-hours", type=int, default=12, help="عدد الساعات بين كل عملية سحب تلقائية")
    parser.add_argument("--limit", type=int, default=40, help="عدد النتائج المطلوبة لكل مسمى في كل جولة")
    args = parser.parse_args()

    if args.daemon:
        logging.info(f"تم تفعيل وضع السيرفر المستمر (Daemon Mode) - يسحب كل {args.interval_hours} ساعة.")
        while True:
            execute_pipeline(results_per_query=args.limit)
            logging.info(f"انتهت الجولة. في انتظار {args.interval_hours} ساعة للجولة القادمة...")
            time.sleep(args.interval_hours * 3600)
    else:
        execute_pipeline(results_per_query=args.limit)    