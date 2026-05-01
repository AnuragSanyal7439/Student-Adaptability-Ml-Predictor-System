"""
Generate a sample CSV file for testing batch predictions.
"""

import numpy as np
import pandas as pd

from model_training import FEATURE_OPTIONS


def generate_sample_csv(filename: str = "sample_batch.csv", n_samples: int = 20) -> pd.DataFrame:
    """Generate a valid sample CSV using the same options as the API."""
    np.random.seed(42)

    data = {
        feature: np.random.choice(options, n_samples)
        for feature, options in FEATURE_OPTIONS.items()
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

    print(f"Sample CSV generated: {filename}")
    print(f"- {n_samples} records created")
    print("- Ready for batch prediction upload")
    print("\nFirst 5 rows:")
    print(df.head().to_string())

    return df


if __name__ == "__main__":
    generate_sample_csv()
