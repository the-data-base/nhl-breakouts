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

,players as (
  select
    f.play_id,
    f.game_id,
    right(left(cast(f.game_id as string), 6), 2) as game_type,
    f.event_id,
    f.team_id,
    f.player_id,
    player_full_name as player_name,
    t.team_full_name as current_team_full_name,
    t.team_name as current_team_name,
    t.team_code as current_team_code,
    f.event_type,
    f.event_description,
    f.play_period,
    f.play_total_seconds_elapsed,
    f.play_x_coordinate as x_coord,
    f.play_y_coordinate as y_coord,
    f.play_distance,
    f.play_angle,
    f.rink_side,
    f.zone_type,
    f.zone,
    f.game_state,
    f.game_state_skaters,
    f.xg_strength_state_code,
    f.xg_model_id,
    f.xg_proba,
    f.x_goal

  from nhl-breakouts.analytics_intermediate.f_plays as f
  left join current_team as t on t.player_id = f.player_id
  where 1 = 1
    and left(cast(f.game_id as string), 6) in ('202202') -- new
    --and f.player_full_name in ('Connor McDavid', 'Auston Matthews', 'Alex Ovechkin', 'Sidney Crosby', 'Jack Eichel', 'Cale Makar', 'Leon Draisaitl', 'Cale Makar', 'Erik Karlsson', 'Jack Hughes', 'Elias Pettersson', 'Patrice Bergeron', 'Nathan MacKinnon', 'Matthew Tkachuk')
    and lower(f.play_period_type) != 'shootout'
    and lower(f.player_role) in ('scorer', 'shooter')
    and f.xg_proba is not null
  )

select * from players;
