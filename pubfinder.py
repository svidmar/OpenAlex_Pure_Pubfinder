import requests
import json
from tqdm import tqdm  # Import tqdm for progress bar
import pandas as pd


def normalize_doi(doi):
    """Normalize DOI by removing 'https://doi.org/' and making it case-insensitive."""
    if doi.startswith("https://doi.org/"):
        return doi[len("https://doi.org/"):].lower()
    return doi.lower()


def fetch_Pure_publications(api_url, api_key, published_after_date, size=100):
    """Fetch all publications from the Pure API with pagination."""
    all_publications = []
    offset = 0

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "api-key": api_key,
    }
    payload = {
        "size": size,
        "offset": offset,
        "publishedAfterDate": published_after_date,
    }

    # Get total count for progress bar
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Failed to fetch data from Pure API. Status code: {response.status_code}")
        return []

    total_count = response.json().get("count", 0)
    print(f"Total items to fetch from Pure API: {total_count}")

    with tqdm(total=total_count, desc="Fetching Pure Publications", unit="items") as pbar:
        while True:
            payload["offset"] = offset
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"Failed to fetch data from Pure API. Status code: {response.status_code}")
                break

            data = response.json()
            items = data.get("items", [])
            all_publications.extend(items)

            pbar.update(len(items))
            if len(items) < size:
                break
            offset += size

    return all_publications


def fetch_openalex_publications(ror_id, from_year, to_year):
    """
    Fetch publications from OpenAlex for a specific ROR ID within a year range.

    Returns a dictionary where keys are work IDs and values are metadata dictionaries.
    """
    api_url = f"https://api.openalex.org/works"
    cursor = "*"
    metadata = {}

    print("Fetching publications from OpenAlex...")
    while cursor:
        response = requests.get(api_url, params={
            "filter": f"institutions.ror:{ror_id},publication_year:{from_year}-{to_year}",
            "per-page": 200,
            "cursor": cursor
        })
        response.raise_for_status()
        data = response.json()

        # Add results to the metadata dictionary
        for work in data["results"]:
            try:
                work_id = work["id"]
                dois = work.get("ids", {}).get("doi", [])
                if isinstance(dois, str):  # If it's a single DOI, convert to a list
                    dois = [dois]
                normalized_dois = [normalize_doi(doi) for doi in dois if doi]

                # Filter authors, affiliations, and ORCID for your institution
                authors_my_institution = []
                affiliations_my_institution = []
                orcids_my_institution = []

                for author in work.get("authorships", []):
                    for aff in author.get("affiliations", []):
                        if "institution_ids" in aff and "https://openalex.org/XYZ123" in aff["institution_ids"]: #replace XYZ123 with institutionID from OpenAlex
                            authors_my_institution.append(author["author"]["display_name"])
                            affiliations_my_institution.append(aff["raw_affiliation_string"])
                            orcid = author["author"].get("orcid", "Not Available")
                            orcids_my_institution.append(orcid)

                metadata[work_id] = {
                    "dois": normalized_dois if normalized_dois else ["No DOI"],  # Handle missing DOIs
                    "title": work.get("title", "No Title"),
                    "authors_my_institution": authors_my_institution,
                    "affiliations_my_institution": affiliations_my_institution,
                    "orcids_my_institution": orcids_my_institution,
                    "publication_year": work.get("publication_year", "Unknown"),
                    "publication_date": work.get("publication_date", "Unknown"),
                    "is_oa": work.get("open_access", {}).get("is_oa", False),
                    "oa_status": work.get("open_access", {}).get("oa_status", "Unknown"),
                    "oa_url": work.get("open_access", {}).get("oa_url", "Not Available"),
                    "is_accepted": work.get("primary_location", {}).get("is_accepted", False),
                    "is_published": work.get("primary_location", {}).get("is_published", False),
                    "license": work.get("primary_location", {}).get("license", "Unknown"),
                    "pdf_url": work.get("primary_location", {}).get("pdf_url", "Not Available"),
                    "source": (work.get("primary_location", {}).get("source") or {}).get("display_name", "Unknown"),
                    "type": work.get("type", "Unknown") 
                }

            except Exception as e:
                print(f"--- Error processing work ID {work.get('id', 'Unknown')} ---")
                print(f"Error: {e}")
                print(f"Problematic record: {json.dumps(work, indent=2)}")
                print("--- End of problematic record ---")
                continue

        cursor = data["meta"].get("next_cursor")
        if cursor:
            cursor = cursor.encode("utf-8").decode("utf-8")

    print(f"Total publications fetched from OpenAlex: {len(metadata)}")
    return metadata


