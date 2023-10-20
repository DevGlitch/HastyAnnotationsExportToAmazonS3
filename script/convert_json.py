import json
import os
import pandas as pd
import logging
import re

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
logger.addHandler(console)


class ConvertJSON:

    def __init__(self):
        logger.info("Initializing ConvertJSON")

        # Get the environment variables
        logger.info("Getting environment variables...")
        try:
            self.project_name = os.environ["HASTY_PROJECT_NAME"]
            self.working_dir = os.environ["WORKING_DIR"]
            self.convert_format = os.environ["CONVERT_FORMAT"]
            self.exclude_labels = os.environ["EXCLUDE_LABELS"].split(',')
        except KeyError:
            logger.error("Missing environment variables")
            raise KeyError("Please set all environment variables")

        if self.convert_format not in ['csv', 'parquet']:
            logger.error("Unsupported format")
            raise ValueError("Unsupported format")

        self.filename = (
                re.sub("[^A-Za-z0-9]+", "_", string=self.project_name) + "_hasty_project_annotations"
        )
        self.json_filename = self.filename + ".json"
        self.csv_filename = self.filename + ".csv"
        self.parquet_filename = self.filename + ".parquet"
        self.data = None
        self.df = None

    def run(self):
        self.load_json()
        self.process_data()
        self.save_data()

    def load_json(self):
        logger.info("Loading JSON data...")
        with open(self.working_dir + self.json_filename, "r") as json_data:
            self.data = json.load(json_data)
        logger.info("JSON data loaded.")

    def process_data(self):
        logger.info("Processing data...")
        df = pd.DataFrame(self.data["images"])

        df['filtered_labels'] = df['labels'].apply(lambda labels: [self.filter_labels(label) for label in labels] if labels else [])

        df = df.explode('filtered_labels', ignore_index=True)

        expected_columns = ['class_name', 'bbox', 'foot', 'sex', 'individual']
        expanded_df = df['filtered_labels'].apply(pd.Series)[expected_columns]

        self.df = pd.concat([df.drop(['filtered_labels'], axis=1), expanded_df], axis=1)
        self.df = self.df.drop(['labels', "tags"], axis=1)

        self.df["image_rating"] = self.df['dataset_name'].str.extract('(\d+)$').astype(int)
        logger.info("Data processed.")

    def filter_labels(self, label):
        filtered_label = {k: v for k, v in label.items() if k not in self.exclude_labels}

        # Flatten 'attributes' into separate columns
        if 'attributes' in filtered_label:
            for attr_key, attr_value in filtered_label['attributes'].items():
                filtered_label[attr_key] = attr_value

        # Remove the 'attributes' key
        filtered_label.pop('attributes', None)

        # Combine columns with class name plus "- Individual" into a single column
        class_name = filtered_label.get('class_name', '')
        individual = filtered_label.pop(class_name + ' - Individual', None)
        if individual:
            filtered_label['individual'] = individual

        return filtered_label

    def save_data(self):
        logger.info("Saving data...")
        if self.convert_format == 'csv':
            self.df.to_csv(self.working_dir + self.csv_filename, index=False)
        elif self.convert_format == 'parquet':
            self.df.to_parquet(self.working_dir + self.parquet_filename, engine="pyarrow", index=False)
        logger.info("Data saved.")


if __name__ == "__main__":
    process_annotations = ConvertJSON()
    process_annotations.run()
