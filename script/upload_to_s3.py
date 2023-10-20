import logging
import re
import os

import boto3

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
logger.addHandler(console)


class Upload2S3:

    def __init__(self):

        logger.info("Initializing Upload2S3...")

        # Get the environment variables
        logger.info("Getting environment variables...")
        try:
            self.access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
            self.secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
            self.bucket_name = os.environ["AWS_S3_BUCKET_NAME"]
            self.bucket_region = os.environ["AWS_S3_BUCKET_REGION"]
            self.project_name = os.environ["HASTY_PROJECT_NAME"]
            self.working_dir = os.environ["WORKING_DIR"]
            self.convert_format = os.environ["CONVERT_FORMAT"]
        except KeyError:
            logger.error("Missing environment variables")
            raise KeyError("Please set all environment variables")

        logger.info("Environment variables successfully retrieved!")

        # Object name is the name of the file that will be uploaded to S3 bucket
        self.object_name = (re.sub("[^A-Za-z0-9]+", "_", string=self.project_name) + "_hasty_project_annotations.json")
        self.object_path = self.working_dir + self.object_name

        # Handle conversion when present
        if self.convert_format:
            self.converted_object_name = (
                    re.sub("[^A-Za-z0-9]+", "_", string=self.project_name)
                    + "_hasty_project_annotations." + self.convert_format
            )
            self.converted_object_path = self.working_dir + self.converted_object_name

        # Initialize the S3 client
        logger.info("Initializing S3 client...")
        self.s3 = boto3.client("s3",
                               region_name=self.bucket_region,
                               aws_access_key_id=self.access_key_id,
                               aws_secret_access_key=self.secret_access_key
                               )
        logger.info("S3 client initialized!")

    def run(self):  # pragma: no cover
        """Runs the script."""
        self.upload()

    def upload(self):
        """Uploads the file to the S3 bucket."""
        logger.info("Uploading JSON file to S3 bucket...")
        self.s3.put_object(
            ACL="private",
            Bucket=self.bucket_name,
            Key=self.object_name,
            Body=open(self.object_path, "rb"),
            ServerSideEncryption="AES256",
            StorageClass="INTELLIGENT_TIERING",
        )
        logger.info("JSON file successfully uploaded to S3 bucket!")

        if self.convert_format:
            logger.info("Uploading" + self.convert_format + "file to S3 bucket...")
            self.s3.put_object(
                ACL="private",
                Bucket=self.bucket_name,
                Key=self.converted_object_name,
                Body=open(self.converted_object_path, "rb"),
                ServerSideEncryption="AES256",
                StorageClass="INTELLIGENT_TIERING",
            )
            logger.info(self.convert_format + "file successfully uploaded to S3 bucket!")


if __name__ == "__main__":
    TwoS3 = Upload2S3()
    TwoS3.run()
