import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import boto3
from moto import mock_s3

from script.download_from_hasty import DownloadAnnotationsFromHasty
from script.upload_to_s3 import Upload2S3


class TestUpload2S3(TestCase):

    @mock_s3
    @patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "test_key",
                             "AWS_SECRET_ACCESS_KEY": "test_secret",
                             "AWS_S3_BUCKET_NAME": "test_bucket",
                             "AWS_S3_BUCKET_REGION": "us-east-1",
                             "HASTY_PROJECT_NAME": "test_project"})
    def test_init_success(self):
        client = boto3.client('s3', region_name=os.environ["AWS_S3_BUCKET_REGION"])
        client.create_bucket(Bucket=os.environ["AWS_S3_BUCKET_NAME"])

        with self.assertLogs("script.upload_to_s3", level="INFO") as mock_logger:
            # Instantiate Upload2S3 class
            uploader = Upload2S3()

        # Assert that the environment variables were correctly retrieved
        self.assertEqual(uploader.access_key_id, "test_key")
        self.assertEqual(uploader.secret_access_key, "test_secret")
        self.assertEqual(uploader.bucket_name, "test_bucket")
        self.assertEqual(uploader.bucket_region, "us-east-1")
        self.assertEqual(uploader.project_name, "test_project")

        # Assert that the object name was correctly generated
        self.assertEqual(uploader.object_name, "test_project_hasty_project_annotations.json")

        # Assert that the S3 client was correctly initialized
        self.assertEqual(uploader.s3._client_config.region_name, "us-east-1")
        self.assertEqual(uploader.s3._request_signer._credentials.access_key, "test_key")
        self.assertEqual(uploader.s3._request_signer._credentials.secret_key, "test_secret")

        # Assert that the logger was called with the correct messages
        self.assertEqual(mock_logger.output[0],
                         "INFO:script.upload_to_s3:Initializing Upload2S3...")
        self.assertEqual(mock_logger.output[1],
                         "INFO:script.upload_to_s3:Getting environment variables...")
        self.assertEqual(mock_logger.output[2],
                         "INFO:script.upload_to_s3:Environment variables successfully retrieved!")
        self.assertEqual(mock_logger.output[3],
                         "INFO:script.upload_to_s3:Initializing S3 client...")
        self.assertEqual(mock_logger.output[4],
                         "INFO:script.upload_to_s3:S3 client initialized!")

    def test_init_missing_env_variables(self):
        with self.assertRaises(KeyError):
            Upload2S3()

    # def test_upload_success(self):
    # TODO: Create some tests for this method
    # ...

    # def test_upload_failure(self):
    # TODO: Create some tests for this method
    # ...


class TestDownloadAnnotationsFromHasty(TestCase):

    @patch("script.download_from_hasty.Client")
    @patch.dict(os.environ, {"HASTY_API_KEY": "test_api_key",
                             "HASTY_PROJECT_NAME": "test_project_name",
                             "WORKING_DIR": "test_working_dir"})
    def setUp(self, mock_client):
        self.mock_client = mock_client

        with self.assertLogs("script.download_from_hasty", level="INFO") as self.mock_logger:
            # Instantiate DownloadAnnotationsFromHasty class
            self.download = DownloadAnnotationsFromHasty()

    def test_init_success(self):
        # Assert logger.info calls were made
        self.assertEqual(self.mock_logger.output[0],
                         "INFO:script.download_from_hasty:Initializing DownloadAnnotationsFromHasty")
        self.assertEqual(self.mock_logger.output[1],
                         "INFO:script.download_from_hasty:Getting environment variables...")
        self.assertEqual(self.mock_logger.output[2],
                         "INFO:script.download_from_hasty:Environment variables successfully retrieved!")
        self.assertEqual(self.mock_logger.output[3],
                         "INFO:script.download_from_hasty:Initializing Hasty client...")
        self.assertEqual(self.mock_logger.output[4],
                         "INFO:script.download_from_hasty:Hasty client initialized!")

        # Assert environment variables were set correctly
        self.assertEqual(self.download.API_KEY, "test_api_key")
        self.assertEqual(self.download.project_name, "test_project_name")
        self.assertEqual(self.download.working_dir, "test_working_dir")

        # Assert Hasty client was initialized correctly
        self.mock_client.assert_called_once_with(api_key="test_api_key")
        self.assertEqual(self.download.client, self.mock_client.return_value)
        self.assertIsNone(self.download.loaded_project)

    def test_init_missing_env_variables(self):
        with self.assertRaises(KeyError):
            DownloadAnnotationsFromHasty()

    def test_load_project_success(self):
        # Create a mock project and mock list of projects
        mock_project = MagicMock()
        mock_project.id = "test_project_id"
        mock_project.name = "test_project_name"
        mock_projects = [mock_project]

        # Set up the mock client object
        self.mock_client.return_value.get_projects.return_value = mock_projects
        self.mock_client.return_value.get_project.return_value = mock_project

        with self.assertLogs(level="INFO") as logs:
            # Call the load_project method
            self.download.load_project()

            # Assert logger.info and logger.error calls were made
            self.assertIn(f"Loading project '{self.download.project_name}'...", logs.output[0])
            self.assertIn(f"Project '{self.download.project_name}' loaded.", logs.output[1])
            self.assertFalse("ERROR" in logs.output)

        # Assert client method calls were made
        self.mock_client.assert_called_once_with(api_key=self.download.API_KEY)
        self.mock_client.return_value.get_projects.assert_called_once_with()
        self.mock_client.return_value.get_project.assert_called_once_with("test_project_id")

        # Assert loaded_project was set correctly
        self.assertEqual(self.download.loaded_project, mock_project)

    def test_load_project_failure(self):
        # Create a mock project and mock list of projects
        mock_project = MagicMock()
        mock_project.id = "not_project_id"
        mock_project.name = "not_my_project_name"
        mock_projects = [mock_project]

        # Set up the mock client object
        self.mock_client.return_value.get_projects.return_value = mock_projects

        with self.assertLogs(level="INFO") as logs:
            with self.assertRaises(ValueError) as e:
                # Call the load_project method and assert it raises a ValueError
                self.download.load_project()
                self.assertEqual(str(e), f"Project '{self.download.project_name}' not found.")

            # Assert logger.info and logger.error calls were made
            self.assertIn(f"Loading project '{self.download.project_name}'...", logs.output[0])
            self.assertIn(f"Project '{self.download.project_name}' not found.", logs.output[1])

        # Assert client method calls were made
        self.mock_client.assert_called_once_with(api_key=self.download.API_KEY)
        self.mock_client.return_value.get_projects.assert_called_once_with()
        self.assertFalse(self.mock_client.return_value.get_project.called)

        # Assert loaded_project is None
        self.assertIsNone(self.download.loaded_project)

    # def test_export_annotations(self, mock_time, mock_zipfile):
    # TODO: Create some tests for this method
    # ...
