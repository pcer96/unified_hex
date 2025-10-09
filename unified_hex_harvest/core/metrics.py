"""
Metric definitions for experiment analysis.
"""

from collections import namedtuple
from typing import List, Dict, Any
# Note: These classes come from bsp_data_analysis.helpers which should be imported in Hex notebook
# CustomFirstSuccessRateMetric, CustomValuedMetric, CustomCountMetric
from ..utils.data_queries import DataQueries

Metric = namedtuple('Metric', ['name', 'metric'])


class MetricDefinitions:
    """Collection of metric definitions for experiment analysis."""
    
    def __init__(self, start_date: str, end_date: str):
        """
        Initialize metric definitions.
        
        Args:
            start_date: Start date for the experiment
            end_date: End date for the experiment
        """
        self.start_date = start_date
        self.end_date = end_date
        self._data_queries = DataQueries()
    
    def _get_bsp_class(self, class_name: str):
        """Get bsp_data_analysis class from global namespace."""
        import sys
        frame = sys._getframe(2)  # Go up 2 levels to get to the caller
        while frame:
            if class_name in frame.f_globals:
                return frame.f_globals[class_name]
            frame = frame.f_back
        else:
            raise NameError(f"{class_name} not found in global namespace. Make sure to import it in your Hex notebook with: from bsp_data_analysis.helpers import *")
    
    def get_conversion_to_subscription(self) -> Metric:
        """Get conversion to subscription metric."""
        CustomFirstSuccessRateMetric = self._get_bsp_class('CustomFirstSuccessRateMetric')
        
        return Metric(
            name='C2S',
            metric=[CustomFirstSuccessRateMetric(
                target_query=self._data_queries.get_conversions(self.start_date, self.end_date), 
                estimator='cumulated'
            )]
        )
    
    def get_conversion_to_pay_subscription(self) -> Metric:
        """Get conversion to paid subscription metric."""
        CustomFirstSuccessRateMetric = self._get_bsp_class('CustomFirstSuccessRateMetric')
        
        return Metric(
            name='C2P',
            metric=[CustomFirstSuccessRateMetric(
                target_query=self._data_queries.get_conversions(self.start_date, self.end_date, only_paid=True), 
                estimator='cumulated'
            )]
        )
    
    def get_subscription_arpu(self) -> Metric:
        """Get subscription ARPU metric."""
        CustomValuedMetric = self._get_bsp_class('CustomValuedMetric')
        
        return Metric(
            name='ARPU',
            metric=[CustomValuedMetric(
                target_query=self._data_queries.get_conversions(self.start_date, self.end_date, only_paid=False), 
                estimator='cumulated'
            )]
        )
    
    def get_subscription_arps(self) -> Metric:
        """Get subscription ARPS metric."""
        CustomValuedMetric = self._get_bsp_class('CustomValuedMetric')
        
        return Metric(
            name='ARPS',
            metric=[CustomValuedMetric(
                target_query=self._data_queries.get_conversions(self.start_date, self.end_date, only_paid=True), 
                estimator='cumulated'
            )]
        )
    
    def get_auto_renew_off(self) -> Metric:
        """Get auto-renew off metric."""
        CustomFirstSuccessRateMetric = self._get_bsp_class('CustomFirstSuccessRateMetric')
        
        return Metric(
            name='AutoRenewOff',
            metric=[CustomFirstSuccessRateMetric(
                target_query=self._data_queries.get_aro(self.start_date, self.end_date), 
                estimator='cumulated'
            )]
        )
    
    def get_qualified_activity_daily(self) -> Metric:
        """Get qualified activity daily metric."""
        CustomCountMetric = self._get_bsp_class('CustomCountMetric')
        
        return Metric(
            name='QualifiedActivityDaily',
            metric=[CustomCountMetric(
                cumulative=True,
                target_query=self._data_queries.get_activity_rate_qualified(self.start_date, self.end_date), 
                estimator='cumulated'
            )]
        )
    
    def get_sessions(self) -> Metric:
        """Get sessions metric."""
        CustomCountMetric = self._get_bsp_class('CustomCountMetric')
        
        return Metric(
            name='Sessions',
            metric=[CustomCountMetric(
                cumulative=True,
                target_query=self._data_queries.get_sessions(self.start_date, self.end_date), 
                estimator='cumulated'
            )]
        )
    
    def get_tracked_hours(self) -> Metric:
        """Get tracked hours metric."""
        CustomValuedMetric = self._get_bsp_class('CustomValuedMetric')
        
        return Metric(
            name='HoursTracked',
            metric=[CustomValuedMetric(
                cumulative=True,
                target_query=self._data_queries.get_time_entries(self.start_date, self.end_date), 
                estimator='cumulated'
            )]
        )
    
    def get_retention(self) -> Metric:
        """Get retention metric (placeholder - implement based on your retention logic)."""
        # This is a placeholder - you'll need to implement your retention logic
        CustomCountMetric = self._get_bsp_class('CustomCountMetric')
        
        return Metric(
            name='Retention',
            metric=[CustomCountMetric(
                cumulative=True,
                target_query=self._data_queries.get_sessions(self.start_date, self.end_date), 
                estimator='cumulated'
            )]
        )
    
    def get_metric_by_name(self, metric_name: str) -> Metric:
        """
        Get a metric by its name.
        
        Args:
            metric_name: Name of the metric to retrieve
            
        Returns:
            Metric object
            
        Raises:
            ValueError: If metric name is not recognized
        """
        metric_map = {
            'ConversionToSubscription': self.get_conversion_to_subscription,
            'ConversionToPaySubscription': self.get_conversion_to_pay_subscription,
            'SubscriptionArpu': self.get_subscription_arpu,
            'SubscriptionArps': self.get_subscription_arps,
            'Retention': self.get_retention,
            'AutoRenewOff': self.get_auto_renew_off,
            'QualifiedActivityDaily': self.get_qualified_activity_daily,
            'Sessions': self.get_sessions,
            'HoursTracked': self.get_tracked_hours,
        }
        
        if metric_name not in metric_map:
            raise ValueError(f"Unknown metric: {metric_name}. Available metrics: {list(metric_map.keys())}")
        
        return metric_map[metric_name]()
    
    def get_metrics_list(self, metric_names: List[str]) -> List[Metric]:
        """
        Get a list of metrics by their names.
        
        Args:
            metric_names: List of metric names to retrieve
            
        Returns:
            List of Metric objects
        """
        return [self.get_metric_by_name(name) for name in metric_names]
