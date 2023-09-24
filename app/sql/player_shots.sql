select
  play_id,
  game_id,
  event_id,
  team_id,
  player_id,
  player_full_name as player_name,
  event_type,
  event_description,
  play_period,
  play_total_seconds_elapsed,
  play_x_coordinate as x_coord,
  play_y_coordinate as y_coord,
  play_distance,
  play_angle,
  rink_side,
  zone_type,
  zone,
  game_state,
  game_state_skaters,
  xg_strength_state_code,
  xg_model_id,
  xg_proba,
  x_goal

from nhl-breakouts.analytics_intermediate.f_plays
where 1 = 1
  and left(cast(game_id as string), 6) in ('202202') -- new
  and player_full_name in ('Connor McDavid', 'Auston Matthews', 'Alex Ovechkin', 'Sidney Crosby', 'Jack Eichel', 'Cale Makar', 'Leon Draisaitl', 'Erik Karlsson')
  and lower(play_period_type) != 'shootout'
  and lower(player_role) in ('scorer', 'shooter')
  and xg_proba is not null
;
