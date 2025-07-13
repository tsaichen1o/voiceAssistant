"""
Contains core functionalities of LLM, including extract information from website
Source: https://github.com/y-pred/Langchain/blob/main/Langchain%202.0/RAG_Conversational_Chatbot.ipynb
"""
import os
from typing import List
import requests
import json
# For web scraping
import bs4
from langchain_community.document_loaders import WebBaseLoader

MAIN_URL = "https://www.tum.de/en/studies/degree-programs"

class WebScraper:
    """Class for web scraping and text processing.
    NOTE: this just works for TUM website, for others, you might need to modify
    the location in HTML that store information you want to extract.
    """    
    def __init__(self, main_url: str):
        """Initialize the WebScraper class.
        Args:
            main_url (str): The URL of the main page to scrape.
        """
        self.main_url = main_url
    
    def get_raw_page_content(self, url: str, interested_class_name: str) -> str:
        """Get raw content of the interested area in the page
        Args:
            url (str): The URL of the page to scrape.
            interested_class_name (str): the name of the class in HTML that
            contains the information that we are interested in
        """
        # Limit parsing to the specified class only
        bs4_strainer = bs4.SoupStrainer(class_=interested_class_name)
        # Load the page content
        loader = WebBaseLoader(
            web_path=url,
            bs_kwargs={"parse_only": bs4_strainer},
        )
        docs = loader.load()
        # Transfer the list of document into text
        text = ""
        for doc in docs:
            text += doc.page_content + "\n"
        text = text.strip()
        text = text.replace('\n', ' ').replace('\t', ' ')
        return text

    def get_main_info(self) -> dict:
        """Get interested information in main url, including the list of
        programs and their urls.
        Returns:
            dict: dictionary where keys are program name, values are dictionary
            contains program information
        """
        # Extract html file of the mail_url
        page = requests.get(self.main_url, timeout=10)
        soup = bs4.BeautifulSoup(page.text, 'html')
        # Find <option> item in html, which include TUM program's name and url
        options_list = soup.find_all('option')
        programs_dict = {}
        for option in options_list:
            # Find info in <option ... data-url=program_url>program_name</option>
            program_name = option.text.strip()
            program_url = option.get('data-url')
            if program_url:
                programs_dict[program_name] = {"url": f"https://www.tum.de{program_url}"}
        return programs_dict
    
    def get_program_info(self, url: str) -> dict:
        """Get interested information from the url of a program, including the
        program summary in the beginning, and Key Data
        Args:
            url (str): the url of the program
        Return:
            dict: the dictionary part in the tum program dictionary that
            corresponds to program need update
        """
        # Dictionary stores that part that need to be added to tum program dict
        update_info = {}
        # Extract html file of the mail_url
        page = requests.get(url, timeout=10)
        soup = bs4.BeautifulSoup(page.text, 'html')
        # Find program description in <p class="lead-text">program_description</p>
        program_description = soup.find("p", class_="lead-text")
        # Find key datas in <div class="flex__md-6 flex__xl-4">
        # <strong>data_name</strong><ul><li>data_values</li></ul></div>
        divs_list = soup.find_all("div", class_="flex__md-6 flex__xl-4")
        for div in divs_list:
            strong_tag = div.find("strong")
            ul_tag = div.find("ul")
            # Extract data_name
            if strong_tag:
                data_name = strong_tag.get_text(strip=True)
                data_name = data_name.replace('\n', ' ').replace('\t', ' ')
            else:
                data_name = ""
            # Extract data_values
            data_values = []
            if ul_tag:
                for li in ul_tag.find_all("li"):
                    value = li.get_text(strip=True)
                    value = value.replace('\n', ' ').replace('\t', ' ')
                    data_values.append(value)
            update_info[f"{data_name}"] = data_values
        # Add program description into updated tum program dictionary
        update_info["program description"] = program_description.text.strip()
        return update_info
    
    def get_tum_programs_dict(self) -> dict:
        """Load from or create tum_programs_dict.json"""
        file_path = r"./app/tests/fixed_data/tum_programs_dict.json"
        # Check if file exists and has valid content
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, dict) and data:  # Optional: make sure it's not empty
                        print("Loaded existing tum_programs_dict.json")
                        return data
            except (OSError, IOError, json.JSONDecodeError) as e:
                print(f"Error reading existing JSON file, will regenerate: {e}")
        # Otherwise, create the file
        print("Creating tum_programs_dict.json")
        programs_dict = self.get_main_info()
        for key, value in programs_dict.items():
            page_content = self.get_raw_page_content(value["url"], "flex__lg-8")
            programs_dict[key].update({"program description": page_content})
            print(f"Collected information for program {key}")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(programs_dict, file, ensure_ascii=False, indent=4)
            print("Stored new data in .app/tests/fixed_data/tum_programs_dict.json")
        except (OSError, IOError, json.JSONDecodeError) as e:
            print(f"Error while saving the TUM programs data: {e}")
        return programs_dict


def main():
    """Call WebScraper to get all TUM programs information"""
    web_scrapper = WebScraper(MAIN_URL)
    tum_programs_dict = web_scrapper.get_tum_programs_dict()


if __name__ == "__main__":
    main()
