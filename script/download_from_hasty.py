import logging
import os
import re
import time
from zipfile import ZipFile

from hasty import Client

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
logger.addHandler(console)


class DownloadAnnotationsFromHasty:

    def __init__(self):

        logger.info("Initializing DownloadAnnotationsFromHasty")

        # Get the environment variables
        logger.info("Getting environment variables...")
        try:
            self.API_KEY = os.environ["HASTY_API_KEY"]
            self.project_name = os.environ["HASTY_PROJECT_NAME"]
            self.working_dir = os.environ["WORKING_DIR"]
        except KeyError:
            logger.error("Missing environment variables")
            raise KeyError("Please set all environment variables")

        logger.info("Environment variables successfully retrieved!")

        # Initialize the Hasty client
        logger.info("Initializing Hasty client...")
        self.client = Client(api_key=self.API_KEY)
        logger.info("Hasty client initialized!")
        self.loaded_project = None

    def run(self):  # pragma: no cover

        # Load the project
        self.load_project()

        # Export the annotations
        self.export_annotations()

    def load_project(self):
        """Loads the project with the given name."""
        logger.info(f"Loading project '{self.project_name}'...")

        # Get the list of all projects.
        projects = self.client.get_projects()

        # Find the project with the given name.
        project = next((p for p in projects if p.name == self.project_name), None)

        # If the project was not found, raise an exception.
        if project is None:
            logger.error(f"Project '{self.project_name}' not found.")
            raise ValueError(f"Project '{self.project_name}' not found.")

        # Load the project
        self.loaded_project = self.client.get_project(project.id)
        logger.info(f"Project '{self.project_name}' loaded.")

    def export_annotations(self):
        """Exports the annotations of the loaded project."""

        # Filename
        filename = (re.sub("[^A-Za-z0-9]+", "_", string=self.project_name) + "_hasty_project_annotations")
        # Zipfile download path
        zip_path = self.working_dir + filename + ".zip"

        # Create export job
        logger.info("Creating annotations export job...")
        export_job = self.loaded_project.export(
            name=filename,
            export_format="json_v1.1",  # Hasty json format
            # All status - Change if you want to export only images with a specific status
            image_status=["NEW", "IN PROGRESS", "TO REVIEW", "DONE", "SKIPPED", "AUTO-LABELED"],
            sign_urls=False,  # Change to add signed URLs
        )

        # Waiting until export job status is DONE meaning ready to be downloaded
        logger.info("Waiting for annotations export to be ready...")
        status = export_job.check_status()
        while status != "DONE":
            time.sleep(2)  # avoid checking too fast as export can take some time
            status = export_job.check_status()
        logger.info("Annotations export ready to be downloaded.")

        # Downloading export (zipfile)
        logger.info("Downloading annotations export...")
        export_job.download(self.working_dir)

        # Unzip json_file and then delete zipfile
        logger.info("Unzipping annotations export...")
        with ZipFile(zip_path, "r") as f:
            f.extractall(self.working_dir)
        logger.info("Annotation file extracted.")

        # Delete zipfile
        try:
            os.remove(zip_path)
        except OSError:
            logger.error("Error while deleting zipfile.")
            raise OSError("Error while deleting zipfile.")
        logger.info("Zipfile deleted.")


if __name__ == "__main__":
    download_annotations = DownloadAnnotationsFromHasty()
    download_annotations.run()
