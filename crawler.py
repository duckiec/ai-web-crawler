import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO, BytesIO
import zipfile
from urllib.parse import urlparse, urljoin
from collections import defaultdict
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(filename='crawler.log', level=logging.ERROR)

def extract_links(url, include_types, exclude_types, include_keywords, exclude_keywords, depth, include_external, visited=None, auth=None, rate_limit=None, user_agent=None, use_dynamic=False, case_sensitive=False):
    headers = {'User-Agent': user_agent} if user_agent else {}
    if visited is None:
        visited = set()

    if depth < 0 or url in visited:
        return []

    visited.add(url)
    links = []
    try:
        if use_dynamic:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
        else:
            response = requests.get(url, auth=auth, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.find_all('a', href=True):
            link = urljoin(url, a.get('href'))
            if include_types and not any(link.endswith(ext) for ext in include_types):
                continue
            if exclude_types and any(link.endswith(ext) for ext in exclude_types):
                continue
            if include_keywords:
                if case_sensitive and not any(kw in link for kw in include_keywords):
                    continue
                elif not case_sensitive and not any(kw.lower() in link.lower() for kw in include_keywords):
                    continue
            if exclude_keywords:
                if case_sensitive and any(kw in link for kw in exclude_keywords):
                    continue
                elif not case_sensitive and any(kw.lower() in link.lower() for kw in exclude_keywords):
                    continue
            if not include_external:
                parsed_url = urlparse(url)
                parsed_link = urlparse(link)
                if parsed_url.netloc != parsed_link.netloc:
                    continue
            links.append(link)
            if depth > 0:
                links.extend(extract_links(link, include_types, exclude_types, include_keywords, exclude_keywords, depth - 1, include_external, visited, auth, rate_limit, user_agent, use_dynamic, case_sensitive))
            if rate_limit:
                time.sleep(rate_limit)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        st.error(f"Error fetching {url}: {e}")

    return links

def main():
    st.title("Advanced Web Link Extractor")

    # Input Section
    st.header("Input URLs")
    file_upload = st.file_uploader("Upload CSV or TXT file with URLs (TXT: one URL per line, CSV: single column)", type=["csv", "txt"])
    url_input = st.text_area("Or enter URL(s) directly (one per line):", placeholder="Enter a single URL or multiple URLs separated by new lines.")

    st.header("Options")

    # Option to include/exclude filters
    with st.expander("Filters", expanded=True):
        enable_filters = st.checkbox("Enable Filters")
        if enable_filters:
            include_types = st.text_input("Include file types (comma-separated, e.g., .pdf,.jpg):", placeholder="Leave blank if not used")
            exclude_types = st.text_input("Exclude file types (comma-separated, e.g., .pdf,.jpg):", placeholder="Leave blank if not used")
            include_keywords = st.text_input("Include keywords (comma-separated):", placeholder="Leave blank if not used")
            exclude_keywords = st.text_input("Exclude keywords (comma-separated):", placeholder="Leave blank if not used")
        else:
            include_types = ""
            exclude_types = ""
            include_keywords = ""
            exclude_keywords = ""

    # Other Options
    st.subheader("Additional Options")
    depth = st.number_input("Depth of crawling:", min_value=0, max_value=10, value=1)
    include_external = st.checkbox("Include external links", value=True)
    auth_user = st.text_input("Basic Auth Username (Optional):", "")
    auth_pass = st.text_input("Basic Auth Password (Optional):", type="password")
    rate_limit = st.number_input("Rate limit (seconds, Optional):", min_value=0.0, step=0.1, value=0.0)
    user_agent = st.text_input("User-Agent (Optional):", "")
    use_dynamic = st.checkbox("Use dynamic content loading (Selenium)", value=False)
    case_sensitive = st.checkbox("Case-sensitive keyword matching", value=False)

    # File Download Options
    st.subheader("Download Options")
    file_type = st.selectbox("Download as:", ["CSV", "TXT"])
    separate_files = st.checkbox("Create separate file for each URL")
    one_file_per_domain = st.checkbox("Save one file per domain (ZIP)")
    unique_links = st.checkbox("Filter unique links")
    show_counts = st.checkbox("Show number of links per URL")

    if st.button("Extract Links"):
        if file_upload:
            # Read URLs from uploaded file
            if file_upload.type == "text/csv":
                df = pd.read_csv(file_upload, header=None)
                urls = df[0].tolist()
            elif file_upload.type == "text/plain":
                urls = file_upload.read().decode('utf-8').splitlines()
        else:
            # Use URL input from text area
            urls = url_input.splitlines()

        all_links = []
        url_links = defaultdict(list)
        file_type_count = defaultdict(int)

        def add_links(url, links):
            if unique_links:
                links = list(set(links))
            domain = urlparse(url).netloc
            if one_file_per_domain:
                if domain not in url_links:
                    url_links[domain] = []
                url_links[domain].extend(links)
            else:
                url_links[url].extend(links)
            all_links.extend(links)
            for link in links:
                ext = link.split('.')[-1]
                file_type_count[ext] += 1

        include_types_list = [t.strip() for t in include_types.split(',')] if include_types else []
        exclude_types_list = [t.strip() for t in exclude_types.split(',')] if exclude_types else []
        include_keywords_list = [k.strip() for k in include_keywords.split(',')] if include_keywords else []
        exclude_keywords_list = [k.strip() for k in exclude_keywords.split(',')] if exclude_keywords else []

        for url in urls:
            links = extract_links(url, include_types_list, exclude_types_list, include_keywords_list, exclude_keywords_list, depth, include_external, auth=auth_user and auth_pass, rate_limit=rate_limit, user_agent=user_agent, use_dynamic=use_dynamic, case_sensitive=case_sensitive)
            add_links(url, links)

        if show_counts:
            st.write("Number of links per URL/domain:", {k: len(v) for k, v in url_links.items()})
            st.write("File type counts:", dict(file_type_count))

        if all_links:
            st.success(f"Extracted {len(all_links)} links.")
            st.write(all_links)

            if one_file_per_domain:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zipf:
                    for domain, links in url_links.items():
                        file_buffer = StringIO()
                        pd.DataFrame(links, columns=['Links']).to_csv(file_buffer, index=False)
                        file_buffer.seek(0)
                        file_name = f"{domain.replace('http://', '').replace('https://', '').replace('/', '_')}.csv"
                        zipf.writestr(file_name, file_buffer.getvalue())
                zip_buffer.seek(0)
                st.download_button(
                    label="Download as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="links_by_domain.zip",
                    mime="application/zip",
                )
            else:
                if file_type == "CSV":
                    output = StringIO()
                    pd.DataFrame(all_links, columns=['Links']).to_csv(output, index=False)
                    output.seek(0)
                    st.download_button(
                        label="Download as CSV",
                        data=output.getvalue(),
                        file_name="links.csv",
                        mime="text/csv",
                    )

                elif file_type == "TXT":
                    output = StringIO()
                    output.write('\n'.join(all_links))
                    output.seek(0)
                    st.download_button(
                        label="Download as TXT",
                        data=output.getvalue(),
                        file_name="links.txt",
                        mime="text/plain",
                    )

if __name__ == "__main__":
    main()
