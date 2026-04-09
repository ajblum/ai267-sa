# Standard Python: Requires Manual S3 Management
def train_model(bucket_name, s3_key, model_save_path):
    import pandas as pd
    import joblib
    import boto3
    import os 

    # 1. Credentials: You must manually pull secrets from the OS environment
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
    )

    # 2. Manual Download: Download from S3 to a local temp file
    local_data = "/tmp/data.csv"
    s3.download_file(bucket_name, s3_key, local_data)

    # 3. Read: Read from the local file you just managed
    data = pd.read_csv(local_data)

    # ... Training Logic (clf = model.fit...) ...

    # 4. Manual Upload: Save locally, then push back to S3
    local_model = "/tmp/model.joblib"
    joblib.dump(clf, local_model)
    s3.upload_file(local_model, bucket_name, model_save_path)    
    
    # 5. Metadata: No way to send 'Accuracy' to the RHOAI Dashboard
    print(f"Model Accuracy: {acc}")

