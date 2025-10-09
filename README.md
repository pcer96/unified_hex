# Harvest Experiment Analysis Library

A centralized Python library for experiment analysis in Hex notebooks. This library eliminates code duplication and makes it easy to maintain and update analysis logic across all your experiments.

## 🎯 Problem Solved

- **Before**: Copy-paste Hex notebooks, modify a few lines, struggle to keep templates updated
- **After**: Centralized library with simple configuration - just specify experiment parameters and get complete analysis

## 🚀 Quick Start

### 1. Install the Library

```bash
# In your Hex notebook or terminal
! pip install -e /path/to/unified_hex_harvest
```

### 2. Setup Secrets

#### For Hex Notebooks:
The template automatically handles Hex secrets. Just make sure you have these secrets in your Hex project:
- `HARVEST_CREDENTIALS` - Your BigQuery service account JSON
- `ARTIFACTORY_USERNAME` - Your Artifactory username (if using private packages)
- `ARTIFACTORY_ACCESS_TOKEN` - Your Artifactory access token
- `ARTIFACTORY_URL` - Your Artifactory URL

#### For Local Development:
1. Copy `local_secrets.py` to `local_secrets_actual.py`
2. Fill in your actual credentials in `local_secrets_actual.py`
3. The file is automatically ignored by git for security

### 3. Use the Template

Copy the `hex_notebook_template.py` into a new Hex notebook and modify just the experiment parameters:

```python
# 🎯 BASIC EXPERIMENT SETTINGS - MODIFY THESE FOR YOUR EXPERIMENT
experiment_name = 'your_experiment_name_here'
start_date = '2025-01-01'
end_date = '2025-01-31'
experiment_segments = ['control_segment', 'treatment_segment']

# Run the analysis
config = create_experiment_config(
    experiment_name=experiment_name,
    start_date=start_date,
    end_date=end_date,
    experiment_segments=experiment_segments
)

analyzer = ExperimentAnalyzer(config)
analyzer.run_full_analysis()
```

That's it! You get a complete experiment analysis with all metrics, breakdowns, and visualizations.

## 📦 Library Structure

```
unified_hex_harvest/
├── core/
│   ├── config.py              # Configuration system
│   ├── experiment_analyzer.py # Main analysis engine
│   └── metrics.py             # Metric definitions
├── utils/
│   └── data_queries.py        # Data query functions
├── hex_notebook_template.py   # Simplified notebook template
└── README.md                  # This file
```

## 🔧 Configuration Options

### Basic Configuration

```python
config = create_experiment_config(
    experiment_name='my_experiment',
    start_date='2025-01-01',
    end_date='2025-01-31',
    experiment_segments=['control', 'treatment']
)
```

### Advanced Configuration

```python
config = ExperimentConfig(
    experiment_name='my_experiment',
    start_date='2025-01-01',
    end_date='2025-01-31',
    actions_end_date='2025-01-31',
    experiment_segments=['control', 'treatment'],
    
    # Analysis options
    only_free_users=True,
    include_reach_section=True,
    include_conversion_breakdowns=True,
    include_projections=True,
    
    # Metrics to analyze
    metrics_list=[
        'ConversionToSubscription',
        'ConversionToPaySubscription',
        'SubscriptionArpu',
        'Retention',
        'AutoRenewOff'
    ],
    
    # Breakdowns
    breakdowns=['Client', 'Tenure', 'User State'],
    metrics_for_breakdowns=['ConversionToSubscription', 'SubscriptionArpu']
)
```

## 📊 Available Metrics

- `ConversionToSubscription` - Conversion to any subscription
- `ConversionToPaySubscription` - Conversion to paid subscription only
- `SubscriptionArpu` - Average Revenue Per User
- `SubscriptionArps` - Average Revenue Per Subscription
- `Retention` - User retention metrics
- `AutoRenewOff` - Auto-renewal cancellation rate
- `QualifiedActivityDaily` - Daily qualified activity
- `Sessions` - User sessions
- `HoursTracked` - Hours tracked

## 🎨 Custom Analysis

You can still add custom analysis alongside the automated analysis:

```python
# Plot specific metric with custom title
analyzer.request_and_plot_metric(
    metric_name='ConversionToSubscription',
    title='Custom C2S Analysis',
    uplift_vs='control_segment'
)

# Get raw data for custom analysis
conversion_data = analyzer.get_conversion_breakdowns()
segmentation_data = analyzer.get_segmentation_breakdowns()

# Add your custom plots and analysis here
```

## 🔄 Maintenance & Updates

### Adding New Metrics

1. Add the metric definition in `core/metrics.py`
2. Add it to the `get_metric_by_name` method
3. Update the default metrics list in `core/config.py`

### Adding New Queries

1. Add query functions in `utils/data_queries.py`
2. Reference them in the metrics definitions

### Updating Analysis Logic

1. Modify the relevant functions in `core/experiment_analyzer.py`
2. All notebooks using the library will automatically get the updates

## 🏗️ Development

### Installing for Development

```bash
git clone <your-repo>
cd unified_hex_harvest
pip install -e .
```

### Testing Changes

1. Make your changes to the library
2. Create a test Hex notebook using the template
3. Verify the analysis works as expected

## 📝 Migration from Old Notebooks

To migrate from your existing Hex notebooks:

1. **Identify the experiment parameters** in your current notebook
2. **Copy the parameters** to the new template
3. **Test the analysis** to ensure it matches your current results
4. **Add any custom analysis** you need beyond the standard metrics

## 🤝 Team Workflow

### For New Experiments

1. Copy `hex_notebook_template.py` to a new Hex notebook
2. Modify the experiment parameters
3. Run the analysis
4. Share results

### For Library Updates

1. One person updates the library code
2. All team members get the updates automatically
3. No need to update individual notebooks

## 🔐 Secrets Management

### Hex Secrets (Recommended)

The library automatically uses Hex secrets when `setup_credentials(use_hex_secrets=True)` is called. Make sure these secrets are configured in your Hex project:

```python
# In your Hex notebook
from unified_hex_harvest import setup_credentials
setup_credentials(use_hex_secrets=True)  # Uses Hex secrets automatically
```

### Local Development

For local development, create a `local_secrets_actual.py` file:

```python
# local_secrets_actual.py (not tracked by git)
HARVEST_CREDENTIALS = """{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}"""

ARTIFACTORY_USERNAME = "your-username"
ARTIFACTORY_ACCESS_TOKEN = "your-token"
ARTIFACTORY_URL = "your-artifactory-url.com"
```

Then use:
```python
from unified_hex_harvest import setup_credentials
setup_credentials(use_hex_secrets=False)  # Uses local secrets
```

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure the library is installed correctly
2. **Query errors**: Check that experiment names and dates are correct
3. **Missing metrics**: Verify the metric name is in the available list
4. **Credentials errors**: Ensure secrets are properly configured in Hex or locally

### Getting Help

1. Check the error messages - they usually indicate the issue
2. Verify your experiment configuration
3. Test with a simple configuration first
4. Ensure secrets are properly set up

## 🎉 Benefits

- ✅ **No more copy-paste**: One library, many notebooks
- ✅ **Easy maintenance**: Update once, benefit everywhere
- ✅ **Consistent analysis**: Same methodology across all experiments
- ✅ **Simple configuration**: Just specify experiment parameters
- ✅ **Extensible**: Easy to add new metrics and features
- ✅ **Team collaboration**: Everyone uses the same analysis framework

## 📈 Future Enhancements

Potential future improvements:
- Automated statistical significance testing
- A/B test power analysis
- Automated report generation
- Integration with experiment tracking systems
- Custom visualization templates
