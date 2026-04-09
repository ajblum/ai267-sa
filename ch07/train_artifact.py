# KFP Component: Infrastructure handles S3 and UI reporting
from kfp.dsl import component, Input, Output, Dataset, Model, Metrics

@component(base_image=BASE_IMAGE)
def train_model(
    data: Input[Dataset],    
    model: Output[Model],    
    metrics: Output[Metrics] 
):
    import pandas as pd
    import joblib

    # 1. DATA ARTIFACTS: Use .path (Points to LOCAL container storage)
    # The KFP Launcher already downloaded the S3 file here for you!
    data_df = pd.read_csv(data.path)

    # ... Training Logic ...

    # 2. DATA ARTIFACTS: Save to LOCAL .path
    # The KFP Launcher will upload this to S3 automatically after return.
    joblib.dump(clf, model.path)

    # 3. METRIC ARTIFACTS: Specialized SDK methods
    # Automatically populates the 'Visualization' tab in RHOAI.
    metrics.log_metric("accuracy", 0.95)

