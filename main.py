# This file contains all the code used in the codelab. 
import sqlalchemy
# from PIL import Image
from google.cloud import storage

# Depending on which database you are using, you'll set some variables differently. 
# In this code we are inserting only one field with one value. 
# Feel free to change the insert statement as needed for your own table's requirements.

# Uncomment and set the following variables depending on your specific instance and database:
connection_name = "aiffel-gn-3:asia-northeast3:viai-images"
table_name = "entries"
db_name = "images"
db_user = "postgres"
db_password = "viai2021"

driver_name = 'postgres+pg8000'
query_string =  dict({"unix_sock": "/cloudsql/{}/.s.PGSQL.5432".format(connection_name)})

sample_input_path = "./sample_images/input/img_0253.png"
sample_output_dent_path = "./sample_images/output/output_0253_dent.png"
sample_output_scratch_path = "./sample_images/output/output_0253_scratch.png"
sample_output_spacing_path = "./sample_images/output/output_0253_scratch.png"


# If the type of your table_field value is a string, surround it with double quotes.
def run_upload(event, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function logs relevant data when a file is changed.

    Args:
        event (dict):  The dictionary with data specific to this type of event.
                       The `data` field contains a description of the event in
                       the Cloud Storage `object` format described here:
                       https://cloud.google.com/storage/docs/json_api/v1/objects#resource
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """

    print('Event ID: {}'.format(context.event_id))
    print('Event type: {}'.format(context.event_type))
    print('Bucket: {}'.format(event['bucket']))
    print('File: {}'.format(event['name'])) #
    print('Metageneration: {}'.format(event['metageneration']))
    print('Created: {}'.format(event['timeCreated'])) #
    print('Updated: {}'.format(event['updated']))

    # 1. Insert new row to the Cloud SQL
    insert(event['name'], event['timeCreated'])
    # 2. Hit the TorchServe inference API
    filename_split = event['name'].split("/")
    original_filename = filename_split[-1]
    predictions = predict(event['bucket'], event['name'], original_filename)
    # 3. Update Cloud Storage - upload masked images to 'images-inferre'
    # update_gcs(predictions)
    # 4. Update Cloud SQL - mark as inferred, and path for the masks
    update_psql(predictions, event['timeCreated'])

def insert(path_original, created_on):
    # request_json = request.get_json()
    table_field1 = "path_original"
    table_field2 = "created_on"
    table_field3 = "is_inferenced"
    table_field4 = "is_inspected"

    stmt = sqlalchemy.text('insert into {} ({}, {}, {}, {}) values ({}, {}, {}, {})'.format(table_name, table_field1, table_field2, table_field3, table_field4, "\'" + path_original + "\'", "\'" + created_on + "\'", "FALSE", "FALSE"))
    
    db = sqlalchemy.create_engine(
      sqlalchemy.engine.url.URL(
        drivername=driver_name,
        username=db_user,
        password=db_password,
        database=db_name,
        query=query_string,
      ),
      pool_size=5,
      max_overflow=2,
      pool_timeout=30,
      pool_recycle=1800
    )
    try:
        with db.connect() as conn:
            conn.execute(stmt)
    except Exception as e:
        print('Error: {}'.format(str(e)))
    print('success')

def predict(bucket, original_path, original_filename):
    print('Predict: ', bucket + "/" + original_filename)
    # TODO: integrate with AI Prediction url
    print("Predict_test: ",sample_output_dent_path)
    # sample payload
    # return [{"class": "dent", "mask": result.squeeze().tolist(), "confidence": conf_score}]

    png_filename = original_filename.split(".")[-2] + ".png"


    # return sample images
    res = {
        "path_original" : original_path,
        "original_filename": original_filename,
        "output_dent_path" : sample_output_dent_path,
        "output_scratch_path" : sample_output_scratch_path,
        "output_spacing_path" : sample_output_spacing_path,
        "destination_blob_name_dent" : "masks-dent/" + png_filename,
        "destination_blob_name_scratch" : "masks-scratch/" + png_filename,
        "destination_blob_name_spacing" : "masks-spacing/" + png_filename,
        "conf_score_dent": 0.3,
        "conf_score_scratch": 0.3,
        "conf_score_spacing": 0.3
    }

    return res

def update_gcs(predictions):
    storage_client = storage.Client()

    bucket_name = "images-inferred"
    output_dent_path = predictions["output_dent_path"]
    output_scratch_path = predictions["output_scratch_path"]
    output_spacing_path = predictions["output_spacing_path"]
    destination_blob_name_dent = predictions["destination_blob_name_dent"]
    destination_blob_name_scratch = predictions["destination_blob_name_scratch"]
    destination_blob_name_spacing = predictions["destination_blob_name_spacing"]

    def upload_blob(bucket_name, source_file_name, destination_blob_name):
        """Uploads a file to the bucket."""
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        print(
            "File {} uploaded to {}.".format(
                source_file_name, destination_blob_name
            )
        )

    # upload_blob(bucket_name, output_dent_path, destination_blob_name_dent)
    # upload_blob(bucket_name, output_scratch_path, destination_blob_name_scratch)
    # upload_blob(bucket_name, output_spacing_path, destination_blob_name_spacing)


def update_psql(predictions, inferenced_on):
    # request_json = request.get_json()
    # table_field = "path_original"
    table_field_key = "path_original"
    table_field_dent = "path_inference_dent"
    table_field_scratch = "path_inference_scratch"
    table_field_spacing = "path_inference_spacing"
    table_field_inferenced = "inferenced_on"
    table_field_conf_score_dent = "conf_score_dent"
    table_field_conf_score_scratch = "conf_score_scratch"
    table_field_conf_score_spacing = "conf_score_spacing"
    table_field_is_inferenced = "is_inferenced"



    # table_field_value = "GCF-test1"
    
    # TODO: update field with input_path as path_original
    stmt = sqlalchemy.text('update {} set {}=\'{}\', {}=\'{}\', {}=\'{}\', {}=\'{}\', {}={}, {}={}, {}={}, {}=\'{}\' where {}=\'{}\''.format(table_name, table_field_dent, predictions["destination_blob_name_dent"] , table_field_scratch, predictions["destination_blob_name_scratch"], table_field_spacing, predictions["destination_blob_name_spacing"], table_field_inferenced, inferenced_on, table_field_conf_score_dent, predictions["conf_score_dent"],table_field_conf_score_scratch, predictions["conf_score_scratch"],table_field_conf_score_spacing, predictions["conf_score_spacing"], table_field_is_inferenced, "True", table_field_key, predictions["path_original"]))
    """
    update {table_name} 
      set {table_field_dent}={predictions.destination_blob_name_dent}, {table_field_scratch}={predictions.destination_blob_name_scratch}, {table_field_spacing}={predictions.destination_blob_name_spacing}
      where {table_field_key}={predictions.path_original}
    """
    # stmt_1 = f"update {table_name} set {table_field_dent}={predictions.destination_blob_name_dent}, {table_field_scratch}={predictions.destination_blob_name_scratch}, {table_field_spacing}={predictions.destination_blob_name_spacing} where {table_field_key}={predictions.path_original}"
    # print("update {table_name} set {table_field_dent}={predictions.destination_blob_name_dent}, {table_field_scratch}={predictions.destination_blob_name_scratch}, {table_field_spacing}={predictions.destination_blob_name_spacing} where {table_field_key}={predictions.path_original}")

    db = sqlalchemy.create_engine(
      sqlalchemy.engine.url.URL(
        drivername=driver_name,
        username=db_user,
        password=db_password,
        database=db_name,
        query=query_string,
      ),
      pool_size=5,
      max_overflow=2,
      pool_timeout=30,
      pool_recycle=1800
    )
    try:
        with db.connect() as conn:
            conn.execute(stmt)
    except Exception as e:
        print('Error: {}'.format(str(e)))
    print('success')


