-- Run only as the authorized beta operator. Returns aggregates, no names or notes.
-- UTC calendar weeks; suggestions served are NOT successful outcomes.
WITH activity AS (
 SELECT DISTINCT user_id, date_trunc('week', created_at AT TIME ZONE 'UTC') AS week
 FROM public.audit_logs
 WHERE event_type IN ('capture_confirmed','beta_retrieval','beta_source_opened',
   'relationship_home_view','relationship_ask_answered','relationship_action_completed',
   'relationship_action_scheduled','relationship_action_dismissed')
), success AS (
 SELECT user_id, date_trunc('week', created_at AT TIME ZONE 'UTC') AS week, count(*) AS actions
 FROM public.relationship_actions WHERE action='completed' GROUP BY 1,2
), served AS (
 SELECT date_trunc('week', created_at AT TIME ZONE 'UTC') AS week,
 count(DISTINCT (user_id, request_id)) AS suggestions
 FROM public.audit_logs WHERE event_type='relationship_suggestion_served' GROUP BY 1
)
SELECT a.week, count(*) AS weekly_active_users,
 coalesce(sum(s.actions),0) AS successful_relationship_actions,
 round(coalesce(sum(s.actions),0)::numeric / nullif(count(*),0),2) AS actions_per_wau,
 count(previous.user_id) AS active_in_previous_week,
 max(served.suggestions) AS suggestions_served
FROM activity a LEFT JOIN success s USING(user_id,week)
LEFT JOIN activity previous ON previous.user_id=a.user_id AND previous.week=a.week-interval '7 days'
LEFT JOIN served ON served.week=a.week
GROUP BY a.week ORDER BY a.week DESC;

-- Activation is recorded once first observed with 5 people / 3 interactions /
-- 1 project / 1 commitment / 1 Ask response containing evidence.
SELECT count(DISTINCT user_id) AS activated_users
FROM public.audit_logs WHERE event_type='relationship_activated';

-- Latest stated willingness per respondent; interest is NOT paid conversion.
WITH latest AS (
 SELECT DISTINCT ON(user_id) user_id,event_type FROM public.audit_logs
 WHERE event_type IN ('willingness_to_pay_yes','willingness_to_pay_no','willingness_to_pay_unsure')
 ORDER BY user_id,created_at DESC
) SELECT event_type,count(*) AS respondents FROM latest GROUP BY event_type;

-- Current private graph density, not historical lifetime totals.
SELECT (SELECT count(*) FROM public.people WHERE deleted_at IS NULL AND archived_at IS NULL) AS people,
 (SELECT count(*) FROM public.entity_edges) AS explicit_connections,
 (SELECT count(*) FROM public.interactions WHERE deleted_at IS NULL AND archived_at IS NULL) AS interactions;
