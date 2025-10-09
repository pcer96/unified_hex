! uv pip install -q bsp-data-analysis -i https://{ARTIFACTORY_USERNAME}:{ARTIFACTORY_ACCESS_TOKEN}@{ARTIFACTORY_URL}/api/pypi/pypi/simple
! uv pip -q install slack_sdk
! uv pip install -q kaleido

import os
from bsp_data_analysis.helpers import *
from bsp_data_analysis.helpers.standard_imports import *
from itertools import islice
from functools import reduce
from IPython.display import Markdown, display
import math
from datetime import datetime, timedelta
from bsp_query_builder.dialects.big_query.common import (Case, case_cond)

from slack_sdk import WebClient
from dataclasses import dataclass, field
import tempfile
from typing import Optional, Union, Dict, List
from scipy.stats import median_abs_deviation
from datetime import datetime

with open('credentials.json', 'w') as f:
    f.write(HARVEST_CREDENTIALS)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'credentials.json'

def get_experiment_user_base(
    experiment_name, 
    segment_name=None, 
    start_date=None, 
    end_date=None,
    exclude_converted = None):

    segmented_users = (
        Query()
        .select(
            ("JSON_EXTRACT_SCALAR(identifiers, '$.harvest_account_id')", "uid"),
            ('MIN(event_timestamp)', 'origin_timestamp'),
            ("MIN_BY( JSON_VALUE(payload, '$.bsp_id'), event_timestamp)", "segmentation_client"),
            ("MIN_BY(JSON_VALUE(payload, '$.segment_name'), event_timestamp)", "segment_name")
        )
        .from_('`harvest-picox-42.harvest_orion.service_improvement`')
        .where(f"JSON_VALUE(payload, '$.experiment_name') = '{experiment_name}' ")
        .group_by('1')
    )

    if segment_name:
        if isinstance(segment_name, str):
            segment_name = [segment_name]
        segments_in_list = '("' + '", "'.join(segment_name) + '")'
        segmented_users.where(f"JSON_VALUE(payload, '$.segment_name') IN {segments_in_list}")
    if start_date:
        segmented_users.where(f'DATE(event_timestamp) >= "{start_date}"')
    if end_date:
        segmented_users.where(f'DATE(event_timestamp) <= "{end_date}"')

    userbase= (
        Query()
        .select(" seg.uid,seg.origin_timestamp,seg.segmentation_client,seg.segment_name")
        .from_(segmented_users, alias = 'seg')
    )

    if exclude_converted:
        transactions = (
            Query()
            .select(
                ('user_id', 'uid'),('timestamp','event_timestamp'),('subscription_id'),('subscription_manager'),('product_info'),('event_info'), ('bookings_net_of_platform_fees_usd', 'event_value'),
                ("JSON_EXTRACT_SCALAR(product_info, '$.periodicity')", 'product_periodicity' ),
                ("SAFE_CAST(REGEXP_EXTRACT(JSON_VALUE(product_info, '$.product_description'), r'^\s*(\d+)') AS INT64)", 'seat_number'),
                ('event_type')
            )
            .from_(" `harvest-lumenx-42.verified.bookings` ")
            .where('''event_type IN ('purchase' , 'free_trial') 
            AND ( JSON_EXTRACT_SCALAR(event_info, '$.is_mid_subscription_expansion') IS NULL OR JSON_EXTRACT_SCALAR(event_info, '$.is_mid_subscription_expansion') = "false") 
            AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') <> "Subscription update" OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
            AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') NOT LIKE "%Additional%" OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
            AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') NOT LIKE "%adjustment%" OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
            AND (ARRAY_LENGTH(JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids')) = 0 OR JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids') IS NULL OR JSON_VALUE(JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids')[OFFSET(0)]) = 'additional_user')
        ''')

        )

        final = (
            Query()
            .select(
                ('uid'),
                ('MIN(event_timestamp) as event_timestamp'),
            )
            .from_(transactions)
            .group_by(1)
        )

        userbase.join(final, alias = 'final', using = 'uid', join_type='left').where('final.uid is null')



    return userbase

