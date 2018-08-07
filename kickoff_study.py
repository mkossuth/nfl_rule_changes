# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import glob
import pandas as pd
import re
import numpy as np


def get_kick_distance(kick_history_dict):
    """get kickoff distance."""
    if "kick" in kick_history_dict:
        kick = kick_history_dict["kick"]
    else:
        kick = kick_history_dict["description"]
    if kick.lower().find("kicks onside") != -1:
        kick_loc = [m.end() for m in re.finditer("kicks onside", kick)]
        kick_history_dict["onside_kick"] = 1
    else:
        kick_loc = [m.end() for m in re.finditer("kicks", kick)]
    yards_loc = [m.start() for m in re.finditer("yard", kick)]
    yards_loc = [idx for idx in yards_loc if idx > kick_loc[0]]
    kick_dist = int(kick[kick_loc[0]:(yards_loc[0] - 1)])
    kick_history_dict["kick_dist"] = kick_dist
    return kick_history_dict, kick_loc, yards_loc


def initialize_kickoff_dictionary():
    """Initialize the kickoff dictionary."""
    kick_history_dict = kick_row.to_dict()
    # set initial value for kick return line to know if filled before
    # treating as a regular kick
    kick_history_dict["kick_ret_yd_line"] = -1
    kick_history_dict["fair_catch"] = 0
    kick_history_dict["pushed_ob"] = 0
    kick_history_dict["kicked_ob"] = 0
    kick_history_dict["ran_ob"] = 0
    kick_history_dict["touchback"] = 0
    kick_history_dict["touchdown"] = 0
    kick_history_dict["onside_kick"] = 0
    kick_history_dict["onside_success"] = 0
    kick_history_dict["fumble"] = 0
    kick_history_dict["turnover"] = 0
    kick_history_dict["lateral"] = 0
    kick_history_dict["no_play"] = 0
    return kick_history_dict


def index_kick_row(kick):
    """Index the kick row for kick_loc, yards_loc and period_loc."""
    kick_loc = [m.end() for m in re.finditer("kicks", kick)]
    yards_loc = [m.start() for m in re.finditer("yard", kick)]
    period_loc = [m.start() for m in re.finditer("\.", kick)]
    period_loc = np.array(period_loc)
    period_loc = period_loc[period_loc > kick_loc[0]]
    return kick, kick_loc, yards_loc, period_loc


def get_challenge_info(kick_history_dict):
    """Get challenge info."""
    kick = kick_history_dict["kick"]
    if kick.lower().find("play challenged") != -1:
        # Play was challenged.  Need to clean up for that
        kick_history_dict["challenge"] = 1
        challenge_idx = [
            m.start() for m in re.finditer("play challenged", kick.lower())
        ]
        if kick.lower().find("reversed") != -1:
            # Play reversed.
            kick_history_dict["reversed"] = 1
            reverse_idx = [
                m.end() for m in re.finditer("reversed.", kick.lower())
            ]
            kick_history_dict["kick"] = kick[reverse_idx[0]:]
        else:
            kick_history_dict["reversed"] = 0
            kick_history_dict["kick"] = kick[:challenge_idx[0]]
    return kick_history_dict


def clean_kick_row(kick, kick_loc, yards_loc):
    """Clean kick row for extraneous sentences."""
    # Remove extraneous commentary on laterals
    if kick.lower().find("didn't try to advance") != -1:
        kick = kick.replace("didn't try to advance", "")
        kick, kick_loc, yards_loc, period_loc = index_kick_row(kick)
    period_loc = [m.start() for m in re.finditer("\.", kick)]
    period_loc = np.array(period_loc)
    sum_period_loc = np.sum(period_loc < kick_loc[0])
    first_item_loc \
        = period_loc[np.max(np.where(period_loc < kick_loc[0]))] - 1
    period_loc = period_loc[period_loc > kick_loc[0]]
    if sum_period_loc > 1:
        # Need to clean up values in case there is some random sentence
        # before kick off info
        kick = kick[first_item_loc:]
        kick, kick_loc, yards_loc, period_loc = index_kick_row(kick)
    return kick, kick_loc, yards_loc, period_loc


