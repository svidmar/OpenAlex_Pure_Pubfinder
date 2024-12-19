# Publication Finder Script

This script helps compare an institutions publications from OpenAlex and Pure by identifying publications missing in Pure based on their DOIs. It fetches data from both systems, processes it, and generates a report in Excel format of the publications missing in Pure. 

## Features

- Fetches publications from the Pure API based on a specified publication date range.
- Fetches publications from OpenAlex for a given institution (by ROR ID) and year range.
- Normalizes and compares DOIs from both systems to identify missing publications in Pure.
- Generates a detailed report in Excel format for publications missing in Pure.

## Prerequisites

- Python 3.7+
- Libraries:
  - `requests`
  - `pandas`
  - `tqdm`
  - `openpyxl`

Install the required libraries with:
```bash
pip install requests pandas tqdm openpyxl
```

## Usage

### Script Parameters

1. **Pure API Parameters**
   - `Pure_API_URL`: The endpoint of the Pure API.
   - `Pure_API_KEY`: Your Pure API key.
   - `published_after`: Fetch publications published after this date (e.g., `2023-12-31T00:00:00.000Z`).

2. **OpenAlex Parameters**
   - `ROR_ID`: The ROR ID of your institution.
   - `FROM_YEAR`: Start year for filtering OpenAlex publications.
   - `TO_YEAR`: End year for filtering OpenAlex publications.

3. **Output**
   - `OUTPUT_FILE`: Path to save the Excel report.

### Example Configuration

Update the `main()` function in the script:
```python
Pure_API_URL = "https://your.pure.instance/api/research-outputs"
Pure_API_KEY = "your_api_key_here"
published_after = "2023-12-31T00:00:00.000Z"

ROR_ID = "your_ror_id"
FROM_YEAR = 2024
TO_YEAR = 2024
OUTPUT_FILE = "missing_publications.xlsx"
```

### Running the Script

Run the script using:
```bash
python pubfinder.py
```

## Outputs

The script generates an Excel file containing the following information for missing publications:
- DOI
- Title
- Authors (My Institution)
- Affiliations (My Institution)
- ORCID (My Institution)
- Publication Year
- Publication Date
- Open Access Status
- OA URL
- Accepted/Published Status
- License
- PDF URL
- Source
- Type
- Link to publication (DOI hyperlink if available)

## Error Handling

- The script handles missing or malformed DOIs and logs errors for problematic records.
- If the API request fails, an appropriate error message will be displayed.

## Notes

- Replace placeholders (e.g., `your_api_key_here`, `your_ror_id`) with actual values.
- Ensure your Pure and OpenAlex APIs are accessible and correctly configured.