def get_time_entries(start_date, end_date):
    return f'''
      with time_entries AS (
    SELECT
      timestamp(DATE(created_at)) AS event_timestamp,
      cast(company_id as string) uid,
      sum(hours) as event_value 
    FROM `harvesthq-production.harvest_analytics.time_entries`
    WHERE created_at between '{start_date}' and '{end_date}'
    GROUP BY 1, 2
  )
  select uid, event_timestamp, event_value
  from time_entries '''

  def get_sessions(start_date=None, end_date='2030-01-01'):
    return f'''with sessions as (
  SELECT
    DISTINCT (session_start_time) AS event_timestamp,
    cast(user_id as string) uid
  FROM
    `harvesthq-production.harvest_analytics.sessions`
  WHERE
    session_start_time between '{start_date}' and '{end_date}' )
    select uid,  event_timestamp
    from  sessions'''

    def get_activity_rate_qualified(
    start_date=None, 
    end_date='2030-01-01'):


    return f'''WITH
  active_users_daily AS (
  SELECT
    dates.date AS event_date,
    users.user_id,
    users.company_id
  FROM
    `harvesthq-production.harvest_analytics.reporting_dates` AS dates
  CROSS JOIN
    `harvesthq-production.harvest_analytics.users` AS users
  INNER JOIN
    `harvesthq-production.harvest_analytics.customers` AS customers
  ON
    users.company_id = customers.company_id
  WHERE
    dates.date between '{start_date}' and '{end_date}'
    AND dates.date < CURRENT_DATE()
    AND DATE(users.created_at) < dates.date
    AND (users.is_active = 1
      OR DATE(users.deactivated_at) > dates.date)
    AND DATE(customers.converted_at) < dates.date
    AND (customers.churned = 0
      OR DATE(customers.churn_date) > dates.date) ),
  team_size_daily AS (
  SELECT
    as_of_date AS event_date,
    company_id,
    MAX(seats) AS seats
  FROM
    `harvesthq-production.harvest_analytics.income_days`
  WHERE
    as_of_date between '{start_date}' and '{end_date}'
  GROUP BY
    1,
    2 ),
  time_entries AS (
  SELECT
    DATE(created_at) AS event_date,
    user_id,
    MAX(CASE
        WHEN platform_group = 'web' THEN 1
        ELSE 0
    END
      ) AS tracked_via_web,
    MAX(CASE
        WHEN platform_group = 'native_mobile' THEN 1
        ELSE 0
    END
      ) AS tracked_via_mobile,
    MAX(CASE
        WHEN platform_group = 'native_desktop' THEN 1
        ELSE 0
    END
      ) AS tracked_via_desktop,
    MAX(CASE
        WHEN platform = 'windows app' THEN 1
        ELSE 0
    END
      ) AS tracked_via_desktop_windows,
    MAX(CASE
        WHEN platform = 'mac app' THEN 1
        ELSE 0
    END
      ) AS tracked_via_desktop_mac,
    MAX(CASE
        WHEN platform_group = 'native_mobile' AND platform LIKE '%ios%' THEN 1
        ELSE 0
    END
      ) AS tracked_via_mobile_ios,
    MAX(CASE
        WHEN platform_group = 'native_mobile' AND platform LIKE '%android%' THEN 1
        ELSE 0
    END
      ) AS tracked_via_mobile_android,
    MAX(CASE
        WHEN platform_group IN ('browser_extension', 'integration') THEN 1
        ELSE 0
    END
      ) AS tracked_via_integration
  FROM
    `harvesthq-production.harvest_analytics.time_entries`
  WHERE
    created_at between '{start_date}' and '{end_date}'
  GROUP BY
    1,
    2 ),
  expenses AS (
  SELECT
    DISTINCT DATE(created_at) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.expenses`
  WHERE
    created_at between '{start_date}' and '{end_date}' ),
  invoices AS (
  SELECT
    DISTINCT DATE(invoice_created_at) AS event_date,
    invoice_creator_user_id AS user_id
  FROM
    `harvesthq-production.harvest_analytics.invoices`
  WHERE
    invoice_created_at between '{start_date}' and '{end_date}' ),
  submitted_timesheets AS (
  SELECT
    DISTINCT DATE(created_at) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.stg_harvest__approval_units`
  WHERE
    created_at between '{start_date}' and '{end_date}' ),
  approved_timesheets AS (
  SELECT
    DISTINCT DATE(event_time) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.events`
  WHERE
    event_time  between '{start_date}' and '{end_date}'
    AND clicked_element_id = 'approval-pending-approve-confirm' ),
  estimates AS (
  SELECT
    DISTINCT DATE(created_at) AS event_date,
    created_by_id AS user_id
  FROM
    `harvesthq-production.harvestapp_replicated_vitess.estimates`
  WHERE
    created_at  between '{start_date}' and '{end_date}' ),
  projects_created AS (
  SELECT
    DISTINCT DATE(created_at) AS event_date,
    creator_user_id AS user_id
  FROM
    `harvesthq-production.harvest_analytics.projects`
  WHERE
    created_at between '{start_date}' and '{end_date}' ),
  users_created AS (
  SELECT
    DISTINCT DATE(created_at) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.users`
  WHERE
    created_at between '{start_date}' and '{end_date}' ),
  page_views AS (
  SELECT
    DATE(event_time) AS event_date,
    user_id,
    MAX(CASE
        WHEN page_id = '/team_members' THEN 1
        ELSE 0
    END
      ) AS viewed_team_page,
    MAX(CASE
        WHEN page_id = '/projects/index/active' THEN 1
        ELSE 0
    END
      ) AS viewed_projects_page,
    MAX(CASE
        WHEN page_id = '/contractor_report' THEN 1
        ELSE 0
    END
      ) AS viewed_contractor_report,
    MAX(CASE
        WHEN page_id = '/reports/time' THEN 1
        ELSE 0
    END
      ) AS viewed_summary_time_report,
    MAX(CASE
        WHEN page_id = '/reports/uninvoiced' THEN 1
        ELSE 0
    END
      ) AS viewed_uninvoiced_report,
    MAX(CASE
        WHEN page_id = '/invoices/archive' THEN 1
        ELSE 0
    END
      ) AS viewed_invoice_report,
    MAX(CASE
        WHEN page_id = '/activity' THEN 1
        ELSE 0
    END
      ) AS viewed_activity_report,
    MAX(CASE
        WHEN page_id = '/profitability_reports' THEN 1
        ELSE 0
    END
      ) AS viewed_profitability_report,
    MAX(CASE
        WHEN page_id = '/saved_reports' THEN 1
        ELSE 0
    END
      ) AS viewed_saved_report,
    MAX(CASE
        WHEN page_id = '/team_members/show' THEN 1
        ELSE 0
    END
      ) AS viewed_team_detail_report,
    MAX(CASE
        WHEN page_id = '/projects/show' THEN 1
        ELSE 0
    END
      ) AS viewed_project_detail_report,
    MAX(CASE
        WHEN page_id = '/invoices' THEN 1
        ELSE 0
    END
      ) AS viewed_invoices_page,
    MAX(CASE
        WHEN page_id LIKE '/reports/detailed/%' AND page_id != '/reports/detailed/filter' THEN 1
        ELSE 0
    END
      ) AS viewed_detailed_time_report,
    MAX(CASE
        WHEN page_id LIKE '/reports/expenses/%' THEN 1
        ELSE 0
    END
      ) AS viewed_detailed_expenses_report,
    MAX(CASE
        WHEN page_id LIKE '/approve%' OR page_id = '/missing_time' THEN 1
        ELSE 0
    END
      ) AS viewed_approvals_page
  FROM
    `harvesthq-production.harvest_analytics.events`
  WHERE
    event_time between '{start_date}' and '{end_date}'
    AND event_type = 'page_view'
  GROUP BY
    1,
    2 ),
  project_events AS (
  SELECT
    DISTINCT DATE(event_time) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.events`
  WHERE
    event_time between '{start_date}' and '{end_date}'
    AND (page_id IN ('/projects/show',
        '/projects/edit')
      OR clicked_element_id IN ('project-actions-edit',
        'project-actions-archive',
        'project-actions-duplicate',
        'project-actions-delete-confirm',
        'project-actions-restore',
        'project-bulk-archive-confirm',
        'project-actions-pin',
        'project-actions-unpin',
        'project-bulk-delete-confirm',
        'projects-filter-by-client-select',
        'projects-filter-archived',
        'projects-filter-active',
        'projects-filter-by-manager-select',
        'projects-clear-filters',
        'projects-filter-budgeted',
        'projects-export-confirm',
        'projects-import-confirm')) ),
  team_events AS (
  SELECT
    DISTINCT DATE(event_time) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.events`
  WHERE
    event_time between '{start_date}' and '{end_date}'
    AND (page_id = '/team_members/show'
      OR (page_id LIKE '/people%'
        AND page_id NOT IN ('/people/new',
          '/people/create'))
      OR clicked_element_id IN ('team-filter-select',
        'team-navigate-previous-week',
        'team-navigate-next-week',
        'team-navigate-return-to-this-week',
        'team-member-actions-edit',
        'team-member-actions-archive',
        'team-manage-archived-people',
        'team-member-actions-pin',
        'team-member-actions-unpin',
        'team-member-delete-confirm',
        'team-export-confirm',
        'team-import-success-close')) ),
  mobile_events AS (
  SELECT
    DATE(event_time) AS event_date,
    user_id,
    MAX(CASE
        WHEN device_operating_system = 'ios' THEN 1
        ELSE 0
    END
      ) AS mobile_ios_engaged,
    MAX(CASE
        WHEN device_operating_system = 'android' THEN 1
        ELSE 0
    END
      ) AS mobile_android_engaged
  FROM
    `harvesthq-production.harvest_analytics.events`
  WHERE
    event_time between '{start_date}' and '{end_date}'
    AND device_category = 'mobile'
    AND (clicked_element_id = 'expense-save'
      OR page IN ('mytimereport',
        'teamreport',
        'teamcapacityreport',
        'invoices'))
  GROUP BY
    1,
    2 ),
  sessions AS (
  SELECT
    DISTINCT DATE(session_start_time) AS event_date,
    user_id
  FROM
    `harvesthq-production.harvest_analytics.sessions`
  WHERE
    session_start_time between '{start_date}' and '{end_date}' ),
  semi_final AS (
  SELECT
    users.event_date,
    users.user_id,
    users.company_id,
    CASE
      WHEN ts.seats IS NULL OR ts.seats < 1 THEN NULL
      WHEN ts.seats < 3 THEN 'Personal (1-2)'
      WHEN ts.seats < 10 THEN 'Small Team (3-9)'
      WHEN ts.seats < 50 THEN 'Medium Team (10-49)'
      WHEN ts.seats < 100 THEN 'Large Team (50-99)'
      ELSE 'XL Team (100+)'
  END
    AS seats_size,
    CASE
      WHEN time.user_id IS NOT NULL THEN 1
      ELSE 0
  END
    AS time_engaged,
    COALESCE(time.tracked_via_integration, 0) AS time_integration_engaged,
    CASE
      WHEN expenses.user_id IS NOT NULL THEN 1
      ELSE 0
  END
    AS expenses_engaged,
    CASE
      WHEN invoices.user_id IS NOT NULL THEN 1
      ELSE 0
  END
    AS invoices_engaged,
    CASE
      WHEN submissions.user_id IS NOT NULL THEN 1
      ELSE 0
  END
    AS timesheet_submission_engaged,
    CASE
      WHEN approvals.user_id IS NOT NULL THEN 1
      ELSE 0
  END
    AS timesheet_approval_engaged,
    CASE
      WHEN estimates.user_id IS NOT NULL THEN 1
      ELSE 0
  END
    AS estimates_engaged,
    GREATEST(CASE
        WHEN project_events.user_id IS NOT NULL THEN 1
        ELSE 0
    END
      , COALESCE(pv.viewed_projects_page, 0),
      CASE
        WHEN pc.user_id IS NOT NULL THEN 1
        ELSE 0
    END
      ) AS projects_engaged,
  FROM
    active_users_daily AS users
  LEFT JOIN
    team_size_daily AS ts
  ON
    users.company_id = ts.company_id
    AND users.event_date = ts.event_date
  LEFT JOIN
    time_entries AS time
  ON
    users.user_id = time.user_id
    AND users.event_date = time.event_date
  LEFT JOIN
    expenses
  ON
    users.user_id = expenses.user_id
    AND users.event_date = expenses.event_date
  LEFT JOIN
    invoices
  ON
    users.user_id = invoices.user_id
    AND users.event_date = invoices.event_date
  LEFT JOIN
    estimates
  ON
    users.user_id = estimates.user_id
    AND users.event_date = estimates.event_date
  LEFT JOIN
    submitted_timesheets AS submissions
  ON
    users.user_id = submissions.user_id
    AND users.event_date = submissions.event_date
  LEFT JOIN
    approved_timesheets AS approvals
  ON
    users.user_id = approvals.user_id
    AND users.event_date = approvals.event_date
  LEFT JOIN
    page_views AS pv
  ON
    users.user_id = pv.user_id
    AND users.event_date = pv.event_date
  LEFT JOIN
    project_events
  ON
    users.user_id = project_events.user_id
    AND users.event_date = project_events.event_date
  LEFT JOIN
    projects_created AS pc
  ON
    users.user_id = pc.user_id
    AND users.event_date = pc.event_date
  ORDER BY
    users.event_date,
    users.user_id)
SELECT
  CAST(user_id AS string) uid,
  TIMESTAMP(event_date) AS event_timestamp
FROM
  semi_final
WHERE
  time_engaged > 0
  OR time_integration_engaged> 0
  OR expenses_engaged> 0
  OR invoices_engaged> 0
  OR timesheet_submission_engaged> 0
  OR timesheet_approval_engaged> 0
  OR estimates_engaged> 0
  OR projects_engaged>0'''



