"""
Example: Simple Experiment Analysis

This example shows how to analyze a basic A/B test with minimal configuration.
"""

from unified_hex_harvest import ExperimentAnalyzer, create_experiment_config

# Simple experiment configuration
config = create_experiment_config(
    experiment_name='simple_ab_test',
    start_date='2025-01-01',
    end_date='2025-01-31',
    experiment_segments=['control', 'treatment']
)

# Run the analysis
analyzer = ExperimentAnalyzer(config)
analyzer.run_full_analysis()
