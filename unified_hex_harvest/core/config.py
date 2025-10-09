"""
Configuration system for experiment analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date


@dataclass
class ExperimentConfig:
    """Configuration for experiment analysis."""
    
    # Core experiment parameters
    experiment_name: str
    start_date: str
    end_date: str
    actions_end_date: Optional[str] = None
    experiment_segments: List[str] = field(default_factory=list)
    
    # Analysis options
    only_free_users: bool = False
    include_reach_section: bool = True
    include_conversion_breakdowns: bool = True
    include_conversions_at_target_paywall_profiles: bool = True
    include_engagement_model: bool = False
    include_projections: bool = True
    
    # Metrics to analyze
    metrics_list: List[str] = field(default_factory=lambda: [
        'ConversionToSubscription',
        'ConversionToPaySubscription', 
        'SubscriptionArpu',
        'SubscriptionArps',
        'Retention',
        'AutoRenewOff'
    ])
    
    # Breakdowns
    breakdowns: List[str] = field(default_factory=lambda: [
        'Client',
        'Tenure', 
        'User State'
    ])
    
    metrics_for_breakdowns: List[str] = field(default_factory=lambda: [
        'ConversionToSubscription',
        'ConversionToPaySubscription',
        'SubscriptionArpu', 
        'Retention',
        'AutoRenewOff'
    ])
    
    # Engagement model settings
    action_engagement_model: Optional[str] = None
    action_engagement_model_2: Optional[str] = None
    
    # Target paywall settings
    target_paywall_display_event: Optional[str] = None
    target_paywall_conversion_event: Optional[str] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.actions_end_date is None:
            self.actions_end_date = self.end_date
            
        if not self.experiment_segments:
            self.experiment_segments = ['control_segment', 'treatment_segment']
    
    @property
    def horizon_in_days(self) -> int:
        """Calculate the horizon in days."""
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.actions_end_date, '%Y-%m-%d')
        return (end - start).days
    
    @property
    def granularity_in_days(self) -> int:
        """Determine granularity based on horizon."""
        return 1 if self.horizon_in_days < 40 else 7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'experiment_name': self.experiment_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'actions_end_date': self.actions_end_date,
            'experiment_segments': self.experiment_segments,
            'only_free_users': self.only_free_users,
            'include_reach_section': self.include_reach_section,
            'include_conversion_breakdowns': self.include_conversion_breakdowns,
            'include_conversions_at_target_paywall_profiles': self.include_conversions_at_target_paywall_profiles,
            'include_engagement_model': self.include_engagement_model,
            'include_projections': self.include_projections,
            'metrics_list': self.metrics_list,
            'breakdowns': self.breakdowns,
            'metrics_for_breakdowns': self.metrics_for_breakdowns,
            'action_engagement_model': self.action_engagement_model,
            'action_engagement_model_2': self.action_engagement_model_2,
            'target_paywall_display_event': self.target_paywall_display_event,
            'target_paywall_conversion_event': self.target_paywall_conversion_event,
            'horizon_in_days': self.horizon_in_days,
            'granularity_in_days': self.granularity_in_days
        }


def create_experiment_config(
    experiment_name: str,
    start_date: str,
    end_date: str,
    experiment_segments: List[str] = None,
    **kwargs
) -> ExperimentConfig:
    """
    Create an experiment configuration with sensible defaults.
    
    Args:
        experiment_name: Name of the experiment
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        experiment_segments: List of segment names
        **kwargs: Additional configuration options
        
    Returns:
        ExperimentConfig object
    """
    if experiment_segments is None:
        experiment_segments = ['control_segment', 'treatment_segment']
    
    return ExperimentConfig(
        experiment_name=experiment_name,
        start_date=start_date,
        end_date=end_date,
        experiment_segments=experiment_segments,
        **kwargs
    )