def request_and_plot_metric(
    common_params,
    segments_params,
    metric,
    title,
    additional_figure_params=None,
    uplift_vs = None # pass a string of the segment vs which you want to compute the uplift e.g. 'control_segment'
    ):

    # extract values from common params to construct the title
    start_date = [param.value for param in common_params if param.__class__.__name__ == 'StartDate'][0]
    end_date = [param.value for param in common_params if param.__class__.__name__ == 'EndDate'][0]
    actions_end_date = [param.value for param in common_params if param.__class__.__name__ == 'ActionsEndDate'][0]
    default_title = f"<b>{metric.name}</b><br>StartDate={start_date} EndDate={end_date} ActionsEndDate={actions_end_date}"
    title = default_title if title is None else title

    
    results = request_multiple_metrics(
       
        common_params=common_params + metric.metric,
        segments_params=segments_params,
    )

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

    if uplift_vs:
        df = pd.DataFrame(results[experiment_segments.index(uplift_vs)].profile)
        cols = ['time_bin']
        for segment in experiment_segments:
            if segment != uplift_vs:
                df0 = pd.DataFrame(results[experiment_segments.index(segment)].profile)
                df = df.merge(df0, on='time_bin', suffixes=['', '_'+segment])
                df[segment+'_uplift_vs_'+uplift_vs] = ((df['value_'+segment] - df['value']) / (df['value'] )) 
                cols.append(segment+'_uplift_vs_'+uplift_vs)

        melted_df = df[cols].melt(id_vars=['time_bin'], var_name='series', value_name='values')

        fig = px.scatter(melted_df, x='time_bin', y='values', color='series', 
                        title=f'<b>Uplift vs {uplift_vs}</b>',
                        labels={'time_bin': 'Days', 'values': '', 'series': ''})


        fig.update_yaxes(title=None)
        fig.update_traces(marker=dict(size=10))
        fig.update_yaxes(showgrid=True, gridcolor='lightgrey')
        fig.update_layout(plot_bgcolor='white')
        fig.add_hline(y=0, line_color="black")
        fig.show()


