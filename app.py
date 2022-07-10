import os
import botocore
import boto3
import flask

from dotenv import load_dotenv


def get_s3_resource():
  return boto3.resource(
      service_name='s3',
      endpoint_url=os.environ['S3_ENDPOINT'],
      aws_access_key_id=os.environ['S3_KEY_ID'],
      aws_secret_access_key=os.environ['S3_APPLICATION_KEY'],
      config=botocore.client.Config(signature_version='s3v4'))


app = flask.Flask(__name__)
load_dotenv(app.root_path + '/.env')

def auth(fn):
  def _auth_fn():
    if flask.request.args['appKey'] != os.environ['APP_KEY']:
      return flask.Response('invalid appKey', status=403)
    return fn()
  return _auth_fn()
  


@app.route('/database/upload', methods=['POST'])
@auth
def backup_database():
  db_file = flask.request.files['db_file']
  s3 = get_s3_resource()
  user_id = flask.request.form['userId']
  s3.Bucket('speech-cards-backup').put_object(
      Key=user_id, Body=db_file.stream.read())
  # Set Access-Control-Allow-Origin to '*' and return
  return flask.Response(
    'backup successful', status=200, 
    headers={'Access-Control-Allow-Origin': '*'})


@app.route('/database/download', methods=['GET'])
@auth
def fetch_database_backup():
  s3 = get_s3_resource()
  database_id = flask.request.args.get('id')

  # if id is None, find the key with the most recent timestamp
  if database_id is None:
    # TODO: this lists all objects in the bucket, switch to a more efficient method
    database_id = sorted(
        s3.Bucket('speech-cards-backup').objects.all(),
        key=lambda x: x.last_modified,
        reverse=True)[0].key

  obj = s3.Object('speech-cards-backup', database_id)
  data = obj.get(ResponseContentEncoding='application/binary')['Body'].read()

  return flask.Response(data, status=200, content_type='application/sqlite3')


@app.route('/database/list', methods=['GET'])
@auth
def index():
  s3 = get_s3_resource()
  bucket = s3.Bucket('speech-cards-backup')
  keys = [obj.key for obj in bucket.objects.all()]
  return flask.jsonify(keys)


if __name__ == '__main__':
  app.run(port=int(os.environ.get('PORT', '8000')))
