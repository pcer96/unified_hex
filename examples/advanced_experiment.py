"""
Example: Advanced Experiment Analysis

This example shows how to configure a complex experiment with custom settings.
"""

from unified_hex_harvest import ExperimentAnalyzer, ExperimentConfig

# Advanced experiment configuration
config = ExperimentConfig(
    experiment_name='advanced_growth_experiment',
    start_date='2025-01-01',
    end_date='2025-01-31',
    actions_end_date='2025-01-31',
    experiment_segments=['control_segment', 'intro_upsell', 'premium_upsell'],
    
    # Analysis options
    only_free_users=True,  # Only analyze free users
    include_reach_section=True,
    include_conversion_breakdowns=True,
    include_conversions_at_target_paywall_profiles=True,
    include_engagement_model=True,
    include_projections=True,
    
    # Custom metrics
    metrics_list=[
        'ConversionToSubscription',
        'ConversionToPaySubscription',
        'SubscriptionArpu',
        'SubscriptionArps',
        'Retention',
        'AutoRenewOff',
        'QualifiedActivityDaily',
        'Sessions'
    ],
    
    # Breakdowns
    breakdowns=['Client', 'Tenure', 'User State'],
    metrics_for_breakdowns=[
        'ConversionToSubscription',
        'ConversionToPaySubscription',
        'SubscriptionArpu',
        'Retention',
        'AutoRenewOff'
    ],
    
    # Engagement model settings
    action_engagement_model='task - create-task',
    action_engagement_model_2='task - create-task',
    
    # Target paywall settings
    target_paywall_display_event='action_kind = "delta_on_session_paywall_shown"',
    target_paywall_conversion_event='offer_group = "Back To School 2024"'
)

# Initialize analyzer
analyzer = ExperimentAnalyzer(config)

# Run full analysis
print("Running advanced experiment analysis...")
analyzer.run_full_analysis()

# Additional custom analysis
print("\nRunning custom uplift analysis...")
analyzer.request_and_plot_metric(
    metric_name='ConversionToSubscription',
    title='C2S with Uplift Analysis',
    uplift_vs='control_segment'
)

# Get conversion breakdown data for further analysis
conversion_data = analyzer.get_conversion_breakdowns()
print(f"\nConversion breakdown data: {conversion_data.shape[0]} rows")
print(conversion_data.head())