def get_conversions(start_date, end_date, only_paid=False):

    transactions = (
        Query()
        .select(
            ('user_id', 'uid'),('timestamp','event_timestamp'),('subscription_id'),('subscription_manager'),('product_info'),('event_info'), ('bookings_net_of_platform_fees_usd', 'event_value'),
            ("JSON_EXTRACT_SCALAR(product_info, '$.periodicity')", 'product_periodicity' ),
            ("SAFE_CAST(REGEXP_EXTRACT(JSON_VALUE(product_info, '$.product_description'), r'^\s*(\d+)') AS INT64)", 'seat_number'),
            ('event_type')
        )
        .from_(" `harvest-lumenx-42.verified.bookings` ")
        .where('''event_type IN ('purchase' , 'free_trial') 
        AND ( JSON_EXTRACT_SCALAR(event_info, '$.is_mid_subscription_expansion') IS NULL OR JSON_EXTRACT_SCALAR(event_info, '$.is_mid_subscription_expansion') = "false") 
        AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') <> "Subscription update" OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
        AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') NOT LIKE "%Additional%" OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
        AND (JSON_EXTRACT_SCALAR(product_info, '$.product_description') NOT LIKE "%adjustment%" OR JSON_EXTRACT_SCALAR(product_info, '$.product_description') IS NULL)
        AND (ARRAY_LENGTH(JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids')) = 0 OR JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids') IS NULL OR JSON_VALUE(JSON_EXTRACT_ARRAY(product_info, '$.add_on_ids')[OFFSET(0)]) = 'additional_user')
    ''')

    )

    if only_paid: 
        transactions = transactions.where('bookings_net_of_platform_fees_usd > 0')

    final = (
        Query()
        .select(
            ('uid'),
            ('event_timestamp'),
            ('event_value')
        )
        .from_(transactions)
    )

    return final


    # ------------------ 🧪 EXPERIMENT VARIABLES 🧪 ------------------ #

