import os

import pandas as pd

from .data_locations import t2_dir


class T2Data:
    @staticmethod
    def get_tm_lineups():
        return _get_df("tm_lineups")

    @staticmethod
    def get_tm_matches():
        return _get_df("tm_matches")

    @staticmethod
    def get_tm_player_df():
        return _get_df("tm_player_df")

    @staticmethod
    def get_wh_season_df():
        return _get_df("wh_season_df")

    @staticmethod
    def get_wh_team_df():
        return _get_df("wh_team_df")

    @staticmethod
    def get_formation_df():
        return _get_df("formation_df")

    @staticmethod
    def get_wh_player_df():
        return _get_df("wh_player_df")

    @staticmethod
    def get_formation_use_df():
        return _get_df("formation_use_df")

    @staticmethod
    def get_mv_df():
        return _get_df("mv_df")

    @staticmethod
    def get_match_df():
        return _get_df("match_df")

    @staticmethod
    def get_transfer_df():
        return _get_df("transfer_df")

    @staticmethod
    def get_attendance_df():
        return _get_df("attendance_df")

    @classmethod
    def get_simplified_wh_matches(cls):
        match_df = cls.get_match_df()

        team_ser = cls.get_wh_team_df().set_index("teamId")["name"]

        return match_df.assign(
            fulltime_score=lambda df: df["home_goals_ft"].astype(int).astype(str)
            + " : "
            + df["away_goals_ft"].astype(int).astype(str),
            date=lambda df: df["datetime"].dt.date,
            home_team=lambda df: team_ser.reindex(df["home_teamid"]).values,
            away_team=lambda df: team_ser.reindex(df["away_teamid"]).values,
        ).loc[:, ["home_team", "away_team", "fulltime_score", "date", "wh_match_id"]]


def reduce_append(df1, df2):
    if isinstance(df1, str):
        df1 = pd.read_parquet(df1)
    if isinstance(df2, str):
        df2 = pd.read_parquet(df2)
    return df1.append(df2)


def get_season_events(season_id):
    for comp_type in ["league", "cup"]:
        try:
            return pd.read_parquet(
                os.path.join(t2_dir, "events", comp_type, f"{season_id}.parquet")
            ).set_index("id")
        except OSError:
            continue


def _get_df(df_id):
    return pd.read_parquet(os.path.join(t2_dir, f"{df_id}.parquet"))
