# crawler_streamlit.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO, BytesIO
import zipfile
from urllib.parse import urlparse, urljoin

def extract_links(url, include_types, exclude_types, depth, include_external, visited=None):
    if visited is None:
        visited = set()

    if depth < 0 or url in visited:
        return []

    visited.add(url)
    links = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for a in soup.find_all('a', href=True):
            link = urljoin(url, a.get('href'))
            if include_types and not any(link.endswith(ext) for ext in include_types):
                continue
            if exclude_types and any(link.endswith(ext) for ext in exclude_types):
                continue
            if not include_external:
                parsed_url = urlparse(url)
                parsed_link = urlparse(link)
                if parsed_url.netloc != parsed_link.netloc:
                    continue
            links.append(link)
            if depth > 0:
                links.extend(extract_links(link, include_types, exclude_types, depth - 1, include_external, visited))
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {url}: {e}")

    return links

def main():
    st.title("Advanced Web Link Extractor")

    url = st.text_input("Enter URL:")
    bulk_input = st.text_area("Bulk Input (one URL per line):")
    file_type = st.selectbox("Download as:", ["CSV", "TXT"])
    separate_files = st.checkbox("Create separate file for each URL")
    unique_links = st.checkbox("Filter unique links")
    show_counts = st.checkbox("Show number of links per URL")
    include_types = st.text_input("Include file types (comma-separated, e.g., .pdf,.jpg):")
    exclude_types = st.text_input("Exclude file types (comma-separated, e.g., .pdf,.jpg):")
    depth = st.number_input("Depth of crawling:", min_value=0, max_value=10, value=1)
    include_external = st.checkbox("Include external links", value=True)

    if st.button("Extract Links"):
        all_links = []
        url_links = {}

        def add_links(url, links):
            if unique_links:
                links = list(set(links))
            url_links[url] = links
            all_links.extend(links)

        include_types_list = [t.strip() for t in include_types.split(',')] if include_types else []
        exclude_types_list = [t.strip() for t in exclude_types.split(',')] if exclude_types else []

        if url:
            links = extract_links(url, include_types_list, exclude_types_list, depth, include_external)
            add_links(url, links)

        if bulk_input:
            urls = bulk_input.splitlines()
            for u in urls:
                links = extract_links(u, include_types_list, exclude_types_list, depth, include_external)
                add_links(u, links)

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