start_date = '2025-09-09'
end_date = str(today().date())
actions_end_date = str(today().date())

experiment_name = 'grw1_post_obe_paywall'
experiment_segments = ['control_segment', 'intro_upsell']

# If the experiment is meant for Free users but you accidentally segmented also Paying users
# then set the only_free_users variable to True.
only_free_users = True

# -------------- 🪴 EXTRA FOR GROWTH EXPERIMENTS 🪴 -------------- #

# Reach and Conversions at Target Paywall
include_reach_section = True
include_conversion_breakdowns = True
include_conversions_at_target_paywall_profiles = True

#target_paywall_display_event = 'action_kind = "delta_on_session_paywall_shown"'
#target_paywall_conversion_event = 'offer_group = "Back To School 2024"'

# growth engagement model
include_engagement_model = False
action_engagement_model = 'task - create-task' #action_kind
action_engagement_model_2 = 'task - create-task' #action_kind

# ------------------- 📈 METRICS TO INCLUDE 📈 ------------------- #

# Commented metrics will not be computed (check the Notion guide if you want to add new metrics)
notebook_metrics_list = [
    'ConversionToSubscription',
    'ConversionToPaySubscription',
    'SubscriptionArpu',
    'SubscriptionArps',
    'Retention',
    'AutoRenewOff'
]

