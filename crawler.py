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
from tqdm import tqdm

logging.basicConfig(filename='crawler.log', level=logging.ERROR)

def extract_links(url, include_types, exclude_types, include_keywords, exclude_keywords, depth, include_external, visited=None, auth=None, rate_limit=None, user_agent=None, retries=3):
    headers = {'User-Agent': user_agent} if user_agent else {}
    if visited is None:
        visited = set()

    if depth < 0 or url in visited:
        return []

    visited.add(url)
    links = []
    for _ in range(retries):
        try:
            response = requests.get(url, auth=auth, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                link = urljoin(url, a.get('href'))
                if include_types and not any(link.endswith(ext) for ext in include_types):
                    continue
                if exclude_types and any(link.endswith(ext) for ext in exclude_types):
                    continue
                if include_keywords and not any(kw in link for kw in include_keywords):
                    continue
                if exclude_keywords and any(kw in link for kw in exclude_keywords):
                    continue
                if not include_external:
                    parsed_url = urlparse(url)
                    parsed_link = urlparse(link)
                    if parsed_url.netloc != parsed_link.netloc:
                        continue
                links.append(link)
                if depth > 0:
                    links.extend(extract_links(link, include_types, exclude_types, include_keywords, exclude_keywords, depth - 1, include_external, visited, auth, rate_limit, user_agent, retries))
                if rate_limit:
                    time.sleep(rate_limit)
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            st.error(f"Error fetching {url}: {e}")

    return links

def main():
    st.title("Advanced Web Link Extractor")

    st.sidebar.header("Settings")

    st.sidebar.subheader("URLs")
    url = st.sidebar.text_input("Enter URL:", help="Enter the URL to start crawling from.")
    bulk_input = st.sidebar.text_area("Bulk Input (one URL per line):", help="Enter multiple URLs, one per line, for bulk extraction.")

    st.sidebar.subheader("Link Filtering")
    include_types = st.sidebar.text_input("Include file types (comma-separated):", help="File types to include, e.g., .pdf,.jpg")
    exclude_types = st.sidebar.text_input("Exclude file types (comma-separated):", help="File types to exclude, e.g., .pdf,.jpg")
    include_keywords = st.sidebar.text_input("Include keywords (comma-separated):", help="Keywords to include in links.")
    exclude_keywords = st.sidebar.text_input("Exclude keywords (comma-separated):", help="Keywords to exclude in links.")

    st.sidebar.subheader("Crawling Settings")
    depth = st.sidebar.number_input("Depth of crawling:", min_value=0, max_value=10, value=1, help="Depth of crawling: 0 for the first page, 1 for one level deeper, etc.")
    include_external = st.sidebar.checkbox("Include external links", value=True, help="Whether to include links from other domains.")
    rate_limit = st.sidebar.number_input("Rate limit (seconds):", min_value=0.0, step=0.1, help="Rate limit between requests in seconds.")
    user_agent = st.sidebar.text_input("User-Agent:", help="Custom User-Agent string for the requests.")

    st.sidebar.subheader("Authentication")
    auth_user = st.sidebar.text_input("Basic Auth Username:", help="Username for basic authentication.")
    auth_pass = st.sidebar.text_input("Basic Auth Password:", type="password", help="Password for basic authentication.")

    st.sidebar.subheader("Output Options")
    file_type = st.sidebar.selectbox("Download as:", ["CSV", "TXT"], help="Format to download the extracted links.")
    separate_files = st.sidebar.checkbox("Create separate file for each URL", help="Create a separate file for each URL.")
    unique_links = st.sidebar.checkbox("Filter unique links", help="Remove duplicate links.")
    show_counts = st.sidebar.checkbox("Show number of links per URL", help="Display the number of links extracted from each URL.")

    auth = HTTPBasicAuth(auth_user, auth_pass) if auth_user and auth_pass else None

    if st.sidebar.button("Extract Links"):
        all_links = []
        url_links = defaultdict(list)
        file_type_count = defaultdict(int)

        def add_links(url, links):
            if unique_links:
                links = list(set(links))
            url_links[url].extend(links)
            all_links.extend(links)
            for link in links:
                ext = link.split('.')[-1]
                file_type_count[ext] += 1

        include_types_list = [t.strip() for t in include_types.split(',')] if include_types else []
        exclude_types_list = [t.strip() for t in exclude_types.split(',')] if exclude_types else []
        include_keywords_list = [kw.strip() for kw in include_keywords.split(',')] if include_keywords else []
        exclude_keywords_list = [kw.strip() for kw in exclude_keywords.split(',')] if exclude_keywords else []

        if url:
            with st.spinner(f'Extracting links from {url}...'):
                links = extract_links(url, include_types_list, exclude_types_list, include_keywords_list, exclude_keywords_list, depth, include_external, auth=auth, rate_limit=rate_limit, user_agent=user_agent)
                add_links(url, links)

        if bulk_input:
            urls = bulk_input.splitlines()
            progress_bar = st.progress(0)
            total_urls = len(urls)
            for i, u in enumerate(urls):
                with st.spinner(f'Extracting links from {u}...'):
                    links = extract_links(u, include_types_list, exclude_types_list, include_keywords_list, exclude_keywords_list, depth, include_external, auth=auth, rate_limit=rate_limit, user_agent=user_agent)
                    add_links(u, links)
                    progress_bar.progress((i + 1) / total_urls)

        if show_counts:
            st.write({url: len(links) for url, links in url_links.items()})

        if all_links:
            st.success(f"Extracted {len(all_links)} links.")
            st.write(all_links)

            if separate_files:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zipf:
                    for url, links in url_links.items():
                        file_buffer = StringIO()
                        pd.DataFrame(links, columns=['Links']).to_csv(file_buffer, index=False)
                        file_buffer.seek(0)
                        file_name = f"{url[:50].replace('http://', '').replace('https://', '').replace('/', '_')}.csv"
                        zipf.writestr(file_name, file_buffer.getvalue())
                zip_buffer.seek(0)
                st.download_button(
                    label="Download as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="links.zip",
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
