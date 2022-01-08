import pandas as pd

def filter_years(results, start=1872, end=2022):
    """filters the results dataset from a given range between 1872 and 2022

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        start (int, optional): lower limit of the filter range. Defaults to 1872.
        end (int, optional): upper limit of the filter range. Defaults to 2022.

    Returns:
        pd.DataFrame: filtered results dataframe
    """
    return results[f'{int(start)}-01-01':f'{int(end)}-01-01']

def filter_teams(results, teams):
    """filters the results dataset from a given list of teams

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        teams (list): list of of teams that will NOT be filtered out

    Returns:
        pd.DataFrame: filtered results dataframe
    """
    return pd.concat([results.loc[(results['home_team']==team) | (results['away_team']==team)] for team in teams])

def filter_encounter(results, team1, team2):
    """filters the results dataset for all encounters between two teams (order between teams does not matter)

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        team1 (string): name of the first team
        team2 (string): name of the second team

    Returns:
        pd.DataFrame: filtered results dataframe
    """
    return results.loc[(results['home_team']==team1) & (results['away_team']==team2) | 
                             (results['home_team']==team2) & (results['away_team']==team1)]

def get_home_match(results, team):
    """gets all matches from a single team that has been played at home

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        team (string): name of the team

    Returns:
        pd.DataFrame: dataframe containing all home_matches of the team
    """
    matches = pd.concat( [results.loc[(results['home_team']==team)]] )
    return matches

def get_away_match(results, team):
    """gets all matches from a single team that has been played away

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        team (string): name of the team

    Returns:
        pd.DataFrame: dataframe containing all away_matches of the team
    """
    matches = pd.concat( [results.loc[(results['away_team']==team)]] )
    return matches

def swap_columns(results):
    """swap home and away columns of the result dataset

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it

    Returns:
        pd.DataFrame: same dataframe with home and away columns swapped
    """
    cols = list(results.columns)
    a, b, c, d = cols.index('home_team'), cols.index('away_team'), cols.index('home_score'), cols.index('away_score')
    cols[b], cols[a], cols[c], cols[d] = cols[a], cols[b], cols[d], cols[c]
    results = results[cols]
    results = results.rename(columns={'home_team':'away_team', 'away_team':'home_team', 'home_score':'away_score', 'away_score':'home_score'})
    return results

def merge_matches(results, team):
    """concatenate all the matches played at home and away so that they are on the same column for the team
    
    ### By using the function swap(), THIS FUNCTION MODIFIES INFORMATION by suggesting everey match of the team has been played at home, which is wrong.
    ### Renaming the columns would be more accurate but less practical to use after.

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        team (string): name of the team

    Returns:
        pd.DataFrame: results dataframe with all matches played by the team in the 'home_team' column
    """
    temp = pd.concat([get_home_match(results, team), swap_columns(get_away_match(results, team))]).sort_index()
    temp['home'] = temp['home_team']==temp['country']
    return temp

def goal_difference(results):
    """add a column from the team score - the opponent's team score to get the goal difference (and therfore the outcome of the match)
    e.g.: France | Belgium | 3 | 2 | ... | 3-2=1 -> win

    Args:
        results (pd.DataFrame): results dataframe after merge_matches, get_home_matches or get_away_matches, or the result will be meaningless

    Returns:
        pd.Dataframe: same dataframe with an additionnal column 'goal_difference'
    """
    temp = results.copy()
    temp['goal_difference']=temp['home_score']-temp['away_score']
    return temp

def aggregate_results(results, team1, team2):
    """provides a summary of the encounters between 2 teams

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        team1 (string): name of the first team
        team2 (string): name of the second team

    Returns:
        pd.Dataframe: contains cumulated scores, number of wins, draws, total of matches and the last encounter
    """
    team1_score = 0
    team2_score = 0
    team1_wins = 0
    team2_wins = 0
    draws = 0
    total = 0
    for _, row in filter_encounter(results, team1, team2).iterrows():
        if row['home_team']==team1:
            team1_score += row['home_score']
            team2_score += row['away_score']
            if row['home_score']>row['away_score']:
                team1_wins += 1
            elif row['home_score']<row['away_score']:
                team2_wins += 1
            else: draws += 1
        else:
            team1_score += row['away_score']
            team2_score += row['home_score']
            if row['away_score']>row['home_score']:
                team1_wins += 1
            elif row['away_score']<row['home_score']:
                team2_wins += 1
            else: draws += 1
    total = draws + team2_wins + team1_wins
    
    return pd.DataFrame.from_dict({
        'team1': [team1],
        'team2': [team2],
        'team1_score': [team1_score],
        'team2_score': [team2_score],
        'team1_wins': [team1_wins],
        'team2_wins': [team2_wins],
        'draws': [draws],
        'total': [total], 
    })

