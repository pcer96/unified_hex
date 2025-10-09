"""
Main experiment analyzer class.
"""

import pandas as pd
import plotly.express as px
from typing import List, Optional, Dict, Any
# Note: These classes come from bsp_data_analysis.helpers which should be imported in Hex notebook
# App, StartDate, EndDate, ActionsEndDate, GranularityInDays, UserBaseBigQuery, OnTableExistence, Label
# request_multiple_metrics, plot_profiles

from .config import ExperimentConfig
from .metrics import MetricDefinitions
from ..utils.data_queries import DataQueries


class ExperimentAnalyzer:
    """Main class for analyzing experiments."""
    
    def __init__(self, config: ExperimentConfig):
        """
        Initialize the experiment analyzer.
        
        Args:
            config: Experiment configuration
        """
        self.config = config
        self.data_queries = DataQueries()
        self.metrics = MetricDefinitions(config.start_date, config.end_date)
        
        # Build common parameters (will be created when needed)
        self.common_params = None
        
        # Build segments parameters (will be created when needed)
        self.segments_params_all = None
        self.segments_params_noft = None
    
    def _build_common_params(self):
        """Build common parameters when needed."""
        if self.common_params is None:
            # Dynamically get App, StartDate, etc. from global namespace
            import sys
            frame = sys._getframe(2) # Go up 2 levels to get to the caller
            while frame:
                if 'App' in frame.f_globals:
                    App = frame.f_globals['App']
                    StartDate = frame.f_globals['StartDate']
                    EndDate = frame.f_globals['EndDate']
                    ActionsEndDate = frame.f_globals['ActionsEndDate']
                    GranularityInDays = frame.f_globals['GranularityInDays']
                    break
                frame = frame.f_back
            else:
                raise NameError("Required bsp_data_analysis.helpers classes (App, StartDate, EndDate, ActionsEndDate, GranularityInDays) not found in global namespace. Make sure to import them in your Hex notebook with: from bsp_data_analysis.helpers import *")
            
            self.common_params = [
                App("HarvestWeb"),
                StartDate(self.config.start_date),
                EndDate(self.config.end_date),
                ActionsEndDate(self.config.actions_end_date),
                GranularityInDays(self.config.granularity_in_days),
            ]
        return self.common_params
    
    def _build_segments_params(self):
        """Build segments parameters when needed."""
        if self.segments_params_all is None or self.segments_params_noft is None:
            # Dynamically get UserBaseBigQuery, OnTableExistence, Label from global namespace
            import sys
            frame = sys._getframe(2) # Go up 2 levels to get to the caller
            while frame:
                if 'UserBaseBigQuery' in frame.f_globals:
                    UserBaseBigQuery = frame.f_globals['UserBaseBigQuery']
                    OnTableExistence = frame.f_globals['OnTableExistence']
                    Label = frame.f_globals['Label']
                    break
                frame = frame.f_back
            else:
                raise NameError("Required bsp_data_analysis.helpers classes (UserBaseBigQuery, OnTableExistence, Label) not found in global namespace. Make sure to import them in your Hex notebook with: from bsp_data_analysis.helpers import *")
            
            custom_user_base_common_params = {
                "experiment_name": self.config.experiment_name,
                "start_date": self.config.start_date,
                "end_date": self.config.end_date
            }
            
            # Segments with all users
            self.segments_params_all = [
                [
                    UserBaseBigQuery(
                        self.data_queries.get_experiment_user_base(
                            **custom_user_base_common_params,
                            segment_name=segment
                        ).to_sql(),
                        OnTableExistence.KEEP,
                    ),
                    Label(segment)
                ]
                for segment in self.config.experiment_segments
            ]
            
            # Segments excluding converted users
            self.segments_params_noft = [
                [
                    UserBaseBigQuery(
                        self.data_queries.get_experiment_user_base(
                            **custom_user_base_common_params,
                            segment_name=segment,
                            exclude_converted=True
                        ).to_sql(),
                        OnTableExistence.KEEP,
                    ),
                    Label(segment)
                ]
                for segment in self.config.experiment_segments
            ]
    
    def request_and_plot_metric(
        self,
        metric_name: str,
        title: Optional[str] = None,
        additional_figure_params: Optional[Dict[str, Any]] = None,
        uplift_vs: Optional[str] = None,
        exclude_converted: bool = False
    ):
        """
        Request and plot a metric.
        
        Args:
            metric_name: Name of the metric to plot
            title: Custom title for the plot
            additional_figure_params: Additional parameters for the figure
            uplift_vs: Segment to compute uplift against
            exclude_converted: Whether to exclude converted users
        """
        metric = self.metrics.get_metric_by_name(metric_name)
        
        # Build segments params if needed
        self._build_segments_params()
        
        # Use appropriate segments params
        segments_params = self.segments_params_noft if exclude_converted else self.segments_params_all
        
        # Build default title
        default_title = f"<b>{metric.name}</b><br>StartDate={self.config.start_date} EndDate={self.config.end_date} ActionsEndDate={self.config.actions_end_date}"
        title = default_title if title is None else title
        
        # Dynamically get request_multiple_metrics from global namespace
        import sys
        frame = sys._getframe(1) # Go up 1 level to get to the caller
        while frame:
            if 'request_multiple_metrics' in frame.f_globals:
                request_multiple_metrics = frame.f_globals['request_multiple_metrics']
                break
            frame = frame.f_back
        else:
            raise NameError("Required bsp_data_analysis.helpers function (request_multiple_metrics) not found in global namespace. Make sure to import it in your Hex notebook with: from bsp_data_analysis.helpers import *")
        
        # Request metrics
        results = request_multiple_metrics(
            common_params=self._build_common_params() + metric.metric,
            segments_params=segments_params,
        )
        
        # Create plot using matplotlib instead of plotly to avoid compatibility issues
        import matplotlib.pyplot as plt
        import pandas as pd
        
        plt.figure(figsize=(12, 6))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, segment in enumerate(self.config.experiment_segments):
            if i < len(results):
                result = results[i]
                df = pd.DataFrame(result.profile)
                plt.plot(df['time_bin'], df['value'], 
                        marker='o', linewidth=2, label=segment, color=colors[i % len(colors)])
        
        plt.title(title.replace('<b>', '').replace('</b>', '').replace('<br>', '\n'), fontsize=14, fontweight='bold')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.legend(title='Segment')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        # Handle uplift calculation
        if uplift_vs:
            self._plot_uplift(results, uplift_vs, metric.name)
    
    def _plot_uplift(self, results: List, uplift_vs: str, metric_name: str):
        """Plot uplift against a baseline segment."""
        import matplotlib.pyplot as plt
        import pandas as pd
        
        df = pd.DataFrame(results[self.config.experiment_segments.index(uplift_vs)].profile)
        cols = ['time_bin']
        
        for segment in self.config.experiment_segments:
            if segment != uplift_vs:
                df0 = pd.DataFrame(results[self.config.experiment_segments.index(segment)].profile)
                df = df.merge(df0, on='time_bin', suffixes=['', '_' + segment])
                df[segment + '_uplift_vs_' + uplift_vs] = (
                    (df['value_' + segment] - df['value']) / (df['value'])
                )
                cols.append(segment + '_uplift_vs_' + uplift_vs)
        
        plt.figure(figsize=(12, 6))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, col in enumerate(cols[1:]):  # Skip time_bin column
            plt.scatter(df['time_bin'], df[col], 
                       label=col.replace('_uplift_vs_' + uplift_vs, ''), 
                       color=colors[i % len(colors)], s=50)
        
        plt.title(f'Uplift vs {uplift_vs}', fontsize=14, fontweight='bold')
        plt.xlabel('Days')
        plt.ylabel('Uplift')
        plt.legend(title='Segment')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        plt.tight_layout()
        plt.show()
    
    def analyze_all_metrics(self, exclude_converted: bool = False):
        """Analyze all configured metrics."""
        for metric_name in self.config.metrics_list:
            print(f"Analyzing {metric_name}...")
            self.request_and_plot_metric(metric_name, exclude_converted=exclude_converted)
    
    def analyze_specific_metrics(self, metric_names: List[str], exclude_converted: bool = False):
        """
        Analyze specific metrics.
        
        Args:
            metric_names: List of metric names to analyze
            exclude_converted: Whether to exclude converted users
        """
        for metric_name in metric_names:
            if metric_name in self.config.metrics_list:
                print(f"Analyzing {metric_name}...")
                self.request_and_plot_metric(metric_name, exclude_converted=exclude_converted)
            else:
                print(f"⚠️  Metric '{metric_name}' not found in available metrics: {self.config.metrics_list}")
    
    def analyze_single_metric(self, metric_name: str, title: Optional[str] = None, 
                            uplift_vs: Optional[str] = None, exclude_converted: bool = False):
        """
        Analyze a single metric with custom options.
        
        Args:
            metric_name: Name of the metric to analyze
            title: Custom title for the plot
            uplift_vs: Segment to compute uplift against
            exclude_converted: Whether to exclude converted users
        """
        print(f"Analyzing {metric_name}...")
        self.request_and_plot_metric(metric_name, title=title, uplift_vs=uplift_vs, 
                                   exclude_converted=exclude_converted)
    
    def get_segmentation_breakdowns(self):
        """Get segmentation breakdowns - copied exactly from original notebook."""
        # Get Query class
        Query = self.data_queries._get_query()
        
        # Build segmented_users exactly like original notebook
        segmented_users = (
            Query()
            .select(
                ("JSON_EXTRACT_SCALAR(identifiers, '$.harvest_account_id')", "uid"),
                ('MIN(event_timestamp)', 'origin_timestamp'),
                ("MIN_BY( JSON_VALUE(payload, '$.bsp_id'), event_timestamp)", "segmentation_client"),
                ("MIN_BY(JSON_VALUE(payload, '$.segment_name'), event_timestamp)", "segment_name")
            )
            .from_('`harvest-picox-42.harvest_orion.service_improvement`')
            .where(f"JSON_VALUE(payload, '$.experiment_name') = '{self.config.experiment_name}' ")
            .group_by('1')
        )

        if self.config.start_date:
            segmented_users.where(f'DATE(event_timestamp) >= "{self.config.start_date}"')
        if self.config.end_date:
            segmented_users.where(f'DATE(event_timestamp) <= "{self.config.end_date}"')

        # Build userbase exactly like original notebook
        userbase = (
            Query()
            .select(" seg.uid,seg.origin_timestamp,seg.segmentation_client,seg.segment_name")
            .from_(segmented_users, alias='seg')
        )

        # Copy exact segmentation_by_client from original notebook
        segmentation_by_client = (
            Query()
            .select(
                ('TIMESTAMP_TRUNC(origin_timestamp, HOUR)', 'time'),
                ('''
                    CASE 
                        WHEN segmentation_client = "harvest_ios" THEN "ios"
                        WHEN segmentation_client = "harvest_android" THEN "android"
                        WHEN segmentation_client = "harvest_web" THEN "web"
                        WHEN segmentation_client IN ("harvest_mac_store", "harvest_windows_store") THEN "desktop"
                    END
                    ''',
                    'segmentation_client'
                ),
                ('COUNT(DISTINCT uid)', 'users'),
            )
            .from_(segmented_users)
            .group_by('1,2')
        )

        # Copy exact segmentation_by_segment from original notebook
        segmentation_by_segment = (
            Query()
            .select(
                'segment_name',
                ('COUNT(DISTINCT uid)', 'users'),
            )
            .from_(segmented_users)
            .group_by('1')
        )
        
        return segmentation_by_client, segmentation_by_segment
    
    def plot_segmentation_breakdowns(self):
        """Plot segmentation breakdowns."""
        segmentation_by_client, segmentation_by_segment = self.get_segmentation_breakdowns()
        
        # Plot by client
        import pandas_gbq
        df_seg_client = pandas_gbq.read_gbq(segmentation_by_client.to_sql())
        df = df_seg_client.copy().sort_values('time')
        df['users_cumulative'] = df.groupby('segmentation_client')['users'].transform('cumsum')
        
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        
        for client in df['segmentation_client'].unique():
            client_data = df[df['segmentation_client'] == client]
            plt.plot(client_data['time'], client_data['users_cumulative'], 
                    marker='o', linewidth=2, label=client)
        
        plt.title('Segmented Users - Breakdown by Client', fontsize=14, fontweight='bold')
        plt.xlabel('Time')
        plt.ylabel('Cumulative Users')
        plt.legend(title='Client')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        
        # Plot by segment
        df_seg_segment = pandas_gbq.read_gbq(segmentation_by_segment.to_sql())
        df = df_seg_segment.copy()
        
        plt.figure(figsize=(10, 6))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        bars = plt.bar(df['segment_name'], df['users'], color=colors[:len(df)])
        
        plt.title('Segmented Users - Breakdown by Segment', fontsize=14, fontweight='bold')
        plt.xlabel('Segment')
        plt.ylabel('Users')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
    
    def get_conversion_breakdowns(self):
        """Get conversion breakdowns if enabled."""
        if not self.config.include_conversion_breakdowns:
            return pd.DataFrame(columns=['segment_name', 'global_user_id', 'offer_group', 'plan', 'periodicity', 'net_revenues_usd'])
        
        conversion_breakdown_query = f"""
        WITH
      first_segmentation AS (
      SELECT
        JSON_EXTRACT_SCALAR(identifiers, '$.harvest_account_id') AS uid,
        MIN(event_timestamp) AS timestamp,
        MIN_BY( JSON_VALUE(payload, '$.bsp_id'), event_timestamp) AS segmentation_client,
        MIN_BY(JSON_VALUE(payload, '$.segment_name'), event_timestamp) AS segment_name
      FROM
        `harvest-picox-42.harvest_orion.service_improvement`
      WHERE
        JSON_VALUE(payload, '$.experiment_name') = '{self.config.experiment_name}'
        AND DATE(event_timestamp) >= '{self.config.start_date}'
        AND DATE(event_timestamp) <= '{self.config.end_date}'
      GROUP BY
        1 ),
      conversions AS (
      SELECT
        user_id uid,
        segment_name, segmentation_client client,
        event_type,
        p.timestamp purchase_timestamp,
        bookings_net_of_platform_fees_usd,
        JSON_EXTRACT_SCALAR(product_info, '$.periodicity') product_periodicity,
        SAFE_CAST(REGEXP_EXTRACT(JSON_VALUE(product_info, '$.product_description'), r'^\\s*(\\d+)') AS INT64) seat_number
      FROM
        `harvest-lumenx-42.verified.bookings` p
      INNER JOIN first_segmentation s ON s.uid = p.user_id
      
      WHERE
       p.timestamp >= s.timestamp
       and 
        event_type in ('purchase', 'free_trial')
        AND ( JSON_EXTRACT_SCALAR(event_info, '$.is_mid_subscription_expansion') IS NULL
          OR JSON_EXTRACT_SCALAR(event_info, '$.is_mid_subscription_expansion') = "false")
        AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') <> "Subscription update"
          OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
        AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') NOT LIKE "%Additional%"
          OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
        AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') NOT LIKE "%adjustment%"
          OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
        AND (ARRAY_LENGTH(JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids')) = 0
          OR JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids') IS NULL
          OR JSON_VALUE(JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids')[
          OFFSET
            (0)]) = 'additional_user')
            
             )

            SELECT
        conversions.uid,
        conversions.segment_name,
        conversions.client,
        conversions.event_type,
        conversions.purchase_timestamp,
        conversions.product_periodicity,
        conversions.bookings_net_of_platform_fees_usd,
        conversions.product_periodicity,
        FROM conversions
        """
        
        import pandas_gbq
        return pandas_gbq.read_gbq(conversion_breakdown_query)
    
    def run_full_analysis(self, metrics_to_analyze: Optional[List[str]] = None):
        """
        Run the complete experiment analysis.
        
        Args:
            metrics_to_analyze: Optional list of specific metrics to analyze. 
                               If None, analyzes all configured metrics.
        """
        print(f"Starting analysis for experiment: {self.config.experiment_name}")
        print(f"Date range: {self.config.start_date} to {self.config.end_date}")
        print(f"Segments: {', '.join(self.config.experiment_segments)}")
        print("-" * 50)
        
        # Plot segmentation breakdowns
        if self.config.include_reach_section:
            print("Plotting segmentation breakdowns...")
            self.plot_segmentation_breakdowns()
        
        # Analyze metrics
        if metrics_to_analyze:
            print(f"Analyzing specific metrics: {', '.join(metrics_to_analyze)}")
            self.analyze_specific_metrics(metrics_to_analyze)
        else:
            print("Analyzing all configured metrics...")
            self.analyze_all_metrics()
        
        # Get conversion breakdowns
        if self.config.include_conversion_breakdowns:
            print("Getting conversion breakdowns...")
            conversion_breakdown_df = self.get_conversion_breakdowns()
            print(f"Conversion breakdown data shape: {conversion_breakdown_df.shape}")
        
        print("Analysis complete!")
