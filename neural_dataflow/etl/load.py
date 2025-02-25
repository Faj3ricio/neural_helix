"""
╔═════════════════════════════╗
║Module: Load Module          ║
╚═════════════════════════════╝
Handles the loading of processed data to various destinations, such as
databases, Google Sheets, or external systems, ensuring efficient and
reliable data transfers within the application.
"""
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../.."))
sys.path.insert(0, root_dir)

class DataLoader:
    """
    Uploads data extracted via web scraping to storage systems
    desired, managing the transfer of data captured from the web in a
    efficient and safe.
    """

    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.path_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', '.env')
        self.folder_raw = os.path.join(current_dir, '..', 'data', 'raw')
        self.folder_processed = os.path.join(current_dir, '..', 'data', 'processed')

    def orchestrador(self):
        """
        WIP
        """
        self.load_data_linkedin()

    def load_data_linkedin(self):
        """
         WIP
        """
        pass
