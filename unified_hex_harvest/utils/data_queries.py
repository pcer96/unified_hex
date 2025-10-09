"""
Data query functions for experiment analysis.
"""

from typing import Optional, List, Union
# Note: Query and other bsp_data_analysis imports should be done in Hex notebook
# from bsp_data_analysis.helpers import *
# from bsp_data_analysis.helpers.standard_imports import *


class DataQueries:
    """Collection of data query functions for experiment analysis."""
    
    @staticmethod
    def get_experiment_user_base(
        experiment_name: str,
        segment_name: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exclude_converted: Optional[bool] = None
    ) -> Query:
        """
        Get user base for an experiment with optional filtering.
        
        Args:
            experiment_name: Name of the experiment
            segment_name: Segment name(s) to filter by
            start_date: Start date filter
            end_date: End date filter
            exclude_converted: Whether to exclude converted users
            
        Returns:
            Query object for the user base
        """
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

        userbase = (
            Query()
            .select(" seg.uid,seg.origin_timestamp,seg.segmentation_client,seg.segment_name")
            .from_(segmented_users, alias='seg')
        )

        if exclude_converted:
            transactions = (
                Query()
                .select(
                    ('user_id', 'uid'), ('timestamp', 'event_timestamp'), ('subscription_id'), 
                    ('subscription_manager'), ('product_info'), ('event_info'), 
                    ('bookings_net_of_platform_fees_usd', 'event_value'),
                    ("JSON_EXTRACT_SCALAR(product_info, '$.periodicity')", 'product_periodicity'),
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

            userbase.join(final, alias='final', using='uid', join_type='left').where('final.uid is null')

        return userbase

    @staticmethod
    def get_time_entries(start_date: str, end_date: str) -> str:
        """Get time entries query."""
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

    @staticmethod
    def get_sessions(start_date: Optional[str] = None, end_date: str = '2030-01-01') -> str:
        """Get sessions query."""
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

    @staticmethod
    def get_activity_rate_qualified(start_date: Optional[str] = None, end_date: str = '2030-01-01') -> str:
        """Get qualified activity rate query."""
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

    @staticmethod
    def get_conversions(start_date: str, end_date: str, only_paid: bool = False) -> Query:
        """Get conversions query."""
        transactions = (
            Query()
            .select(
                ('user_id', 'uid'), ('timestamp', 'event_timestamp'), ('subscription_id'), 
                ('subscription_manager'), ('product_info'), ('event_info'), 
                ('bookings_net_of_platform_fees_usd', 'event_value'),
                ("JSON_EXTRACT_SCALAR(product_info, '$.periodicity')", 'product_periodicity'),
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

    @staticmethod
    def get_aro(start_date: str, end_date: str) -> Query:
        """Get auto-renew off query."""
        aro = (
            Query()
            .select('user_id uid, timestamp as event_timestamp')
            .from_("`harvest-lumenx-42.verified.bookings`")
            .where(" event_type = 'auto_renew_off'")
        )

        if start_date:
            aro.where(f" timestamp >=  '{start_date}'")
        if end_date:
            aro.where(f" timestamp <= '{end_date}'")

        final = (
            Query()
            .select(
                ('uid'),
                ('event_timestamp'),
            )
            .from_(aro)
        )

        return final
