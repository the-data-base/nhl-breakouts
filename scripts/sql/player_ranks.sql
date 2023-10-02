-- Goal: re-create Jfresh percentile ranks
--... query the top percentile forwards in the NHL over the past 3 seasons
--... padding for ev based on analysis in xg_padding.ipynb...

with

-- cte1: the player's current team
current_team as (
select
 distinct s.player_team_season_id
 ,s.player_id
 ,s.team_id
 ,s.season_id
 ,t.abbreviation as team_code
 ,t.full_name as team_full_name
 ,t.team_name
 ,s.career_first_dt
 ,sum(s.games_played) over (partition by player_id) as games_played
from nhl-breakouts.dbt_dom.d_player_team_season as s
left join nhl-breakouts.dbt_dom.d_teams as t on t.team_id = s.team_id
where is_player_current_team is True
qualify row_number() over (partition by player_id order by player_season_team_last_dt desc) = 1
)

-- cte2: current-season-stats
,current_stats as (
select
-- identifiers
  s.player_id
  ,s.game_type
  ,s.player_full_name as player_name
  ,'2023' as season
  ,'Last 3 seasons' as season_window
-- avg features
  ,avg(avg_time_on_ice_mins) as avg_toi_m
  ,avg(avg_ev_time_on_ice_mins) as avg_ev_toi_m
  ,avg(avg_pp_time_on_ice_mins) as avg_pp_toi_m
  ,avg(avg_sh_time_on_ice_mins) as avg_sh_toi_m
-- sum features
  ,count(distinct season_id) as season_ct
  ,sum(boxscore_games) as gp
  ,sum(time_on_ice_seconds) as toi_s
  ,sum(time_on_ice_minutes) as toi_m
  ,sum(ev_time_on_ice_minutes) as ev_toi_m
  ,sum(pp_time_on_ice_minutes) as pp_toi_m
  ,sum(sh_time_on_ice_minutes) as sh_toi_m
  ,sum(goals) as goals
  ,sum(assists_primary) as a1
  ,sum(minor_pim_drawn) as minor_pim_drawn
  ,sum(minor_pim_taken) as minor_pim_taken
  ,sum(shots_iscored) as shots_iscored
  ,round(sum(shots_ixg), 2) as shots_ixg
  ,sum(shots_ev_iscored) as shots_ev_iscored
  ,round(sum(shots_ev_ixg), 2) as shots_ev_ixg
  ,sum(shots_pp_iscored) as shots_pp_iscored
  ,round(sum(shots_pp_ixg), 2) as shots_pp_ixg
  ,sum(shots_sh_iscored) as shots_sh_iscored
  ,round(sum(shots_sh_ixg), 2) as shots_sh_ixg
  ,sum(penalty_shot_goals) as ps_goals
  ,sum(empty_net_goals) as en_goals
  ,sum(shots_xgf) as xgf
  ,sum(shots_xga) as xga
  ,sum(shots_ev_xgf) as xgf_ev
  ,sum(shots_ev_xga) as xga_ev
  ,sum(shots_pp_xgf) as xgf_pp
  ,sum(shots_pp_xga) as xga_pp
  ,sum(shots_sh_xgf) as xgf_sh
  ,sum(shots_sh_xga) as xga_sh
-- differential features
  ,sum(minor_pim_drawn) - sum(minor_pim_taken) as minor_pim_diff
  ,sum(shots_iscored) - sum(penalty_shot_goals) - sum(empty_net_goals) as xgoals
  ,round(sum(shots_iscored) - sum(shots_ixg), 2) as gae
  ,round(sum(shots_xgf) - sum(shots_xga), 2) as xg_diff
  ,round(sum(shots_ev_xgf) - sum(shots_ev_xga), 2) as xg_ev_diff
  ,round(sum(shots_pp_xgf) - sum(shots_pp_xga), 2) as xg_pp_diff
  ,round(sum(shots_sh_xgf) - sum(shots_sh_xga), 2) as xg_sh_diff
-- per60 features (original)
  ,round((sum(minor_pim_drawn) - sum(minor_pim_taken)) / ((sum(time_on_ice_minutes)) / 60),2) as minor_pim_diff_per60
  ,round((sum(shots_iscored) - sum(penalty_shot_goals) - sum(empty_net_goals)) / ((sum(time_on_ice_minutes)) / 60),2) as xgoals_per60
  ,round((sum(goals) / ((sum(time_on_ice_minutes)) / 60)),2) as goals_per60
  ,round((sum(shots_iscored) - sum(shots_ixg)) / ((sum(time_on_ice_minutes)) / 60),2) as gae_per60
  ,round((sum(assists_primary) / ((sum(time_on_ice_minutes)) / 60)),2) as a1_per60
  ,round(safe_divide(sum(shots_ev_xgf), ((sum(ev_time_on_ice_minutes)) / 60)),2) as xgf_ev_per60
  ,round(safe_divide(sum(shots_ev_xga), ((sum(ev_time_on_ice_minutes)) / 60)),2) as xga_ev_per60
  ,round(safe_divide(sum(shots_pp_xgf), ((sum(pp_time_on_ice_minutes)) / 60)),2) as xgf_pp_per60
  ,round(safe_divide(sum(shots_pp_xga), ((sum(pp_time_on_ice_minutes)) / 60)),2) as xga_pp_per60
  ,round(safe_divide(sum(shots_sh_xgf), ((sum(sh_time_on_ice_minutes)) / 60)),2) as xgf_sh_per60
  ,round(safe_divide(sum(shots_sh_xga), ((sum(sh_time_on_ice_minutes)) / 60)),2) as xga_sh_per60
-- per60 features (padded)
  ,round((sum(shots_ev_xgf) + (2.5/60*1000)) / ((sum(ev_time_on_ice_minutes) + 1000) / 60),2) as adj_xgf_ev_per60
  ,round((sum(shots_ev_xga) + (2.5/60*1000)) / ((sum(ev_time_on_ice_minutes) + 1000) / 60),2) as adj_xga_ev_per60
  ,round(safe_divide((sum(shots_pp_xgf) + (5/60*200)), ((sum(pp_time_on_ice_minutes) + 200) / 60)),2) as adj_xgf_pp_per60
  ,round(safe_divide((sum(shots_pp_xga) + (2/60*200)), ((sum(pp_time_on_ice_minutes) + 200) / 60)),2) as adj_xga_pp_per60
  ,round(safe_divide((sum(shots_sh_xgf) + (1.2/60*150)), ((sum(sh_time_on_ice_minutes) + 150) / 60)),2) as adj_xgf_sh_per60
  ,round(safe_divide((sum(shots_sh_xga) + (4/60*150)), ((sum(sh_time_on_ice_minutes) + 150) / 60)),2) as adj_xga_sh_per60

from
  nhl-breakouts.dbt_dom.f_player_season as s
where 1 =1
  and game_type = '02'
  and cast(season_id as int64) in (20202021, 20212022, 20222023)
group by 1, 2, 3, 4, 5
having 1 = 1
  and sum(time_on_ice_minutes) > 150
  and sum(boxscore_games) > 30
  and avg(avg_time_on_ice_mins) > 9
  and sum(case when cast(season_id as int64) = 20222023 then shots_iff else 0 end) > 10
)