def get_kickoff_location(kick_history_dict):
    """Get kickoff location and return line and team side."""
    kick = kick_history_dict["kick"]
    from_loc_end = [m.end() for m in re.finditer("from", kick)]
    to_loc_start = [m.start() for m in re.finditer(" to ", kick)]
    kick_from_tmyd = kick[from_loc_end[0]:(to_loc_start[0])]
    [kick_from_tm_yd, kick_from_yd_line] \
        = str.split(kick_from_tmyd)
    kick_from_yd_line = int(kick_from_yd_line)
    kick_history_dict["from_yd"] = kick_from_tmyd
    kick_history_dict["from_tm_yd"] = kick_from_tm_yd
    kick_history_dict["from_yd_line"] = kick_from_yd_line
    return kick_history_dict


def get_touchback_info(kick_history_dict, data, idx):
    """Get touchback info and return kick_history_dict."""
    kick_history_dict["touchback"] = 1
    kick_history_dict["kick_ret_yd_line"] \
        = "{} {}".format(data.loc[idx, "def"], 20)
    kick_history_dict["to_tm_yd"] = kick_history_dict["def"]
    kick_history_dict["to_yd_line"] \
        = 100 - (
            kick_history_dict["from_yd_line"] + kick_history_dict["kick_dist"]
        )
    kick_history_dict["kick_ret_dist"] = 0
    kick_history_dict = parse_kick_return_info(kick_history_dict)
    return kick_history_dict


def get_out_of_bounds_info(kick_history_dict, data, idx):
    """Get out of bounds return yard line and return kick_history_dict."""
    # Remove 'out of bounds' from to_yd variable
    kick_history_dict["to_yd"] \
        = kick_history_dict["to_yd"].replace("out of bounds", "")
    kick_history_dict = split_to_yard_line_info(kick_history_dict)
    if data.loc[idx+1, "ydline"] > 50:
        kick_history_dict["kick_ret_yd_line"] \
            = "{} {}".format(
                data.loc[idx+1, "off"],
                int(100 - data.loc[idx+1, "ydline"])
            )
    else:
        kick_history_dict["kick_ret_yd_line"] \
            = "{} {}".format(
                data.loc[idx+1, "def"],
                data.loc[idx+1, "ydline"]
            )
    return kick_history_dict


def get_fair_catch_info(kick_history_dict):
    """Return fair catch info."""
    kick_history_dict["kick_ret_dist"] = 0
    kick_history_dict["kick_ret_yd_line"] = kick_history_dict["to_yd"]
    kick_history_dict["fair_catch"] = 1
    return kick_history_dict


def split_to_yard_line_info(kick_history_dict):
    [kick_history_dict["to_tm_yd"], kick_history_dict["to_yd_line"]] \
        = str.split(kick_history_dict["to_yd"])
    kick_history_dict["to_yd_line"] = int(kick_history_dict["to_yd_line"])
    return kick_history_dict


def split_no_gain_info(kick_history_dict, to_loc_end, period_loc):
    """Return kick info for no gain on return."""
    kick = kick_history_dict["kick"]
    kick_history_dict["kick_ret_dist"] = 0
    kick_history_dict["kick_ret_yd_line"] = kick[to_loc_end[0]:(period_loc[0])]
    return kick_history_dict


