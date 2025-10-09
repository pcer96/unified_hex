"""
Example: Local Development Setup

This example shows how to set up the library for local development with your actual secrets.
"""

from unified_hex_harvest import ExperimentAnalyzer, create_experiment_config, setup_credentials

# Setup credentials for local development
# This will look for local_secrets_actual.py with your real credentials
setup_credentials(use_hex_secrets=False)

# Now you can run your analysis locally
config = create_experiment_config(
    experiment_name='test_experiment',
    start_date='2025-01-01',
    end_date='2025-01-31',
    experiment_segments=['control', 'treatment']
)

analyzer = ExperimentAnalyzer(config)
analyzer.run_full_analysis()