-- cte3: current-season-stats
,season_stats as (
select
-- identifiers
  s.player_id
  ,s.game_type
  ,s.player_full_name as player_name
  ,left(cast(season_id as string), 4) as season
  ,'1 season' as season_window
-- avg features
  ,avg(avg_time_on_ice_mins) as avg_toi_m
  ,avg(avg_ev_time_on_ice_mins) as avg_ev_toi_m
  ,avg(avg_pp_time_on_ice_mins) as avg_pp_toi_m
  ,avg(avg_sh_time_on_ice_mins) as avg_sh_toi_m
-- sum features
  ,count(distinct season_id) as season_ct
  ,sum(boxscore_games) as gp
  ,sum(time_on_ice_seconds) as toi_s
  ,sum(time_on_ice_minutes) as toi_m
  ,sum(ev_time_on_ice_minutes) as ev_toi_m
  ,sum(pp_time_on_ice_minutes) as pp_toi_m
  ,sum(sh_time_on_ice_minutes) as sh_toi_m
  ,sum(goals) as goals
  ,sum(assists_primary) as a1
  ,sum(minor_pim_drawn) as minor_pim_drawn
  ,sum(minor_pim_taken) as minor_pim_taken
  ,sum(shots_iscored) as shots_iscored
  ,round(sum(shots_ixg), 2) as shots_ixg
  ,sum(shots_ev_iscored) as shots_ev_iscored
  ,round(sum(shots_ev_ixg), 2) as shots_ev_ixg
  ,sum(shots_pp_iscored) as shots_pp_iscored
  ,round(sum(shots_pp_ixg), 2) as shots_pp_ixg
  ,sum(shots_sh_iscored) as shots_sh_iscored
  ,round(sum(shots_sh_ixg), 2) as shots_sh_ixg
  ,sum(penalty_shot_goals) as ps_goals
  ,sum(empty_net_goals) as en_goals
  ,sum(shots_xgf) as xgf
  ,sum(shots_xga) as xga
  ,sum(shots_ev_xgf) as xgf_ev
  ,sum(shots_ev_xga) as xga_ev
  ,sum(shots_pp_xgf) as xgf_pp
  ,sum(shots_pp_xga) as xga_pp
  ,sum(shots_sh_xgf) as xgf_sh
  ,sum(shots_sh_xga) as xga_sh
-- differential features
  ,sum(minor_pim_drawn) - sum(minor_pim_taken) as minor_pim_diff
  ,sum(shots_iscored) - sum(penalty_shot_goals) - sum(empty_net_goals) as xgoals
  ,round(sum(shots_iscored) - sum(shots_ixg), 2) as gae
  ,round(sum(shots_xgf) - sum(shots_xga), 2) as xg_diff
  ,round(sum(shots_ev_xgf) - sum(shots_ev_xga), 2) as xg_ev_diff
  ,round(sum(shots_pp_xgf) - sum(shots_pp_xga), 2) as xg_pp_diff
  ,round(sum(shots_sh_xgf) - sum(shots_sh_xga), 2) as xg_sh_diff
-- per60 features (original)
  ,round((sum(minor_pim_drawn) - sum(minor_pim_taken)) / ((sum(time_on_ice_minutes)) / 60),2) as minor_pim_diff_per60
  ,round((sum(shots_iscored) - sum(penalty_shot_goals) - sum(empty_net_goals)) / ((sum(time_on_ice_minutes)) / 60),2) as xgoals_per60
  ,round((sum(goals) / ((sum(time_on_ice_minutes)) / 60)),2) as goals_per60
  ,round((sum(shots_iscored) - sum(shots_ixg)) / ((sum(time_on_ice_minutes)) / 60),2) as gae_per60
  ,round((sum(assists_primary) / ((sum(time_on_ice_minutes)) / 60)),2) as a1_per60
  ,round(safe_divide(sum(shots_ev_xgf), ((sum(ev_time_on_ice_minutes)) / 60)),2) as xgf_ev_per60
  ,round(safe_divide(sum(shots_ev_xga), ((sum(ev_time_on_ice_minutes)) / 60)),2) as xga_ev_per60
  ,round(safe_divide(sum(shots_pp_xgf), ((sum(pp_time_on_ice_minutes)) / 60)),2) as xgf_pp_per60
  ,round(safe_divide(sum(shots_pp_xga), ((sum(pp_time_on_ice_minutes)) / 60)),2) as xga_pp_per60
  ,round(safe_divide(sum(shots_sh_xgf), ((sum(sh_time_on_ice_minutes)) / 60)),2) as xgf_sh_per60
  ,round(safe_divide(sum(shots_sh_xga), ((sum(sh_time_on_ice_minutes)) / 60)),2) as xga_sh_per60
-- per60 features (padded)
  ,round((sum(shots_ev_xgf) + (2.5/60*1000)) / ((sum(ev_time_on_ice_minutes) + 1000) / 60),2) as adj_xgf_ev_per60
  ,round((sum(shots_ev_xga) + (2.5/60*1000)) / ((sum(ev_time_on_ice_minutes) + 1000) / 60),2) as adj_xga_ev_per60
  ,round(safe_divide((sum(shots_pp_xgf) + (5/60*200)), ((sum(pp_time_on_ice_minutes) + 200) / 60)),2) as adj_xgf_pp_per60
  ,round(safe_divide((sum(shots_pp_xga) + (2/60*200)), ((sum(pp_time_on_ice_minutes) + 200) / 60)),2) as adj_xga_pp_per60
  ,round(safe_divide((sum(shots_sh_xgf) + (1.2/60*150)), ((sum(sh_time_on_ice_minutes) + 150) / 60)),2) as adj_xgf_sh_per60
  ,round(safe_divide((sum(shots_sh_xga) + (4/60*150)), ((sum(sh_time_on_ice_minutes) + 150) / 60)),2) as adj_xga_sh_per60
from
  nhl-breakouts.dbt_dom.f_player_season as s
where 1 =1
  and game_type = '02'
  and cast(season_id as int64) in (20202021, 20212022, 20222023)
  --and exists (select 1 from current_stats where current_stats.player_id = s.player_id)
group by 1, 2, 3, 4, 5
having 1 = 1
  and sum(time_on_ice_minutes) > 150
  and sum(boxscore_games) > 12
  and avg(avg_time_on_ice_mins) > 9
  and sum(shots_iff) > 10
)