def kick_return_info(kick_history_dict,
                     to_loc_end,
                     yards_loc,
                     data,
                     idx):
    """Get kick return info, including touchdowns."""
    kick = kick_history_dict["kick"]
    for_loc_start, for_loc_end = find_for_in_desc(kick)
    kick_history_dict["kick_ret_dist"] \
        = int(kick[for_loc_end[0]:(yards_loc[1])])
    if kick.lower().find("touchdown") != -1:
        kick_history_dict["touchdown"] = 1
        kick_history_dict["kick_ret_yd_line"] \
            = "{} {}".format(data.loc[idx, "off"], 0)
    else:
        kick_history_dict["touchdown"] = 0
        kick_history_dict["kick_ret_yd_line"] \
            = kick[to_loc_end[1]:for_loc_start[0]]
    kick_history_dict = parse_kick_return_info(kick_history_dict)
    return kick_history_dict


def parse_kick_return_info(kick_history_dict):
    """Parse kick return info, watching for 50 yard line."""
    if kick_history_dict["kick_ret_yd_line"] == "50":
        kick_history_dict["kick_ret_tm_yd"] = "NA"
        kick_history_dict["kick_ret_line"] = 50
    else:
        try:
            [
                kick_history_dict["kick_ret_tm_yd"],
                kick_history_dict["kick_ret_line"]
            ] = str.split(kick_history_dict["kick_ret_yd_line"])
        except ValueError:
            print(kick_history_dict["kick_ret_yd_line"])
    return kick_history_dict


def split_ob_info(kick_history_dict):
    """Record out of bounds info then change 'ob at' to 'to'."""
    kick = kick_history_dict["kick"]
    if kick.lower().find("ran ob") != -1:
        kick_history_dict["ran_ob"] = 1
    if kick.lower().find("pushed ob") != -1:
        kick_history_dict["pushed_ob"] = 1
    kick_history_dict["kick"] = kick.replace("ob at", "to")
    return kick_history_dict


def find_for_in_desc(kick):
    """Find the word for in the play description."""
    for_loc_start = [m.start() for m in re.finditer(" for ", kick)]
    for_loc_end = [m.end() for m in re.finditer(" for ", kick)]
    return for_loc_start, for_loc_end


def get_penalty_info(kick_history_dict):
    """Get penalty information."""
    kick = kick_history_dict["kick"]
    penalty_idx = [m.start() for m in re.finditer("penalty on ", kick.lower())]
    kick_penalty = kick[penalty_idx[0]:]
    no_play_test = kick.lower().find("no play") != -1
    declined_test = kick.lower().find("declined") != -1
    offsetting_test = kick.lower().find("offset") != -1
    if not no_play_test and not declined_test and not offsetting_test:
        # This penalty was a valid play, so parse the penalty information
        # First, keep only the penalty sentence
        enforced_idx = [
            m.end() for m in re.finditer("enforced at", kick_penalty.lower())
        ]
        period_idx = [
            m.start() for m in re.finditer("\.", kick_penalty.lower())
        ]
        period_idx = [idx for idx in period_idx if idx > enforced_idx[0]]
        kick_penalty = kick_penalty[:period_idx[0]]
        space_idx = [m.start() for m in re.finditer(" ", kick_penalty.lower())]
        dash_idx = [m.start() for m in re.finditer("-", kick_penalty.lower())]
        if dash_idx:
            pen_team_idx = np.min((space_idx[0], dash_idx[0]))
        else:
            pen_team_idx = space_idx[0]
        pen_team = kick_penalty[penalty_idx[0]:pen_team_idx]
        # Add space here so penalty yards is defined by space_idx and yards_loc
        yards_loc = [
            m.start() for m in re.finditer(" yards ", kick_penalty.lower())
        ]
        yards_start_idx = [
            idx for idx in space_idx if yards_loc[0] - idx > 1
        ][-1]
        kick_history_dict["penalty_yards"] = int(
            kick_penalty[yards_start_idx:yards_loc[0]]
        )
        enforced_yard = kick_penalty[enforced_idx[0]:]
        kick_history_dict["penalty_loc"] = enforced_yard
        [
            kick_history_dict["penalty_tm_yd"],
            kick_history_dict["penalty_line"]
        ] = kick_history_dict["penalty_loc"].split()
        if pen_team.lower() == kick_history_dict["def"].lower():
            # Penalty on receiving team, so yardage will be backwards
            kick_history_dict["penalty_on"] = "def"
        else:
            # Penalty on kicking team, so yardage will be moved forward
            kick_history_dict["penalty_on"] = "off"
        kick_history_dict["penalty_on"] = pen_team
    elif no_play_test:
        kick_history_dict["penalty_no_play"] = 1
    elif declined_test:
        kick_history_dict["penalty_declined"] = 1
    elif offsetting_test:
        kick_history_dict["penalty_offset"] = 1
    return kick_history_dict


