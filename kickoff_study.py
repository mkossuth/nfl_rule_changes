# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import re
import numpy as np


def get_kick_distance(kick, kick_history_dict):
    """get kickoff distance."""
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
    return kick_history_dict


def clean_kick_row(kick, kick_loc, yards_loc):
    """Clean kick row for extraneous sentences."""
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
        kick_loc = [m.end() for m in re.finditer("kicks", kick)]
        yards_loc = [m.start() for m in re.finditer("yard", kick)]
        period_loc = [m.start() for m in re.finditer("\.", kick)]
        period_loc = np.array(period_loc)
        period_loc = period_loc[period_loc > kick_loc[0]]    
    return kick, kick_loc, yards_loc, period_loc


def get_kickoff_location(kick, kick_history_dict):
    """Get kickoff location and return line and team side."""
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
        

def get_touchback_info(kick, kick_history_dict, data, idx):
    """Get touchback info and return kick_history_dict."""
    kick_history_dict["touchback"] = 1
    kick_history_dict["kick_ret_yd_line"] \
        = "{} {}".format(data.loc[idx, "def"], 20)
    kick_history_dict["to_tm_yd"] = kick_history_dict["def"]
    kick_history_dict["to_yd_line"] \
        = 100 - (kick_history_dict["from_yd_line"]
        + kick_history_dict["kick_dist"])
    kick_history_dict["kick_ret_dist"] = 0
    return kick_history_dict
      
# TODO look at results of drive to see how often score based on kickoff
# TODO need to consider multiple things happening on kickoff, so can't use elif
# TODO need to do if statements for all tests
data = pd.read_csv("2002_nfl_pbp_data.csv")
kick_history_df = pd.DataFrame(
    columns=["gameid", "season", "qtr", "min", "sec",
             "off", "def", "description",
             "offscore", "defscore",
             "from_yd", "from_tm_yd", "from_yd_line",
             "to_yd", "to_tm_yd", "to_yd_line",
             "kick_dist", "kick_ret_dist", "kick_ret_yd_line",
             "onside",
             "touchdown",
             "fumble",
             "ran_ob",
             "pushed_ob",
             "kicked_ob",
             "fair_catch",
             "turnover",
             "touchback"])
for idx, kick_row in data[
        data["description"].str.contains(r"^(?=.*kicks)")
        ].iterrows():
    kick_row = kick_row.drop(["down", "togo", "ydline"])
    kick = kick_row.description
    #  Check if kick off touchdown #(?=.*TOUCHDOWN)")
    if kick.lower().find("onside") != -1:
        pass
        #print("Onside")
        #print(kick)
    elif kick.lower().find("penalty") != -1:
        pass
        #print("penalty")
        #print(kick)
    elif kick.lower().find("fumble") != -1 or kick.lower().find("muff") != -1:
        pass
        #print("fumble")
        #print(kick)
    elif kick.lower().find("field goal") != -1:
        pass
        #print("random field goal issue")
        #print(kick)
    elif kick.lower().find("lateral") != -1:
        pass
        #print("lateral")
        #print(kick)
    elif kick.lower().find("touchdown") != -1:
        print("touchdown")
        print(kick)
    else:
        kick_history_dict = initialize_kickoff_dictionary()
        kick_history_dict, kick_loc, yards_loc \
            = get_kick_distance(kick, kick_history_dict)
        # Clean up kick row info
        kick, kick_loc, yards_loc, period_loc \
            = clean_kick_row(kick, kick_loc, yards_loc)
        if kick.lower().find("fair catch") != -1:
            period_loc = [m.start() for m in re.finditer("fair catch", kick)]
        to_loc_end = [m.end() for m in re.finditer(" to ", kick)]
        # Get kick off line information
        kick_history_dict = get_kickoff_location(kick, kick_history_dict)
        # Get kick off destination information
        kick_history_dict["to_yd"] = kick[to_loc_end[0]:(period_loc[0])]
        # Check for a touchback
        if kick.lower().find("touchback") != -1:
            kick_history_dict = get_touchback_info(
                kick, kick_history_dict, data, idx
            )
        elif kick.lower().find("out of bounds") != -1:
            if data.loc[idx+1, "ydline"] > 50:
                kick_history_dict["kick_ret_yd_line"] \
                    = "{} {}".format(
                        data.loc[idx+1, "off"],
                        100 - data.loc[idx+1, "ydline"]
                    )
            else:
                kick_history_dict["kick_ret_yd_line"] \
                    = "{} {}".format(
                        data.loc[idx+1, "def"],
                        data.loc[idx+1, "ydline"]
                    )
        elif kick.lower().find("touchdown") != -1:
            pass
            
        else:
            [
                kick_history_dict["to_tm_yd"],
                kick_history_dict["to_yd_line"]
            ] = str.split(kick_history_dict["to_yd"])
            kick_history_dict["to_yd_line"] \
                = int(kick_history_dict["to_yd_line"])
            kick_history_dict["touchback"] = 0
            for_loc_start = [m.start() for m in re.finditer(" for ", kick)]
            for_loc_end = [m.end() for m in re.finditer(" for ", kick)]
            if kick.lower().find("fair catch") != -1:
                kick_history_dict["kick_ret_dist"] = 0
                kick_history_dict["kick_ret_yd_line"] \
                    = kick_history_dict["to_yd"]
                kick_history_dict["fair_catch"] = 1
            elif kick.lower().find("no gain") != -1:
                kick_history_dict["kick_ret_dist"] = 0
                kick_history_dict["kick_ret_yd_line"] \
                    = kick[to_loc_end[0]:(period_loc[0])]
            elif kick.lower().find(" ob") != -1:
                at_loc_end = [m.end() for m in re.finditer(" at ", kick)]
                kick_history_dict["kick_ret_yd_line"] \
                    = kick[at_loc_end[0]:for_loc_start[0]]
            else:
                kick_history_dict["kick_ret_dist"] \
                    = int(kick[for_loc_end[0]:(yards_loc[1])])
                kick_history_dict["kick_ret_yd_line"] \
                    = kick[to_loc_end[1]:for_loc_start[0]]
        if kick_history_dict["kick_ret_yd_line"] == "50":
            kick_history_dict["kick_ret_tm_yd"] = "NA"
            kick_history_dict["kick_ret_line"] = 50
        else:
            [
                kick_history_dict["kick_ret_tm_yd"],
                kick_history_dict["kick_ret_line"]
            ] = str.split(kick_history_dict["kick_ret_yd_line"])       
        kick_history_dict["onside"] = 0
        kick_history_dict["touchdown"] = 0
        kick_history_dict["fumble"] = 0
        kick_history_dict["turnover"] = 0
        if kick.lower().find("ran ob") != -1:
            kick_history_dict["ran_ob"] = 1
        if kick.lower().find("pushed ob") != -1:
            kick_history_dict["pushed_ob"] = 1
        if kick.lower().find("out of bounds") != -1:
            kick_history_dict["kicked_ob"] = 1
        kick_history_df = kick_history_df.append(
            pd.Series(kick_history_dict), ignore_index=True
        )
