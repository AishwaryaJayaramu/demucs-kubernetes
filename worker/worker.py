from urllib import request
import redis
import os 
from minio import Minio
import json
print("Starting worker thread")

redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

r = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

REDIS_KEY = "toWorkers"
input_dir = "/tmp/input"
output_dir = "/tmp/output"

BUCKET_NAME = "working"
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"
print(f"Getting minio connection now for host {minioHost}!")

MINIO_CLIENT = None
try:
    MINIO_CLIENT = Minio(minioHost, access_key=minioUser, secret_key=minioPasswd, secure=False)
    print("Got minio connection",MINIO_CLIENT )
except Exception as exp:
    print(f"Exception raised in worker loop: {str(exp)}")

output_files = os.path.join(output_dir, "mdx_extra_q")

def get_file_to_input_dir(file_name):
    print("Downloading the file", file_name)
    file_path = os.path.join(input_dir, file_name)
    MINIO_CLIENT.fget_object(BUCKET_NAME, file_name, file_path)
    print("Placed file in temporary location", file_path)
    print("Files : ", os.listdir(input_dir))
    return file_path

def create_bucket(bucket_name):
    found = MINIO_CLIENT.bucket_exists(bucket_name)
    if not found:
       MINIO_CLIENT.make_bucket(bucket_name)
    else:
       print("Bucket already exists")

def upload_file(file_name, bucket_name, file_path):
    MINIO_CLIENT.fput_object(bucket_name, file_name, file_path)
    
def upload_dir(file_dir, file_hash):
    files = os.listdir(file_dir)
    print("Available files in dir", file_dir, files)
    for file in files:
        print("Uploading file", file, 'To bucket', file_hash)
        file_path = os.path.join(file_dir, file)
        upload_file(file, file_hash, file_path)
    print("Uploaded all files in dir file_dir")

def user_counter():
    try:
        print("Looking for a message")
        message = r.blpop(REDIS_KEY)
        print("Found message", message)
        file_data = json.loads(message[1].decode())
        file_name = file_data['file_name']
        context   = file_data['context']
        file_path = get_file_to_input_dir(file_name)
        command = f"python -u -m demucs.separate --out {output_dir} {file_path} --mp3"
        os.system(command)
        bucket_name = file_name[:-4]
        create_bucket(bucket_name)
        upload_dir(os.path.join(output_dir, "mdx_extra_q", bucket_name), bucket_name)
    except Exception as exp:
        print(f"Exception raised in worker loop: {str(exp)}")

while True:
  user_counter()