def extract_Pure_dois(Pure_publications):
    """
    Extract DOIs from Pure publications. Handles multiple DOIs and skips entries without DOIs.
    """
    dois = set()
    for pub in Pure_publications:
        electronic_versions = pub.get("electronicVersions", [])
        for version in electronic_versions:
            doi = version.get("doi")
            if doi:
                normalized_doi = normalize_doi(doi)
                dois.add(normalized_doi)
    return dois



def generate_missing_in_Pure_report(openalex_metadata, Pure_dois, output_file):
    """
    Generate a report of publications from OpenAlex missing in Pure.

    Parameters:
    - openalex_metadata: Metadata from OpenAlex.
    - Pure_dois: DOIs present in Pure (already normalized).
    - output_file: File path for the output Excel file.
    """
    missing_data = []

    # Debugging: Count items without DOIs
    no_doi_count = 0

    for work_id, meta in openalex_metadata.items():
        # Normalize OpenAlex DOIs for comparison
        openalex_dois = [normalize_doi(doi) for doi in meta["dois"] if doi != "No DOI"]

        # Check if any DOI from OpenAlex exists in Pure
        if not any(doi in Pure_dois for doi in openalex_dois):
            doi_hyperlink = (
                ", ".join([f"https://doi.org/{doi}" for doi in meta["dois"] if doi != "No DOI"])
                if meta["dois"]
                else "No DOI"
            )
            # Filter out None values in ORCID list
            orcids_filtered = [orcid for orcid in meta["orcids_my_institution"] if orcid is not None]

            missing_data.append({
                "DOI": ", ".join(meta["dois"]) if meta["dois"] else "No DOI",
                "Title": meta["title"],
                "Authors (My Institution)": "; ".join(meta["authors_my_institution"]) if meta["authors_my_institution"] else "Not Available",
                "Affiliations (My Institution)": "; ".join(meta["affiliations_my_institution"]) if meta["affiliations_my_institution"] else "Not Available",
                "ORCID (My Institution)": "; ".join(orcids_filtered) if orcids_filtered else "Not Available",
                "Publication Year": meta["publication_year"],
                "Publication Date": meta["publication_date"],
                "Is OA": meta["is_oa"],
                "OA Status": meta["oa_status"],
                "OA URL": meta["oa_url"],
                "Accepted": meta["is_accepted"],
                "Published": meta["is_published"],
                "License": meta["license"],
                "PDF URL": meta["pdf_url"],
                "Type": meta.get("type", "Unknown"),  
                "Source": meta.get("source", "Unknown"),  
                "Link": doi_hyperlink
            })

        # Count publications without DOIs
        if not openalex_dois:
            no_doi_count += 1

    print(f"Number of OpenAlex works without DOIs: {no_doi_count}")

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(missing_data)

    # Save the DataFrame to an Excel file
    df.to_excel(output_file, index=False)
    print(f"Report of missing DOIs in Pure saved to {output_file}")


def main():
    Pure_API_URL = "https://xyz.elsevierpure.com/ws/api/524/research-outputs" # Replace instance URL
    Pure_API_KEY = "MY_API_KEY" # Replace with Pure API key
    published_after = "2023-12-31T00:00:00.000Z" # Use to limit the number of research output pulled from Pure

    ROR_ID = "xyz" # Add institution ROR ID
    FROM_YEAR = 2024 # Define year range for OpenAlex
    TO_YEAR = 2024 # Define year range for OpenAlex
    OUTPUT_FILE = "/users/.../pubs_missing_in_pure.xlsx" # Path to Excel file output

    Pure_publications = fetch_Pure_publications(Pure_API_URL, Pure_API_KEY, published_after)
    Pure_dois = extract_Pure_dois(Pure_publications)

    openalex_metadata = fetch_openalex_publications(ROR_ID, FROM_YEAR, TO_YEAR)

    generate_missing_in_Pure_report(openalex_metadata, Pure_dois, OUTPUT_FILE)


if __name__ == "__main__":
    main()
