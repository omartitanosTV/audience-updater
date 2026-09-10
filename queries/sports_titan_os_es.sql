-- Audience Definition: Sports - Titan OS (ES)
-- Platform: Titan OS
-- Market: ES
-- Test Period: Last 3 days
--
-- Positive Signals:
-- 1. Apps: DAZN
-- 2. Titles: Football matches, sports highlights, sports broadcasts
-- 3. Affinities Tier 1: sports
-- 4. Affinities Tier 2:
--    football, golf, tennis, basketball, formula racing,
--    baseball, cricket, rugby, ice hockey, water sports
--
-- Demographics: None
-- Exclusions: None


WITH

/* ================================================================================================
   APPS
================================================================================================ */

apps AS (

    SELECT
        country_code,
        device_id

    FROM titanos_dwh.public.app_launches_all_sources a

    WHERE a.country_code = 'ES'
      AND a.os_version = 'Titan OS'
      AND a.app_name IN (
          'DAZN'
      )
      AND a.app_usage_date BETWEEN current_date() - 3 AND current_date() - 1

    GROUP BY
        country_code,
        device_id

    HAVING SUM(a.duration_in_minutes) > 30
),


/* ================================================================================================
   TITLES
================================================================================================ */

titles AS (

    SELECT DISTINCT
        b.country_code,
        b.device_id

    FROM titanos_dwh.public.broadcast_match_nulls b

    WHERE b.country_code = 'ES'
      AND b.event_date BETWEEN current_date() - 3 AND current_date() - 1
      AND b.time_watched_seconds > 180
      AND b.title IN (
          'Deportes 2',
          'Deportes 1',
          'Futbol Laliga Ea Sports',
          'LaLiga EA Sports',
          'Resúmenes LALIGA EA Sports',
          'Estudio estadio',
          'El chiringuito',
          'El chiringuito de jugones',
          'Deportes fin de semana',
          'Gol',
          'Teledeporte 1',
          'Teledeporte 2',
          'Deportes 1 (Antena 3)'
      )
),


/* ================================================================================================
   AFFINITIES TIER 1
================================================================================================ */

affinities1 AS (

    SELECT
        country_code,
        device_id

    FROM titanos_dwh.simplytv.affinities_tier1_active_devices a

    WHERE a.country_code = 'ES'
      AND a.os_version = 'Titan OS'
      AND a.segment = 'sports'
      AND a.engagement_score >= 0.2
),


/* ================================================================================================
   AFFINITIES TIER 2
================================================================================================ */

affinities2 AS (

    SELECT
        country_code,
        device_id

    FROM titanos_dwh.simplytv.affinities_tier2_active_devices a

    WHERE a.country_code = 'ES'
      AND a.os_version = 'Titan OS'
      AND a.segment IN (
          'football',
          'golf',
          'tennis',
          'basketball',
          'formula racing',
          'baseball',
          'cricket',
          'rugby',
          'ice hockey',
          'water sports'
      )
      AND a.engagement_score >= 0.2
),


/* ================================================================================================
   COMBINE ALL POSITIVE SIGNALS
================================================================================================ */

audience_devices_pre_exclusion AS (

    SELECT device_id
    FROM apps

    UNION

    SELECT device_id
    FROM titles

    UNION

    SELECT device_id
    FROM affinities1

    UNION

    SELECT device_id
    FROM affinities2
),


/* ================================================================================================
   FINAL AUDIENCE DEVICES
================================================================================================ */

audience_devices AS (

    SELECT DISTINCT
        device_id

    FROM audience_devices_pre_exclusion
),


/* ================================================================================================
   MAP DEVICE_ID TO IFA_ID
================================================================================================ */

target_audience AS (

    SELECT DISTINCT
        d.country_code,
        d.os_version,
        d.ifa_id

    FROM titanos_trinity_data_model.public.dim_devices_all d

    INNER JOIN audience_devices ad
        ON ad.device_id = d.externalid

    WHERE d.is_dev = FALSE
      AND d.is_factory = FALSE
      AND d.ifa_id IS NOT NULL
      AND d.ifa_id <> '00000000-0000-0000-0000-000000000000'
      AND d.country_code = 'ES'
      AND d.os_version = 'Titan OS'
)


/* ================================================================================================
   OUTPUT FOR SPRINGSERVE
================================================================================================ */

SELECT DISTINCT
    ifa_id

FROM target_audience

WHERE ifa_id IS NOT NULL
  AND ifa_id <> '00000000-0000-0000-0000-000000000000'

ORDER BY
    ifa_id;