import os
import requests
import json
import time


class ITUCourseDataFetcher:
    """Fetches and saves course data from ITU's API."""

    BASE_URL_BRANCH_CODES = "https://obs.itu.edu.tr/public/DersProgram/SearchBransKoduByProgramSeviye"
    BASE_URL_COURSE_DATA = "https://obs.itu.edu.tr/public/DersProgram/DersProgramSearch"
    OUTPUT_DIR = "data"
    PROGRAM_LEVEL = "LS"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        }

    def fetch_branch_codes(self):
        """Fetch branch codes based on the program level."""
        params = {"programSeviyeTipiAnahtari": self.PROGRAM_LEVEL}
        response = requests.get(self.BASE_URL_BRANCH_CODES, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch branch codes: {response.status_code}")

    def fetch_course_data(self, branch_code_id):
        """Fetch course data for a specific branch code."""
        params = {
            "ProgramSeviyeTipiAnahtari": self.PROGRAM_LEVEL,
            "dersBransKoduId": branch_code_id
        }
        response = requests.get(self.BASE_URL_COURSE_DATA, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch course data for branch code {branch_code_id}: {response.status_code}")

    def save_to_file(self, filename, data):
        """Save data to a JSON file."""
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(self.OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def run(self):
        """Main function to fetch and save all course data."""
        try:
            branch_codes = self.fetch_branch_codes()
            for branch in branch_codes:
                branch_code_id = branch["bransKoduId"]
                branch_code = branch["dersBransKodu"]
                print(f"Fetching data for {branch_code} (ID: {branch_code_id})...")
                course_data = self.fetch_course_data(branch_code_id)
                self.save_to_file(f"{branch_code}.json", course_data)
                print(f"Data for {branch_code} saved successfully.")
                time.sleep(1)

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    fetcher = ITUCourseDataFetcher()
    fetcher.run()