# ----------------------- 🧩 BREAKDOWNS 🧩 ----------------------- #

breakdowns = [
    'Client',
     'Tenure',
     'User State'
]

metrics_for_breakdowns = [
    'ConversionToSubscription',
    'ConversionToPaySubscription',
    'SubscriptionArpu',
    'Retention',
    'AutoRenewOff'
]

# ----------------------- 🔮 PROJECTIONS 🔮 ---------------------- #

include_projections = True


# COMMON PARAMS

horizon_in_days = (datetime.strptime(actions_end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days

common_params = [
    App("HarvestWeb"),
    StartDate(start_date),
    EndDate(end_date),
    ActionsEndDate(actions_end_date),
    GranularityInDays(1 if horizon_in_days < 40 else 7),
]


# SEGMENTS PARAMS DEFINITIONS

custom_user_base_common_params = {
    "experiment_name": experiment_name,
    "start_date": start_date,
    "end_date": end_date
}


segments_params_all = [
    [
        UserBaseBigQuery(
            get_experiment_user_base(
                **custom_user_base_common_params,
                segment_name=segment
            ).to_sql(),
            OnTableExistence.KEEP,
        ),
        Label(segment)
    ]
    for segment in experiment_segments
]


segments_params_noft = [
    [
        UserBaseBigQuery(
            get_experiment_user_base(
                **custom_user_base_common_params,
                segment_name=segment,
                exclude_converted=True
            ).to_sql(),
            OnTableExistence.KEEP,
        ),
        Label(segment)
    ]
    for segment in experiment_segments
]


def get_aro(start_date, end_date):
    aro = (
        Query()
        .select('user_id uid, timestamp as event_timestamp')
        .from_( "`harvest-lumenx-42.verified.bookings`")
        .where(" event_type = 'auto_renew_off'")
    )

    if start_date:
        aro.where(f" timestamp >=  '{start_date}'")
    if end_date:
        aro.where(f" timestamp <= '{end_date}'" )

    final = (
        Query()
        .select(
            ('uid'),
            ('event_timestamp'),
        )
        .from_(aro)
    )

    return final



from collections import namedtuple

Metric = namedtuple('Metric', ['name', 'metric'])

conversion_to_subscription_=  Metric(
    name='C2S',
    metric=[CustomFirstSuccessRateMetric(target_query=get_conversions(start_date, end_date), estimator='cumulated')]
)


conversion_to_pay_subscription=  Metric(
    name='C2P',
    metric=[CustomFirstSuccessRateMetric(target_query=get_conversions(start_date, end_date,  only_paid=True), estimator='cumulated')]
)


ARPU =  Metric(
    name='ARPU',
    metric=[CustomValuedMetric(target_query=get_conversions(start_date, end_date, only_paid=False), estimator='cumulated')]
)


ARPS =  Metric(
    name='ARPU',
    metric=[CustomValuedMetric(target_query=get_conversions(start_date, end_date, only_paid=True), estimator='cumulated')]
)


ArOff =  Metric(
    name='AutoRenewOff',
    metric=[CustomFirstSuccessRateMetric(target_query=get_aro(start_date, end_date), estimator='cumulated')]
)




Qualified_activity =  Metric(
    name='QualifiedActivityDaily',
    metric=[CustomCountMetric(cumulative=True,target_query=get_activity_rate_qualified(start_date, end_date), estimator='cumulated')]
)

Sessions = Metric (
    name='Sessions',
    metric=[CustomCountMetric(cumulative=True,target_query=get_sessions(start_date, end_date), estimator='cumulated')]

)

TrackedHours = Metric (
    name='HoursTracked',
    metric=[CustomValuedMetric(cumulative=True,target_query=get_time_entries(start_date, end_date), estimator='cumulated')]

)

segmentation_by_client = (
    Query()
    .select(
        ('TIMESTAMP_TRUNC(origin_timestamp, HOUR)', 'time'),
        (   '''
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






segmentation_by_segment = (
    Query()
    .select(
        'segment_name',
        ('COUNT(DISTINCT uid)', 'users'),
    )
    .from_(segmented_users)
    .group_by('1')
)


if include_conversion_breakdowns:

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
    JSON_VALUE(payload, '$.experiment_name') = '{experiment_name}'
    AND DATE(event_timestamp) >= '{start_date}'
    AND DATE(event_timestamp) <= '{end_date}'
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
    conversion_breakdown_df = read_gbq(conversion_breakdown_query)

else: # empty dfs to avoid Hex charts errors
    conversion_breakdown_df = pd.DataFrame(columns=['segment_name', 'global_user_id', 'offer_group', 'plan', 'periodicity', 'net_revenues_usd'])




### example of usage 
'''
df_seg_client = read_gbq(segmentation_by_client)
df_seg_segment = read_gbq(segmentation_by_segment)
df = df_seg_client.copy().sort_values('time')

df['users_cumulative'] = df.groupby('segmentation_client')['users'].transform('cumsum')

px.line(
    df, 
    x='time', 
    y='users_cumulative', 
    color='segmentation_client', 
    title='<b>Segmented Users - Breakdown by Client',
    category_orders={'segmentation_client': ['ios', 'android', 'desktop', 'web']}    
)

df = df_seg_segment.copy()
px.bar(
    df, 
    x='segment_name', 
    y='users', 
    color='segment_name', 
    title='<b>Segmented Users - Breakdown by Segment',
)

if 'ConversionToSubscription' in notebook_metrics_list:
    
   if 'ConversionToSubscription' in notebook_metrics_list:
    
    request_and_plot_metric(
        common_params=common_params,
        segments_params=segments_params_all,
        metric=conversion_to_subscription_,
        title=None
    )


if 'ConversionToPaySubscription' in notebook_metrics_list:
    
    request_and_plot_metric(
        common_params=common_params,
        segments_params=segments_params_all,
        metric=conversion_to_pay_subscription,
        title=None
    )
'''