-- cte4: union together
,raw_stats as (
  select *from current_stats
  union all
  select *
  from season_stats
)
-- cte5: diff metrics
,stats as (
  select
    *
  -- after-padding & adjustments
  ,adj_xgf_ev_per60 - adj_xga_ev_per60 as adj_xg_ev_diff_per60
  ,adj_xgf_pp_per60 - adj_xga_pp_per60 as adj_xg_pp_diff_per60
  ,adj_xgf_sh_per60 - adj_xga_sh_per60 as adj_xg_sh_diff_per60
  -- raw per 60
  ,xgf_ev_per60 - xga_ev_per60 as xg_ev_diff_per60
  ,xgf_pp_per60 - xga_pp_per60 as xg_pp_diff_per60
  ,xgf_sh_per60 - xga_sh_per60 as xg_sh_diff_per60

  from raw_stats
  )

-- cte6: percentiles
,percentiles as (
select
  -- identifiers
  s.player_id
  ,s.player_name
  ,s.game_type
  ,s.season
  ,s.season_window
  ,p.primary_position_name
  ,p.primary_position_type
  ,p.birth_date
  ,p.nationality
  ,p.height
  ,p.weight
  ,p.primary_number
  ,p.shoots_catches
  ,t.team_id as current_team_id
  ,t.team_full_name as current_team_full_name
  ,t.team_name as current_team_name
  ,t.team_code as current_team_code
  ,t.career_first_dt as first_career_game
  -- rankings (adjusted per 60 -- did not pad all, just xg related)
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by avg_toi_m asc)  as `Avg TOI`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by toi_s asc)  as `TOI`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by adj_xg_ev_diff_per60 asc) as `EV XG`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by adj_xgf_ev_per60 asc) as `EV Offense`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by adj_xga_ev_per60 desc) as `EV Defense`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by adj_xg_pp_diff_per60 asc) as `PP`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by adj_xg_sh_diff_per60 asc) as `PK`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by gae_per60 asc) as `Finishing`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by goals_per60 asc)  as `Gx60`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by a1_per60 asc)  as `A1x60`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by minor_pim_diff_per60 asc)  as `Penalty`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xgoals_per60 asc)  as `XGx60`
--/**
 -- rankings (per 60)
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_ev_diff asc) as `EV XG 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xgf_ev asc) as `EV Offense 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xga_ev_per60 desc) as `EV Defense 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_pp_diff asc) as `PP 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_sh_diff asc) as `PK 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by gae asc) as `Finishing 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by a1_per60 asc)  as `A1x60 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by minor_pim_diff asc)  as `Penalty 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by goals_per60 asc)  as `Gx60 2`

--**/
  ,'tbd' as `Competition`
  ,'tbd' as `Teammates`
  -- time on ice
  ,season_ct
  ,gp
  ,toi_m
  ,ev_toi_m
  ,pp_toi_m
  ,sh_toi_m
  ,avg_toi_m
  ,avg_ev_toi_m
  ,avg_pp_toi_m
  ,avg_sh_toi_m
  -- all strength states
  ,xg_diff
  ,xgf
  ,xga
  ,gae
  ,gae_per60
  ,goals
  ,goals_per60
  ,a1
  ,a1_per60
  ,minor_pim_diff_per60
  -- even strength per60
  ,xg_ev_diff_per60
  ,adj_xg_ev_diff_per60
  ,xgf_ev_per60
  ,adj_xgf_ev_per60
  ,xga_ev_per60
  ,adj_xga_ev_per60
  -- even strength totals
  ,xg_ev_diff
  ,xgf_ev
  ,xga_ev
  -- powerplay per60
  ,xg_pp_diff_per60
  ,adj_xg_pp_diff_per60
  ,xgf_pp_per60
  ,adj_xgf_pp_per60
  ,xga_pp_per60
  ,adj_xga_pp_per60
  -- powerplay totals
  ,xg_pp_diff
  ,xgf_pp
  ,xga_pp
  -- shorthanded per60
  ,xg_sh_diff_per60
  ,adj_xg_sh_diff_per60
  ,xgf_sh_per60
  ,adj_xgf_sh_per60
  ,xga_sh_per60
  ,adj_xga_sh_per60
  -- shorthanded totals
  ,xg_sh_diff
  ,xgf_sh
  ,xga_sh
