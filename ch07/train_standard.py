from kfp import dsl
from kfp.dsl import component
from kfp import kubernetes


@component(base_image=BASE_IMAGE)
def prepare_data(
    bucket_name: str,
    train_key: str,
    test_key: str,
):
    import os
    import boto3
    import pandas as pd
    from sklearn.model_selection import train_test_split

    # Connect to S3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    # Load raw data
    df = pd.read_csv(
        "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
    )

    # Prepare train/test data
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["species"],
    )

    # Save locally
    local_train = "/tmp/train.csv"
    local_test = "/tmp/test.csv"

    train_df.to_csv(local_train, index=False)
    test_df.to_csv(local_test, index=False)

    # Upload for the next pipeline step
    s3.upload_file(local_train, bucket_name, train_key)
    s3.upload_file(local_test, bucket_name, test_key)


@component(base_image=BASE_IMAGE)
def train_model(
    bucket_name: str,
    train_key: str,
    test_key: str,
    model_key: str,
):
    import os
    import boto3
    import joblib
    import pandas as pd

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    # Connect to S3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    # Download prepared data
    local_train = "/tmp/train.csv"
    local_test = "/tmp/test.csv"

    s3.download_file(bucket_name, train_key, local_train)
    s3.download_file(bucket_name, test_key, local_test)

    # Load prepared data
    train_df = pd.read_csv(local_train)
    test_df = pd.read_csv(local_test)

    X_train = train_df.drop(columns=["species"])
    y_train = train_df["species"]

    X_test = test_df.drop(columns=["species"])
    y_test = test_df["species"]

    # Train model
    clf = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
    )

    clf.fit(X_train, y_train)

    # Evaluate model
    predictions = clf.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    # Save model locally
    local_model = "/tmp/model.joblib"
    joblib.dump(clf, local_model)

    # Upload trained model
    s3.upload_file(
        local_model,
        bucket_name,
        model_key,
    )

    print(f"Accuracy: {accuracy}")


@dsl.pipeline(name="iris-standard-pipeline")
def iris_pipeline():

    prepare_task = prepare_data(
        bucket_name="ml-data",
        train_key="prepared/train.csv",
        test_key="prepared/test.csv",
    )

    train_task = train_model(
        bucket_name="ml-data",
        train_key="prepared/train.csv",
        test_key="prepared/test.csv",
        model_key="models/iris/model.joblib",
    )

    # Inject S3 credentials into both containers
    for task in [prepare_task, train_task]:
        kubernetes.use_secret_as_env(
            task,
            secret_name="aws-credentials",
            secret_key_to_env={
                "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
            },
        )

