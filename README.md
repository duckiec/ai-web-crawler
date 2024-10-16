Here’s an updated version of your README for the AI Web Crawler project. It includes some clarifications and formatting improvements for better readability:

```markdown
# AI Web Crawler

## Overview
AI Web Crawler is a web scraping tool built with Python and Streamlit, completely **written by AI**. It extracts and filters links from single or multiple URLs and handles dynamic content with Selenium. This project was developed with the help of AI.

## Features
- **Dynamic Content Loading**: Uses Selenium for pages with dynamic content.
- **Custom Filters**: Include or exclude links based on file types and keywords.
- **Bulk URL Handling**: Process URLs from direct input or uploaded CSV/TXT files.
- **Download Options**: Save results in CSV or TXT formats, with options for ZIP files per domain.
- **Rate Limiting**: Set a delay between requests to avoid overwhelming servers.
- **Authentication**: Supports basic authentication.

## Installation

### Clone the Repository:
```bash
git clone https://github.com/yourusername/ai-web-crawler.git
cd ai-web-crawler
```

### Install Dependencies:
Run the following command to install the required packages:
```bash
pip install -r requirements.txt
```

### `requirements.txt`:
The dependencies include:
- `streamlit`
- `requests`
- `beautifulsoup4`
- `pandas`
- `selenium`
- `webdriver-manager`

## Run the App:
To start the application, run:
```bash
streamlit run app.py
```

## Using the Interface:
1. **Input URLs**: Upload a CSV/TXT file or enter URLs directly.
2. **Filters (Optional)**: Choose to include or exclude links by file types or keywords.
3. **Additional Options**: Set crawl depth, include/exclude external links, configure rate limits, and specify the user-agent.
4. **Download Results**: Choose to save results in CSV or TXT format, and optionally save one file per domain as a ZIP.

```

### Key Changes
- Added section headings for clarity.
- Improved formatting for commands and features.
- Fixed a minor typo in the "Installation" section and clarified the `requirements.txt` explanation.
- Removed unnecessary repetition for clarity.

Feel free to modify any part to better suit your project's style or details!
