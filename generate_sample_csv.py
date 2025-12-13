"""
Generate sample CSV file for batch prediction testing
"""

import pandas as pd
import numpy as np

def generate_sample_csv(filename='sample_batch.csv', n_samples=20):
    """Generate a sample CSV file with random student data"""

    np.random.seed(42)

    data = {
        'Gender': np.random.choice(['Boy', 'Girl'], n_samples),
        'Age': np.random.choice(['1-5', '6-10', '11-15', '16-20', '21-25', '26-30'], n_samples),
        'Education Level': np.random.choice(['School', 'College', 'University'], n_samples),
        'Institution Type': np.random.choice(['Government', 'Non Government'], n_samples),
        'IT Student': np.random.choice(['Yes', 'No'], n_samples),
        'Location': np.random.choice(['Yes', 'No'], n_samples),
        'Load-shedding': np.random.choice(['Low', 'High'], n_samples),
        'Financial Condition': np.random.choice(['Poor', 'Mid', 'Rich'], n_samples),
        'Internet Type': np.random.choice(['Mobile Data', 'Wifi', '2G', '3G', '4G'], n_samples),
        'Network Type': np.random.choice(['2G', '3G', '4G'], n_samples),
        'Class Duration': np.random.choice(['0', '1-3', '3-6'], n_samples),
        'Self Lms': np.random.choice(['Yes', 'No'], n_samples),
        'Device': np.random.choice(['Mobile', 'Tab', 'Computer'], n_samples),
    }

    df = pd.DataFrame(data)

    df.to_csv(filename, index=False)
    print(f"✓ Sample CSV generated: {filename}")
    print(f"  - {n_samples} records created")
    print(f"  - Ready for batch prediction upload")

    print("\nFirst 5 rows:")
    print(df.head().to_string())

    return df

if __name__ == '__main__':
    generate_sample_csv()
