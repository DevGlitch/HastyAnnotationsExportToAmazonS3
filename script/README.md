## Script Functions and Usage

This documentation provides an overview of the two Python scripts, ```download_from_hasty.py``` and ```upload_to_s3.py```,
along with their functions and usage.

### download_from_hasty.py

The ```download_from_hasty.py``` script contains a class called ```DownloadAnnotationsFromHasty```,
which has two main functions: ```load_project``` and ```export_annotations```. The class constructor initializes the
Hasty client and the ```loaded_project``` variable. This script can be run by calling the ```run()``` function.

Function: ```load_project()```

    This function loads the project with the given name.
    It first gets the list of all projects and then finds the project with the given name.
    If the project is not found, an exception is raised.
    Otherwise, the function loads the project and sets the loaded project to the loaded_project variable.

Function: ```export_annotations()```

    This function exports the annotations of the loaded project in JSON format.
    It first creates an export job for the loaded project with the given name and format.
    Then, it waits until the export job status is "DONE" which means the annotations are ready to be downloaded.
    It downloads the annotations in a zipfile format and then unzips the file to extract the JSON file containing the annotations.
    Finally, it deletes the zipfile.

To run the script, an API key, project name, and working directory should be set as environment variables.
The run function is called to execute the script which loads the project and exports its annotations.
The annotations are saved in the working directory as a JSON file with the name <project_name>_
hasty_project_annotations.json.

### upload_to_s3.py

The ```upload_to_s3.py``` script contains a class called ```Upload2S3```, which has one main function.
The class constructor initializes the AWS credentials and the S3 client.
This script can be run by calling the ```run()``` function.

Function: ```upload()```

    This function uses the S3 client's put_object() method to upload a file specified in self.object_path to the S3 
    bucket specified in self.bucket_name and with the name specified in self.object_name.
    The put_object() method also specifies additional options such as access control (ACL), server-side encryption 
    (ServerSideEncryption), and storage class (StorageClass) for the object being uploaded.

To use the script, AWS credentials, AWS S3 bucket details, Hasty project name should be set as environment variables.
The run() function is called to execute the script, which uploads the file to the specified S3 bucket.
