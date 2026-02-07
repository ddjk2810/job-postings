#!/usr/bin/env python3
"""
Generate 1-sentence hiring priority insights for each company based on new job postings.

Analyzes new job titles to detect themes like:
- Geographic expansion (new locations/countries)
- Product line buildouts (repeated keywords)
- Seniority patterns (leadership hiring vs intern classes)
- Department focus (engineering, sales, marketing, etc.)
- Technology themes (AI, cloud, fintech, etc.)
"""

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


def load_company_config():
    """Load company configuration to get display names."""
    config_path = Path('companies_config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            return {c['slug']: c['name'] for c in config.get('companies', [])}
    return {}


def find_two_most_recent_csvs(company_dir, company_slug):
    """Find the two most recent job CSV files for comparison."""
    pattern = re.compile(rf'^{re.escape(company_slug)}_jobs_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$')

    files = []
    for f in company_dir.iterdir():
        match = pattern.match(f.name)
        if match:
            # Exclude "new" and "consolidated" files
            if '_new_' not in f.name and '_consolidated_' not in f.name:
                files.append((match.group(1), f))

    files.sort(key=lambda x: x[0], reverse=True)
    return files[:2] if len(files) >= 2 else None


def load_titles_from_csv(filepath):
    """Load job titles from a CSV file."""
    titles = []
    if not filepath.exists():
        return titles
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            titles.append({
                'title': row.get('title', ''),
                'location': row.get('location', ''),
                'department': row.get('department', '')
            })
    return titles


def classify_seniority(title):
    """Classify a job title by seniority level."""
    t = title.lower()
    if any(x in t for x in ['chief', ' cmo', ' cto', ' cfo', ' coo', ' cso', 'c-suite']):
        return 'c-level'
    if any(x in t for x in [' vp ', 'vp,', 'vp ', 'vice president']):
        return 'vp'
    if 'director' in t:
        return 'director'
    if any(x in t for x in ['principal', 'distinguished', 'staff']):
        return 'staff-principal'
    if any(x in t for x in ['senior', ' sr ', 'sr.', 'sr ']):
        return 'senior'
    if 'manager' in t or 'lead' in t:
        return 'manager-lead'
    if any(x in t for x in ['intern', 'co-op', 'biltern']):
        return 'intern'
    if any(x in t for x in ['associate', 'junior', ' jr ', ' i ', 'entry']):
        return 'junior'
    return 'mid'


def classify_department(title):
    """Classify a job title by department/function."""
    t = title.lower()
    if any(x in t for x in ['engineer', 'developer', 'software', 'sre', 'devops', 'qa ', 'quality assurance', 'sdet']):
        return 'engineering'
    if any(x in t for x in ['data scientist', 'machine learning', 'ml ', ' ai ', 'algorithm']):
        return 'ai-ml'
    if any(x in t for x in ['product manager', 'product design', 'product owner']):
        return 'product'
    if any(x in t for x in ['account executive', 'sales', 'business development', 'sdr', 'bdm', 'revenue']):
        return 'sales'
    if any(x in t for x in ['marketing', 'content', 'brand', 'communications']):
        return 'marketing'
    if any(x in t for x in ['customer success', 'customer service', 'support', 'customer care']):
        return 'customer-success'
    if any(x in t for x in ['recruit', 'talent', 'people', 'hr ', 'human resource']):
        return 'people'
    if any(x in t for x in ['finance', 'accountant', 'accounting', 'tax ', 'fp&a', 'billing', 'payroll']):
        return 'finance'
    if any(x in t for x in ['legal', 'counsel', 'compliance', 'governance']):
        return 'legal-compliance'
    if any(x in t for x in ['security', 'grc', 'sox']):
        return 'security'
    if any(x in t for x in ['consultant', 'implementation', 'professional services', 'solution architect']):
        return 'consulting-services'
    if any(x in t for x in ['design', 'ux ', 'ui ']):
        return 'design'
    if any(x in t for x in ['operations', 'admin', 'office', 'facilities']):
        return 'operations'
    return 'other'


def extract_locations(jobs):
    """Extract notable location patterns from job listings."""
    locations = []
    for j in jobs:
        loc = j.get('location', '').lower()
        locations.append(loc)
    return locations


def detect_geo_themes(new_jobs):
    """Detect geographic expansion themes from new job locations."""
    geo_keywords = {
        'india': ['india', 'bangalore', 'bengaluru', 'pune', 'hyderabad', 'chennai', 'gurugram', 'mumbai', 'coimbatore'],
        'philippines': ['manila', 'philippines'],
        'latin-america': ['brazil', 'sao paulo', 'mexico', 'bogota', 'colombia', 'costa rica', 'monterrey'],
        'europe': ['berlin', 'london', 'dublin', 'paris', 'warsaw', 'krakow', 'amsterdam', 'stockholm', 'copenhagen'],
        'apac': ['singapore', 'tokyo', 'taipei', 'seoul', 'sydney', 'melbourne'],
        'middle-east': ['dubai', 'cairo', 'maadi'],
        'remote': ['remote'],
    }

    geo_counts = Counter()
    for job in new_jobs:
        loc = job.get('location', '').lower()
        title = job.get('title', '').lower()
        combined = loc + ' ' + title
        for region, keywords in geo_keywords.items():
            if any(kw in combined for kw in keywords):
                geo_counts[region] += 1

    return geo_counts


def detect_title_keywords(new_jobs):
    """Detect repeated keywords in new job titles that suggest a theme."""
    word_freq = Counter()
    skip_words = {
        'senior', 'staff', 'principal', 'lead', 'manager', 'director', 'associate',
        'intern', 'junior', 'engineer', 'specialist', 'analyst', 'consultant',
        'representative', 'coordinator', 'administrator', 'i', 'ii', 'iii', 'iv',
        'the', 'and', 'for', 'of', 'in', 'at', 'to', 'a', 'an', '-', '/', '&',
        'remote', 'hybrid', 'us', 'usa', 'uk', 'sr', 'sr.', 'jr', 'jr.',
    }

    for job in new_jobs:
        title = job.get('title', '')
        # Extract meaningful multi-word phrases
        words = re.findall(r'[A-Za-z]+(?:\s+[A-Za-z]+)?', title)
        for word in words:
            w = word.lower().strip()
            if w not in skip_words and len(w) > 2:
                word_freq[w] += 1

    # Return words that appear 3+ times
    return {w: c for w, c in word_freq.items() if c >= 3}


def generate_insight(company_name, new_jobs, prev_count, curr_count):
    """Generate a 1-sentence insight about a company's hiring priorities."""
    if not new_jobs:
        return None

    n = len(new_jobs)

    # Classify all new jobs
    seniority = Counter(classify_seniority(j['title']) for j in new_jobs)
    departments = Counter(classify_department(j['title']) for j in new_jobs)
    geo = detect_geo_themes(new_jobs)
    keywords = detect_title_keywords(new_jobs)

    dept_labels = {
        'engineering': 'engineering',
        'ai-ml': 'AI/ML',
        'sales': 'sales',
        'marketing': 'marketing',
        'product': 'product',
        'customer-success': 'customer success',
        'consulting-services': 'consulting/services',
        'finance': 'finance',
        'people': 'people/recruiting',
        'legal-compliance': 'legal/compliance',
        'security': 'security',
        'design': 'design',
        'operations': 'operations',
        'other': 'mixed functions',
    }

    # Find the strongest signal to lead the sentence
    # Priority: product keyword > geo expansion > department focus > seniority

    # 1. Check for dominant product/brand keyword (e.g. "Datagrid", "MANTL", "Retail")
    notable_keywords = []
    skip_generic = {
        'account', 'executive', 'software', 'product', 'customer', 'sales',
        'support', 'service', 'manager', 'senior', 'engineer', 'development',
    }
    for word, count in sorted(keywords.items(), key=lambda x: -x[1]):
        if count >= 3 and word.lower() not in skip_generic:
            notable_keywords.append((word, count))

    # 2. Geographic themes
    notable_geo = [(r, c) for r, c in geo.most_common(3) if c >= 3 and r != 'remote']

    # 3. Department focus
    top_depts = departments.most_common(3)
    primary_dept = top_depts[0] if top_depts else ('other', 0)

    # 4. Seniority
    senior_plus = seniority.get('c-level', 0) + seniority.get('vp', 0) + seniority.get('director', 0)
    intern_count = seniority.get('intern', 0)

    # Build a natural sentence
    net = curr_count - prev_count

    # Start with the primary action
    if notable_keywords and notable_keywords[0][1] >= 4:
        # Strong product/theme signal
        top_kw = notable_keywords[0][0]
        top_kw_count = notable_keywords[0][1]
        verb = "building out" if net > 5 else "investing in"
        sentence = f"{verb} **{top_kw}** ({top_kw_count} related roles)"
    elif notable_geo and notable_geo[0][1] >= 5:
        # Strong geographic signal
        top_region = notable_geo[0][0].title()
        top_region_count = notable_geo[0][1]
        sentence = f"expanding in **{top_region}** ({top_region_count} roles)"
        notable_geo = notable_geo[1:]  # consume so it's not repeated in secondary
    elif senior_plus >= 4:
        # Leadership hiring wave
        sentence = f"hiring **leadership** ({senior_plus} director+ roles)"
    elif intern_count >= 4:
        # Intern class
        sentence = f"building a **Summer 2026 intern class** ({intern_count} intern roles)"
    elif primary_dept[1] >= 3:
        # Department-led
        dept_name = dept_labels.get(primary_dept[0], primary_dept[0])
        ratio = primary_dept[1] / n
        if ratio > 0.5:
            sentence = f"heavily focused on **{dept_name}** ({primary_dept[1]}/{n} new roles)"
        else:
            sentence = f"primarily hiring in **{dept_name}** ({primary_dept[1]} roles)"
    else:
        sentence = f"adding {n} new roles across multiple functions"

    # Add a secondary detail if there's room
    secondary = []
    if notable_keywords and notable_keywords[0][1] >= 4:
        # Already used keyword as primary, add geo or dept
        if notable_geo:
            secondary.append(f"with expansion into {notable_geo[0][0].title()}")
        elif len(top_depts) >= 2 and top_depts[1][1] >= 3:
            dept2 = dept_labels.get(top_depts[1][0], top_depts[1][0])
            secondary.append(f"plus {dept2} hires")
    else:
        # Add keyword detail if not already primary
        if notable_keywords and notable_keywords[0][1] >= 3:
            kw = notable_keywords[0][0]
            secondary.append(f"with emphasis on {kw}")
        elif notable_geo and notable_geo[0][1] >= 3:
            secondary.append(f"with growth in {notable_geo[0][0].title()}")

    if secondary:
        sentence += ", " + secondary[0]

    return sentence + "."


def generate_all_insights(date_current=None, date_previous=None):
    """
    Generate insights for all companies.

    Args:
        date_current: Specific date to use for current data (YYYY-MM-DD)
        date_previous: Specific date to use for previous data (YYYY-MM-DD)

    Returns:
        list: List of (company_name, insight, new_count, prev_count, curr_count) tuples
    """
    companies_dir = Path('companies')
    company_names = load_company_config()
    insights = []

    for company_dir in sorted(companies_dir.iterdir()):
        if not company_dir.is_dir():
            continue

        slug = company_dir.name
        name = company_names.get(slug, slug.title())

        # Find files to compare
        if date_current and date_previous:
            current_file = company_dir / f"{slug}_jobs_{date_current}.csv"
            previous_file = company_dir / f"{slug}_jobs_{date_previous}.csv"
            if not current_file.exists() or not previous_file.exists():
                continue
        else:
            pair = find_two_most_recent_csvs(company_dir, slug)
            if not pair or len(pair) < 2:
                continue
            current_file = pair[0][1]
            previous_file = pair[1][1]
            date_current = pair[0][0]
            date_previous = pair[1][0]

        # Load and compare
        current_jobs = load_titles_from_csv(current_file)
        previous_jobs = load_titles_from_csv(previous_file)

        prev_titles = set(j['title'] for j in previous_jobs)
        new_jobs = [j for j in current_jobs if j['title'] not in prev_titles]

        if not new_jobs:
            continue

        insight = generate_insight(name, new_jobs, len(previous_jobs), len(current_jobs))
        if insight:
            insights.append((name, insight, len(new_jobs), len(previous_jobs), len(current_jobs)))

    return insights, date_previous, date_current


def format_insights_markdown(insights, date_from, date_to):
    """Format insights as markdown."""
    lines = []
    lines.append(f"\n## Company Hiring Priorities ({date_from} -> {date_to})\n")
    lines.append("One-sentence summary of what each company appears to be prioritizing based on new job postings:\n")

    # Sort by number of new titles descending
    insights.sort(key=lambda x: -x[2])

    for name, insight, new_count, prev_count, curr_count in insights:
        net = curr_count - prev_count
        net_str = f"+{net}" if net >= 0 else str(net)
        lines.append(f"**{name}** ({prev_count}->{curr_count}, {net_str} net): {insight}\n")

    return '\n'.join(lines)


def main():
    """Main function - can be run standalone or imported."""
    import sys

    date_current = None
    date_previous = None

    # Accept optional date arguments
    if len(sys.argv) >= 3:
        date_previous = sys.argv[1]
        date_current = sys.argv[2]

    insights, date_from, date_to = generate_all_insights(date_current, date_previous)

    if not insights:
        print("No new job data to analyze.")
        return

    output = format_insights_markdown(insights, date_from, date_to)
    print(output)

    # Also write to file
    output_file = Path('company_insights.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\nInsights saved to {output_file}")


if __name__ == "__main__":
    main()
