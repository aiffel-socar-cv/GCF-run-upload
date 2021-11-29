# This file contains all the code used in the codelab. 
import sqlalchemy

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
    predict()
    # 3. Update Cloud SQL - mark as inferred, and path for the masks
    # update()

def insert(path_original, created_on):
    # request_json = request.get_json()
    table_field1 = "path_original"
    table_field2 = "created_on"

    stmt = sqlalchemy.text('insert into {} ({}, {}) values ({}, {})'.format(table_name, table_field1, table_field2, path_original, created_on))
    
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

def predict(original_path):
    print('Predict: ', original_path)

def update():
    # request_json = request.get_json()
    table_field = "path_original"
    table_field_value = "GCF-test1"
    
    stmt = sqlalchemy.text('insert into {} ({}) values ({})'.format(table_name, table_field, table_field_value))
    
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