def get_fumble_info(kick_history_dict):
    """Get fumble/muff info and return kick_history_dict."""
    kick = kick_history_dict["kick"]
    kick_history_dict["fumble"] = 1
    challenge_test = kick.lower().find("challenge") != -1
    turnover_test = kick.find("RECOVERED") != -1
    if not challenge_test:
        kick_history_dict["kick_ret_yd_line"] = "FUM -1"
        if turnover_test:
            # Other team has recovered the ball
            kick_history_dict["turnover"] = 1
    return kick_history_dict


def get_lateral_info(kick_history_dict):
    """Get lateral results and replace final return into kick return info"""
    kick = kick_history_dict["kick"]
    kick_history_temp = kick_history_dict
    lateral_idx = [m.end() for m in re.finditer(" Lateral to", kick)]
    for idx in lateral_idx:
        kick_temp = kick[idx:]
        to_loc_end = [m.end() for m in re.finditer(" to ", kick_temp)]
        for_loc_start, for_loc_end = find_for_in_desc(kick_temp)
        yards_loc = [m.start() for m in re.finditer("yard", kick_temp)]
        kick_history_temp["kick_ret_yd_line"] \
            = kick_temp[to_loc_end[0]:for_loc_start[0]]
        kick_ret_dist = int(kick_temp[for_loc_end[0]:(yards_loc[0])])
        kick_history_dict["kick_ret_dist"] += kick_ret_dist
        kick_history_temp = parse_kick_return_info(kick_history_temp)
        # If ball is on defenders side
        if kick_history_temp["kick_ret_tm_yd"] == kick_history_temp["def"]:
            # But if it was run backwards over the 50
            if (kick_history_temp["kick_ret_tm_yd"]
                    != kick_history_dict["kick_ret_tm_yd"]):
                kick_history_dict["kick_ret_tm_yd"] \
                    = kick_history_temp["kick_ret_tm_yd"]
                kick_history_dict["kick_ret_line"] \
                    = kick_history_temp["kick_ret_line"]
            else:  # Ball still on same side
                kick_history_dict["kick_ret_line"] \
                    = np.max(
                        (
                            int(kick_history_temp["kick_ret_line"]),
                            int(kick_history_dict["kick_ret_line"])
                        )
                    )
    return kick_history_dict


