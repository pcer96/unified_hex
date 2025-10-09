"""
Simplified Hex Notebook Template for Experiment Analysis

This template shows how to use the centralized experiment analysis library.
Just modify the experiment parameters below and run the analysis!
"""

# =============================================================================
# 📦 INSTALLATION & IMPORTS
# =============================================================================

# Install required packages first (if not already installed)
# ! uv pip install -q bsp-data-analysis -i https://{ARTIFACTORY_USERNAME}:{ARTIFACTORY_ACCESS_TOKEN}@{ARTIFACTORY_URL}/api/pypi/pypi/simple
# ! uv pip install -q bsp-query-builder -i https://{ARTIFACTORY_USERNAME}:{ARTIFACTORY_ACCESS_TOKEN}@{ARTIFACTORY_URL}/api/pypi/pypi/simple

# Install the centralized library
! uv pip install git+https://github.com/pcer96/unified_hex.git

# Import the centralized library
from unified_hex_harvest import ExperimentAnalyzer, ExperimentConfig, create_experiment_config

# Standard imports (these should already be available in your Hex environment)
import os
from bsp_data_analysis.helpers import *
from bsp_data_analysis.helpers.standard_imports import *
from bsp_query_builder.dialects.big_query.common import (Case, case_cond)
from IPython.display import Markdown, display
from datetime import datetime

# =============================================================================
# 🔐 SETUP CREDENTIALS
# =============================================================================

# Setup credentials (same as your original notebook)
with open('credentials.json', 'w') as f:
    f.write(HARVEST_CREDENTIALS)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'credentials.json'

# =============================================================================
# 🔧 EXPERIMENT CONFIGURATION
# =============================================================================

# 🎯 BASIC EXPERIMENT SETTINGS - MODIFY THESE FOR YOUR EXPERIMENT
experiment_name = 'your_experiment_name_here'
start_date = '2025-01-01'
end_date = str(today().date())  # or specify a date like '2025-01-31'
experiment_segments = ['control_segment', 'treatment_segment']

# 📊 OPTIONAL SETTINGS - MODIFY AS NEEDED
only_free_users = False  # Set to True if experiment is for free users only
include_reach_section = True  # Show user segmentation breakdowns
include_conversion_breakdowns = True  # Show detailed conversion data
include_projections = True  # Include projection analysis

# 📈 METRICS TO ANALYZE - ADD/REMOVE AS NEEDED
metrics_to_analyze = [
    'ConversionToSubscription',
    'ConversionToPaySubscription', 
    'SubscriptionArpu',
    'SubscriptionArps',
    'Retention',
    'AutoRenewOff'
]

# 🧩 BREAKDOWNS TO INCLUDE
breakdowns = [
    'Client',
    'Tenure', 
    'User State'
]

# =============================================================================
# 🚀 RUN THE ANALYSIS
# =============================================================================

# Create experiment configuration
config = create_experiment_config(
    experiment_name=experiment_name,
    start_date=start_date,
    end_date=end_date,
    experiment_segments=experiment_segments,
    only_free_users=only_free_users,
    include_reach_section=include_reach_section,
    include_conversion_breakdowns=include_conversion_breakdowns,
    include_projections=include_projections,
    metrics_list=metrics_to_analyze,
    breakdowns=breakdowns
)

# Initialize the analyzer
analyzer = ExperimentAnalyzer(config)

# Option 1: Run complete analysis with all metrics
# analyzer.run_full_analysis()

# Option 2: Run analysis with specific metrics only
# analyzer.run_full_analysis(metrics_to_analyze=['ConversionToSubscription', 'SubscriptionArpu'])

# Option 3: Analyze individual metrics with custom options
# analyzer.analyze_single_metric('ConversionToSubscription', title='Custom C2S Title')
# analyzer.analyze_single_metric('ConversionToSubscription', uplift_vs='control_segment')

# Option 4: Analyze multiple specific metrics
# analyzer.analyze_specific_metrics(['ConversionToSubscription', 'SubscriptionArpu'])

# For now, let's run the complete analysis
analyzer.run_full_analysis()

# =============================================================================
# 🎨 CUSTOM ANALYSIS (OPTIONAL)
# =============================================================================

# You can also run individual analyses:

# Plot a specific metric with custom title
# analyzer.request_and_plot_metric(
#     metric_name='ConversionToSubscription',
#     title='Custom Title for C2S',
#     uplift_vs='control_segment'  # Show uplift vs control
# )

# Get segmentation breakdowns
# analyzer.plot_segmentation_breakdowns()

# Get conversion breakdown data
# conversion_data = analyzer.get_conversion_breakdowns()
# print(conversion_data.head())

# =============================================================================
# 📝 NOTES
# =============================================================================

"""
This template provides:

1. ✅ Simple configuration - just change the experiment parameters
2. ✅ Automatic analysis - runs all configured metrics and breakdowns  
3. ✅ Consistent output - same format across all experiments
4. ✅ Easy maintenance - update the library to fix bugs or add features
5. ✅ Customizable - can still add custom analysis as needed

To use this template:
1. Copy this code into a new Hex notebook
2. Modify the experiment parameters at the top
3. Run the notebook
4. Get your complete experiment analysis!

The centralized library handles all the complex query building, metric calculations,
and plotting, so you can focus on interpreting results rather than writing code.
"""
