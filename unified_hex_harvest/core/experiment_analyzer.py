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
        
        # Build common parameters
        self.common_params = [
            App("HarvestWeb"),
            StartDate(config.start_date),
            EndDate(config.end_date),
            ActionsEndDate(config.actions_end_date),
            GranularityInDays(config.granularity_in_days),
        ]
        
        # Build segments parameters
        self._build_segments_params()
    
    def _build_segments_params(self):
        """Build segments parameters for the experiment."""
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
        
        # Use appropriate segments params
        segments_params = self.segments_params_noft if exclude_converted else self.segments_params_all
        
        # Build default title
        default_title = f"<b>{metric.name}</b><br>StartDate={self.config.start_date} EndDate={self.config.end_date} ActionsEndDate={self.config.actions_end_date}"
        title = default_title if title is None else title
        
        # Request metrics
        results = request_multiple_metrics(
            common_params=self.common_params + metric.metric,
            segments_params=segments_params,
        )
        
        # Create plot
        fig = plot_profiles(
            results,
            title=title,
            show=False,
            return_figure=True,
            height=500,
        )
        
        if additional_figure_params:
            fig.update_layout(**additional_figure_params)
        
        fig.update_layout(margin={"t": 80}).show()
        
        # Handle uplift calculation
        if uplift_vs:
            self._plot_uplift(results, uplift_vs, metric.name)
    
    def _plot_uplift(self, results: List, uplift_vs: str, metric_name: str):
        """Plot uplift against a baseline segment."""
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
        
        melted_df = df[cols].melt(id_vars=['time_bin'], var_name='series', value_name='values')
        
        fig = px.scatter(
            melted_df, 
            x='time_bin', 
            y='values', 
            color='series',
            title=f'<b>Uplift vs {uplift_vs}</b>',
            labels={'time_bin': 'Days', 'values': '', 'series': ''}
        )
        
        fig.update_yaxes(title=None)
        fig.update_traces(marker=dict(size=10))
        fig.update_yaxes(showgrid=True, gridcolor='lightgrey')
        fig.update_layout(plot_bgcolor='white')
        fig.add_hline(y=0, line_color="black")
        fig.show()
    
    def analyze_all_metrics(self, exclude_converted: bool = False):
        """Analyze all configured metrics."""
        for metric_name in self.config.metrics_list:
            print(f"Analyzing {metric_name}...")
            self.request_and_plot_metric(metric_name, exclude_converted=exclude_converted)
    
    def get_segmentation_breakdowns(self):
        """Get segmentation breakdowns."""
        # Get segmented users query
        segmented_users = self.data_queries.get_experiment_user_base(
            experiment_name=self.config.experiment_name,
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )
        
        # Segmentation by client
        segmentation_by_client = (
            segmented_users
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
            .group_by('1,2')
        )
        
        # Segmentation by segment
        segmentation_by_segment = (
            segmented_users
            .select(
                'segment_name',
                ('COUNT(DISTINCT uid)', 'users'),
            )
            .group_by('1')
        )
        
        return segmentation_by_client, segmentation_by_segment
    
    def plot_segmentation_breakdowns(self):
        """Plot segmentation breakdowns."""
        segmentation_by_client, segmentation_by_segment = self.get_segmentation_breakdowns()
        
        # Plot by client
        df_seg_client = pd.read_gbq(segmentation_by_client.to_sql())
        df = df_seg_client.copy().sort_values('time')
        df['users_cumulative'] = df.groupby('segmentation_client')['users'].transform('cumsum')
        
        fig = px.line(
            df,
            x='time',
            y='users_cumulative',
            color='segmentation_client',
            title='<b>Segmented Users - Breakdown by Client</b>',
            category_orders={'segmentation_client': ['ios', 'android', 'desktop', 'web']}
        )
        fig.show()
        
        # Plot by segment
        df_seg_segment = pd.read_gbq(segmentation_by_segment.to_sql())
        df = df_seg_segment.copy()
        
        fig = px.bar(
            df,
            x='segment_name',
            y='users',
            color='segment_name',
            title='<b>Segmented Users - Breakdown by Segment</b>',
        )
        fig.show()
    
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
        SAFE_CAST(REGEXP_EXTRACT(JSON_VALUE(product_info, '$.product_description'), r'^\s*(\d+)') AS INT64) seat_number
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
        
        return pd.read_gbq(conversion_breakdown_query)
    
    def run_full_analysis(self):
        """Run the complete experiment analysis."""
        print(f"Starting analysis for experiment: {self.config.experiment_name}")
        print(f"Date range: {self.config.start_date} to {self.config.end_date}")
        print(f"Segments: {', '.join(self.config.experiment_segments)}")
        print("-" * 50)
        
        # Plot segmentation breakdowns
        if self.config.include_reach_section:
            print("Plotting segmentation breakdowns...")
            self.plot_segmentation_breakdowns()
        
        # Analyze all metrics
        print("Analyzing metrics...")
        self.analyze_all_metrics()
        
        # Get conversion breakdowns
        if self.config.include_conversion_breakdowns:
            print("Getting conversion breakdowns...")
            conversion_breakdown_df = self.get_conversion_breakdowns()
            print(f"Conversion breakdown data shape: {conversion_breakdown_df.shape}")
        
        print("Analysis complete!")