def team_summary(results, team, fifa):
    """creates a summary of a team's perfomance

    Args:
        results (pd.DataFrame): results dataframe or sub-part of it
        team (string): name of the team

    Returns:
        pd.DataFrame: summary including global goal average, average goal scored and taken, win statistics and the team's FIFA ranking
    """
    win = 0
    loss = 0
    draw = 0
    goal_average = 0
    goal_scored_average = 0
    goal_taken_average = 0
    for _, match in goal_difference(merge_matches(results, team)).iterrows():
        if match['home_score']>match['away_score']:
            win+=1
        elif match['home_score']==match['away_score']:
            draw+=1
        else:
            loss+=1
        goal_average += match['goal_difference']
        goal_scored_average += match['home_score']
        goal_taken_average += match['away_score']
        
    return pd.DataFrame.from_dict({'team':[team], 'goal_average':[goal_average],
            'goal_scored_average':[goal_scored_average/(win+draw+loss)],
            'goal_taken_average':[goal_taken_average/(win+draw+loss)],
            'win':[win],
            'draw':[draw],
            'loss':[loss],
            'FIFA_rank':[int(fifa[fifa['Country']==team].index[0])]})

def aggregate_summaries(data, teams, fifa):
    """aggregates every team summary in a single dataframe

    Args:
        data (pd.DataFrame): results dataframe or sub-part of it
        teams (list(string)): list of the team's names

    Returns:
        pd.DataFrame: dataframe containing every team's summary
    """
    temp = pd.DataFrame(columns=['team', 'goal_average', 'goal_scored_average', 'goal_taken_average', 'win', 'draw', 'loss', 'FIFA_rank'])
    for team in teams:
        try :
            temp = temp.append(team_summary(data, team, fifa), ignore_index=True)
        except :
            # print(team)
            continue
    temp[['goal_average', 'goal_scored_average', 'goal_taken_average', 'win', 'draw', 'loss', 'FIFA_rank']] = temp[['goal_average', 
        'goal_scored_average', 'goal_taken_average', 'win', 'draw', 'loss', 'FIFA_rank']].apply(pd.to_numeric)
    return temp

def fill_years(df, mode="team"):
    """fills a dataframe with empty rows for a given time range to get a homogeneous dataframe

    Args:
        df (pd.DataFrame): original dataframe with holes for certain dates for certain teams or countries
        mode (string, optional): switch between team (works with racing_bar_chart) and country (works with scatter_map_chart) mode. Defaults to "team".

    Returns:
        pd.DataFrame: filled dataframe
    """
    min_year = df['date'].min()
    max_year = df['date'].max()
    if (mode=="team"):
        for team in df['home_team'].unique():
            for gap in range(min_year, df.loc[(df['home_team']==team)]['date'].min()):
                s_row = pd.Series([gap,0,team], index=df.columns)
                df = df.append(s_row,ignore_index=True)
            for after_gap in range(df.loc[(df['home_team']==team)]['date'].max(), max_year+1):
                s_row = pd.Series([after_gap,df.loc[(df['home_team']==team)]['cumulated_score'].max(),team], index=df.columns)
                df = df.append(s_row,ignore_index=True)
    elif (mode=="country"):
        for pays in df['country'].unique():
            for before_gap in range(min_year, df.loc[(df['country']==pays)]['date'].min()):
                s_row = pd.Series([pays,0,before_gap], index=df.columns)
                df = df.append(s_row,ignore_index=True)
            for after_gap in range(df.loc[(df['country']==pays)]['date'].max(), max_year+1):
                s_row = pd.Series([pays,df.loc[(df['country']==pays)]['match_hosted'].max(),after_gap], index=df.columns)
                df = df.append(s_row,ignore_index=True)
    else :
        print("please provide a mode")
    return df

def aggregate_countries(df):
    df_final = pd.DataFrame(columns=['country', 'match_hosted'])
    for pays in df['home_team'].unique():
        temp = df[df['country']==pays].drop(['home_team', 'away_team', 'home_score', 'away_score', 'tournament', 'city', 'neutral'], axis=1)
        temp = temp.reset_index().groupby(pd.Grouper(key='date', axis=0, freq='Y')).count()
        # return (temp)
        count = 0
        try :
            for i, row in temp.iterrows():
                count += row['country']
                temp.at[i, "match_hosted"] = count
            temp['match_hosted'] = temp['match_hosted'].astype(int)
            # temp = temp.asfreq('YS')
            temp = temp.assign(country=f'{pays}').reset_index()
            temp['date'] = temp['date'].dt.year
        except KeyError:
            # print(pays)
            continue
        df_final = df_final.append(temp, ignore_index=True)
    df_final['date'] = df_final['date'].astype(int)
    df_final['match_hosted'] = df_final['match_hosted'].astype(int)
    return df_final
