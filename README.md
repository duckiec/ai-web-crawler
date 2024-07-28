
# AI Web Crawler
Overview
AI Web Crawler is a web scraping tool built with Python and Streamlit completely **written by AI**. It extracts and filters links from single or multiple URLs and handles dynamic content with Selenium. This project was developed with the help of AI.

# Features
- Dynamic Content Loading: Use Selenium for pages with dynamic content.
- Custom Filters: Include or exclude links by file types and keywords.
- Bulk URL Handling: Process URLs from direct input or uploaded CSV/TXT files.
- Download Options: Save results in CSV or TXT formats, with options for ZIP files per domain.
- Rate Limiting: Set a delay between requests.
- Authentication: Supports basic authentication.
- Installation


# Clone the Repository:



`git clone https://github.com/yourusername/ai-web-crawler.git`
`cd ai-web-crawler`
Install Dependencies:


`pip install -r requirements.txt requirements.txt:`

requirements.txt: 
- streamlit
- requests
- beautifulsoup4
- pandas
- selenium
- webdriver-manager

Run the App:


`streamlit run app.py`

Using the Interface:

Input URLs: Upload a CSV/TXT file or enter URLs directly.
Filters (Optional): Choose to include or exclude links by file types or keywords.
Additional Options: Set crawl depth, external links, rate limits, and user-agent.
Download Results: Choose CSV or TXT format, and optionally save one file per domain as a ZIP.
