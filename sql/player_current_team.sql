select
 distinct s.player_team_season_id
 ,s.player_id
 ,s.team_id
 ,s.season_id
 ,t.abbreviation as team_code
from nhl-breakouts.dbt_dom.d_player_team_season as s
left join nhl-breakouts.dbt_dom.d_teams as t on t.team_id = s.team_id
where is_player_current_team is True
qualify row_number() over (partition by player_id order by player_season_team_last_dt desc) = 1
;
