from kfp import dsl
from kfp.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Model,
    Metrics,
)


@component(base_image=BASE_IMAGE)
def prepare_data(
    train_data: Output[Dataset],
    test_data: Output[Dataset],
):
    import pandas as pd
    from sklearn.model_selection import train_test_split

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

    # Write Dataset artifacts
    train_df.to_csv(
        train_data.path,
        index=False,
    )

    test_df.to_csv(
        test_data.path,
        index=False,
    )


@component(base_image=BASE_IMAGE)
def train_model(
    train_data: Input[Dataset],
    test_data: Input[Dataset],
    model: Output[Model],
    metrics: Output[Metrics],
):
    import joblib
    import pandas as pd

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    # Load prepared Dataset artifacts
    train_df = pd.read_csv(train_data.path)
    test_df = pd.read_csv(test_data.path)

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

    # Write Model artifact
    joblib.dump(
        clf,
        model.path,
    )

    # Record pipeline metrics
    metrics.log_metric(
        "accuracy",
        float(accuracy),
    )


@dsl.pipeline(name="iris-artifact-pipeline")
def iris_pipeline():

    prepare_task = prepare_data()

    train_task = train_model(
        train_data=prepare_task.outputs["train_data"],
        test_data=prepare_task.outputs["test_data"],
    )