from
  stats as s
  left join nhl-breakouts.analytics_intermediate.d_players as p
    on p.player_id = s.player_id
  left join current_team as t
    on p.player_id = t.player_id
)

/**
-- qa query
select
  player_name
  ,primary_position_type
  -- rankings (raw_)
  ,round(avg_toi_m, 1) as avg_toi_m
  ,round(avg_ev_toi_m, 1) as avg_ev_toi_m
  ,round(avg_pp_toi_m, 1) avg_pp_toi_m
  ,round(avg_sh_toi_m, 1) avg_sh_toi_m
  -- shorthanded per60
  ,xg_sh_diff_per60
  ,adj_xg_sh_diff_per60
  ,xgf_sh_per60
  ,adj_xgf_sh_per60
  ,xga_sh_per60
  ,adj_xga_sh_per60
  -- powerplay per60
  ,xg_pp_diff_per60
  ,adj_xg_pp_diff_per60
  ,xgf_pp_per60
  ,adj_xgf_pp_per60
  ,xga_pp_per60
  ,adj_xga_pp_per60
  -- even strength per60
  ,xg_ev_diff_per60
  ,adj_xg_ev_diff_per60
  ,xgf_ev_per60
  ,adj_xgf_ev_per60
  ,xga_ev_per60
  ,adj_xga_ev_per60
  -- time on ice
  ,season_ct
  ,gp
  ,round(toi_m, 0) as toi_m
  ,round(ev_toi_m, 0) as ev_toi_m
  ,round(pp_toi_m, 0) as pp_toi_m
  ,round(sh_toi_m, 0) as sh_toi_m
  ,avg_toi_m
  ,avg_ev_toi_m
  ,avg_pp_toi_m
  ,avg_sh_toi_m
  -- all strength states
  ,xg_diff
  ,xgf
  ,xga
  ,gae
  ,gae_per60
  ,goals
  ,goals_per60
  ,a1
  ,a1_per60
  ,minor_pim_diff_per60
  -- even strength totals
  ,xg_ev_diff
  ,xgf_ev
  ,xga_ev
  -- powerplay totals
  ,xg_pp_diff
  ,xgf_pp
  ,xga_pp
  -- shorthanded totals
  ,xg_sh_diff
  ,xgf_sh
  ,xga_sh
from percentiles
where season_window = 'Last 3 seasons'
order by 7 asc
;
**/

select *
from percentiles
order by 5 desc, 4 desc, 21 desc;