# TODO look at results of drive to see how often score based on kickoff
# TODO need to consider multiple things happening on kickoff, so can't use elif
# TODO need to do if statements for all tests
kick_history_df = pd.DataFrame(
    columns=["gameid", "season", "qtr", "min", "sec",
             "off", "def", "description",
             "offscore", "defscore",
             "from_yd", "from_tm_yd", "from_yd_line",
             "to_yd", "to_tm_yd", "to_yd_line",
             "kick_dist", "kick_ret_dist",
             "kick_ret_yd_line", "kick_ret_line", "kick_ret_tm_yd",
             "onside_kick",
             "onside_success",
             "touchdown",
             "fumble",
             "ran_ob",
             "pushed_ob",
             "kicked_ob",
             "fair_catch",
             "turnover",
             "touchback",
             "lateral"]
)
kick_history_to_do = kick_history_df.copy()
for f_name in glob.glob("*nfl_pbp_data.csv"):
    data = pd.read_csv(f_name)
    for idx, kick_row in data[
            data["description"].str.contains(r"^(?=.*kicks)")
            ].iterrows():
        kick_row = kick_row.drop(["down", "togo", "ydline"])
        kick = kick_row.description
        try:
            kick_history_dict = initialize_kickoff_dictionary()
            kick_history_dict, kick_loc, yards_loc \
                = get_kick_distance(kick_history_dict)
            # Clean up kick row info
            kick, kick_loc, yards_loc, period_loc \
                = clean_kick_row(kick, kick_loc, yards_loc)
            # Remove ob text
            if kick.lower().find(" ob") != -1:
                kick_history_dict["kick"] = kick
                kick_history_dict = split_ob_info(kick_history_dict)
                kick = kick_history_dict["kick"]
                kick, kick_loc, yards_loc, period_loc = index_kick_row(kick)
            kick_history_dict["kick"] = kick
            if kick.lower().find("challenge") != -1:
                kick_history_dict = get_challenge_info(kick_history_dict)
            if kick.lower().find("fair catch") != -1:
                period_loc = [
                    m.start() for m in re.finditer("fair catch", kick)
                ]
            to_loc_end = [m.end() for m in re.finditer(" to ", kick)]
            # Get kick off line information
            kick_history_dict = get_kickoff_location(kick_history_dict)
            # Get kick off destination information
            kick_history_dict["to_yd"] = kick[to_loc_end[0]:(period_loc[0])]
            # Check for a touchback
            if kick.lower().find("touchback") != -1:
                kick_history_dict["touchback"] = 1
                kick_history_dict = get_touchback_info(
                    kick_history_dict, data, idx
                )
            elif kick.lower().find("out of bounds") != -1:
                kick_history_dict = get_out_of_bounds_info(
                    kick_history_dict, data, idx
                )
            elif np.logical_and(
                    kick.lower().find("onside") != -1,
                    kick.lower().find("recovered") != -1):
                # Onside kick recovered by kicking team
                kick_history_dict["onside_success"] = 1
                kick_history_dict = split_no_gain_info(
                    kick_history_dict, to_loc_end, period_loc
                )
            else:
                kick_history_dict = split_to_yard_line_info(kick_history_dict)
                if kick.lower().find("fair catch") != -1:
                    kick_history_dict = get_fair_catch_info(kick_history_dict)
                elif kick.lower().find("no gain") != -1:
                    kick_history_dict = split_no_gain_info(
                        kick_history_dict, to_loc_end, period_loc
                    )
                elif (kick.lower().find("fumble") != -1
                      or kick.lower().find("muff") != -1):
                    kick_history_dict = get_fumble_info(kick_history_dict)
                else:
                    kick_history_dict = kick_return_info(
                        kick_history_dict,
                        to_loc_end,
                        yards_loc,
                        data,
                        idx)
                    if np.logical_or(kick.lower().find("lateral") != -1,
                                     kick.lower().find("handoff") != -1):
                        kick_history_dict["lateral"] = 1
                        # Update kick return with final lateral location
                        kick_history_dict = get_lateral_info(kick_history_dict)
            if kick.lower().find("penalty") != -1:
                kick_history_dict = get_penalty_info(kick_history_dict)
            if kick.lower().find("out of bounds") != -1:
                kick_history_dict["kicked_ob"] = 1
                kick_history_dict["kick_ret_dist"] = 0
            if kick.lower().find("no play") != -1:
                kick_history_dict["no_play"] = 1
            kick_history_dict = parse_kick_return_info(kick_history_dict)
            kick_history_df = kick_history_df.append(
                pd.Series(kick_history_dict), ignore_index=True
            )
        except:
            kick_history_to_do = kick_history_to_do.append(
                pd.Series(kick_row), ignore_index=True
            )
kick_history_df.to_csv("test.csv")
kick_history_to_do.to_csv("to_do.csv")
