-- Goal: re-create Jfresh percentile ranks
--... query the top percentile forwards in the NHL over the past 3 seasons

with
-- the player's current team
current_team as (
select
 distinct s.player_team_season_id
 ,s.player_id
 ,s.team_id
 ,s.season_id
 ,t.abbreviation as team_code
 ,t.full_name as team_full_name
 ,t.team_name
from nhl-breakouts.dbt_dom.d_player_team_season as s
left join nhl-breakouts.dbt_dom.d_teams as t on t.team_id = s.team_id
where is_player_current_team is True
qualify row_number() over (partition by player_id order by player_season_team_last_dt desc) = 1
)



-- current-season-stats
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
-- sum features
  ,sum(boxscore_games) as gp
  ,sum(time_on_ice_seconds) as toi_s
  ,sum(time_on_ice_minutes) as toi_m
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
-- per60 features
  ,round((sum(minor_pim_drawn) - sum(minor_pim_taken)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as minor_pim_diff_per60
  ,round((sum(shots_iscored) - sum(penalty_shot_goals) - sum(empty_net_goals)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgoals_per60
  ,round((sum(goals) / ((sum(time_on_ice_minutes) + 500) / 60)),2) as goals_per60
  ,round((sum(shots_iscored) - sum(shots_ixg)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as gae_per60
  ,round((sum(assists_primary) / ((sum(time_on_ice_minutes) + 500) / 60)),2) as a1_per60
  ,round((sum(shots_xgf) - sum(shots_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_diff_per60
  ,round(sum(shots_ev_xgf) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgf_ev_per60
  ,round(sum(shots_ev_xga) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xga_ev_per60
  ,round((sum(shots_ev_xgf) - sum(shots_ev_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_ev_diff_per60
  ,round(sum(shots_pp_xgf) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgf_pp_per60
  ,round(sum(shots_pp_xga) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xga_pp_per60
  ,round((sum(shots_pp_xgf) - sum(shots_pp_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_pp_diff_per60
  ,round(sum(shots_sh_xgf) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgf_sh_per60
  ,round(sum(shots_sh_xga) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xga_sh_per60
  ,round((sum(shots_sh_xgf) - sum(shots_sh_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_sh_diff_per60
from
  nhl-breakouts.dbt_dom.f_player_season as s
where 1 =1
  and game_type = '02'
  and cast(season_id as int64) in (20202021, 20212022, 20222023)
group by 1, 2, 3, 4, 5
having 1 = 1
  and sum(time_on_ice_minutes) > 450
  and sum(boxscore_games) > 30
  and avg(avg_time_on_ice_mins) > 6
  and sum(case when cast(season_id as int64) = 20222023 then shots_iff else 0 end) > 10

)
-- current-season-stats
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
-- sum features
  ,sum(boxscore_games) as gp
  ,sum(time_on_ice_seconds) as toi_s
  ,sum(time_on_ice_minutes) as toi_m
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
-- per60 features
  ,round((sum(minor_pim_drawn) - sum(minor_pim_taken)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as minor_pim_diff_per60
  ,round((sum(shots_iscored) - sum(penalty_shot_goals) - sum(empty_net_goals)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgoals_per60
  ,round((sum(goals) / ((sum(time_on_ice_minutes) + 500) / 60)),2) as goals_per60
  ,round((sum(shots_iscored) - sum(shots_ixg)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as gae_per60
  ,round((sum(assists_primary) / ((sum(time_on_ice_minutes) + 500) / 60)),2) as a1_per60
  ,round((sum(shots_xgf) - sum(shots_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_diff_per60
  ,round(sum(shots_ev_xgf) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgf_ev_per60
  ,round(sum(shots_ev_xga) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xga_ev_per60
  ,round((sum(shots_ev_xgf) - sum(shots_ev_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_ev_diff_per60
  ,round(sum(shots_pp_xgf) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgf_pp_per60
  ,round(sum(shots_pp_xga) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xga_pp_per60
  ,round((sum(shots_pp_xgf) - sum(shots_pp_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_pp_diff_per60
  ,round(sum(shots_sh_xgf) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xgf_sh_per60
  ,round(sum(shots_sh_xga) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xga_sh_per60
  ,round((sum(shots_sh_xgf) - sum(shots_sh_xga)) / ((sum(time_on_ice_minutes) + 500) / 60),2) as xg_sh_diff_per60
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
  and avg(avg_time_on_ice_mins) > 6
  and sum(shots_iff) > 10

)

-- union together
,raw_stats as (
  select * from current_stats
  union all
  select * from season_stats
)

-- percentiles
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
  -- rankings (raw_)
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by avg_toi_m asc)  as `Avg TOI`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by toi_s asc)  as `TOI`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_ev_diff_per60 asc) as `EV XG`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xgf_ev_per60 asc) as `EV Offense`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xga_ev_per60 desc) as `EV Defense`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_pp_diff_per60 asc) as `PP`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_sh_diff_per60 asc) as `PK`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by gae_per60 asc) as `Finishing`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by goals_per60 asc)  as `Gx60`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xgoals_per60 asc)  as `XGx60`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by a1_per60 asc)  as `A1x60`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by minor_pim_diff_per60 asc)  as `Penalty`
--/**
 -- rankings (raw except defense)
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_ev_diff asc) as `EV XG 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xgf_ev asc) as `EV Offense 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xga_ev_per60 desc) as `EV Defense 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_pp_diff asc) as `PP 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by xg_sh_diff asc) as `PK 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by gae asc) as `Finishing 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by goals_per60 asc)  as `Gx60 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by a1_per60 asc)  as `A1x60 2`
  ,100*percent_rank() over (partition by primary_position_type, game_type, season, season_window order by minor_pim_diff asc)  as `Penalty 2`
--**/
  ,'tbd' as `Competition`
  ,'tbd' as `Teammates`
  -- raw features
  ,gp
  ,xg_diff
  ,xg_ev_diff
  ,xgf_ev
  ,xga_ev
  ,xg_pp_diff
  ,xg_sh_diff
  ,gae
  ,goals_per60
  ,a1_per60
  ,xgf
  ,xga
  ,goals
  ,a1
  ,toi_m
  ,avg_toi_m
  ,xg_ev_diff_per60
  ,xgf_ev_per60
  ,xga_ev_per60
  ,xg_pp_diff_per60
  ,xg_sh_diff_per60
  ,gae_per60
  ,minor_pim_diff_per60

from
  raw_stats as s
  left join nhl-breakouts.analytics_intermediate.d_players as p
    on p.player_id = s.player_id
  left join current_team as t
    on p.player_id = t.player_id
)

select *
from percentiles
order by 5 desc, 4 desc, 20 desc;
