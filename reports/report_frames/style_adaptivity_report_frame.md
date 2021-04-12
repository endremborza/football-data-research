## Describing style

style is defined for each side × match × phase

currently, phases are: `['first_quarter', 'first_half', 'upto_third_quarter', 'full_game']`

and in the following, first half will be taken as default.

...

## Measuring Adaptivity

take my team vs team x in season S

- a sample of 18 matches is taken: the last 9 games of my team and the last 9 games of team x in season S. (games where no 9 previous games are available are discarded)
- of these 18 matches, 18 style measurements are taken, 9 from my team and 9 from the opposition of team x

the question is which of these 18 performances a team chooses to emulate and how this choice affects the outcome of the game, this is currently measured in 2 different ways


### Weighted similarity

simply measure similarity to style of these 18 observations using euclidean distance

- `my_game-weighted_similarity`: mean similarity to style of my team's past games weighted by success (final goal difference)
- `not_my_game-weighted_similarity`: mean similarity to style of team x's opponents in the last 9 games weighted by success

### Parameter on similarity**

run a regression on the similarity measure of the 18 games and take the parameters from variables defining those 18 games. setting every parameter to zero where p-value is lower than 30%

- `is_my_game-similarity_param`: parameter of `is_my_game` dummy
- `normed_success-similarity_param`: parameter of goal difference standard-scaled for my games and opposition of team x separately
- `success_in_my_game-similarity_param`: parameter for interaction of `is_my_game` dummy and standardized goal difference


## Results

simple OLS regression

- target: `won` dummy
- 1158 observations (match × side)
- `my_win_rate` win rate in last 9 games
- `opps_opp_win_rate` loss rate of opposition
- every variable starting with `opposition-` is the same variable for the opposition tame of the match


### Specific space

space columns: `['pass_success_rate', 'ballrecovery_dist_from_opp_goal']`

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>my_win_rate</th>
      <td>0.596 (pval: 0%)</td>
      <td>0.567 (pval: 0%)</td>
      <td>0.56 (pval: 0%)</td>
      <td>0.587 (pval: 0%)</td>
      <td>0.583 (pval: 0%)</td>
    </tr>
    <tr>
      <th>opps_opp_win_rate</th>
      <td>0.411 (pval: 0%)</td>
      <td>0.417 (pval: 0%)</td>
      <td>0.396 (pval: 0%)</td>
      <td>0.406 (pval: 0%)</td>
      <td>0.399 (pval: 0%)</td>
    </tr>
    <tr>
      <th>const</th>
      <td>0.0 (pval: 100%)</td>
      <td>0.005 (pval: 88%)</td>
      <td>0.022 (pval: 56%)</td>
      <td>0.054 (pval: 39%)</td>
      <td>0.059 (pval: 42%)</td>
    </tr>
    <tr>
      <th>is_my_game-similarity_param</th>
      <td></td>
      <td>0.036 (pval: 22%)</td>
      <td>0.034 (pval: 25%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>normed_success-similarity_param</th>
      <td></td>
      <td>-0.082 (pval: 27%)</td>
      <td>-0.069 (pval: 35%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>success_in_my_game-similarity_param</th>
      <td></td>
      <td>-0.19 (pval: 0%)</td>
      <td>-0.177 (pval: 0%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>opposition-is_my_game-similarity_param</th>
      <td></td>
      <td></td>
      <td>-0.047 (pval: 11%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>opposition-normed_success-similarity_param</th>
      <td></td>
      <td></td>
      <td>0.119 (pval: 11%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>opposition-success_in_my_game-similarity_param</th>
      <td></td>
      <td></td>
      <td>0.133 (pval: 2%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td>0.024 (pval: 41%)</td>
      <td>0.023 (pval: 43%)</td>
    </tr>
    <tr>
      <th>not_my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td>0.008 (pval: 75%)</td>
      <td>0.008 (pval: 75%)</td>
    </tr>
    <tr>
      <th>opposition-my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>-0.016 (pval: 59%)</td>
    </tr>
    <tr>
      <th>opposition-not_my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>0.016 (pval: 55%)</td>
    </tr>
  </tbody>
</table>



### Abstract space

space: `['umap_x', 'umap_y']`

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>my_win_rate</th>
      <td>0.596 (pval: 0%)</td>
      <td>0.574 (pval: 0%)</td>
      <td>0.568 (pval: 0%)</td>
      <td>0.587 (pval: 0%)</td>
      <td>0.581 (pval: 0%)</td>
    </tr>
    <tr>
      <th>opps_opp_win_rate</th>
      <td>0.411 (pval: 0%)</td>
      <td>0.406 (pval: 0%)</td>
      <td>0.386 (pval: 0%)</td>
      <td>0.397 (pval: 0%)</td>
      <td>0.389 (pval: 0%)</td>
    </tr>
    <tr>
      <th>const</th>
      <td>0.0 (pval: 100%)</td>
      <td>0.0 (pval: 100%)</td>
      <td>0.013 (pval: 73%)</td>
      <td>0.099 (pval: 10%)</td>
      <td>0.063 (pval: 37%)</td>
    </tr>
    <tr>
      <th>is_my_game-similarity_param</th>
      <td></td>
      <td>0.044 (pval: 8%)</td>
      <td>0.041 (pval: 11%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>normed_success-similarity_param</th>
      <td></td>
      <td>0.107 (pval: 9%)</td>
      <td>0.111 (pval: 8%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>success_in_my_game-similarity_param</th>
      <td></td>
      <td>0.072 (pval: 16%)</td>
      <td>0.076 (pval: 14%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>opposition-is_my_game-similarity_param</th>
      <td></td>
      <td></td>
      <td>-0.032 (pval: 21%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>opposition-normed_success-similarity_param</th>
      <td></td>
      <td></td>
      <td>-0.011 (pval: 86%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>opposition-success_in_my_game-similarity_param</th>
      <td></td>
      <td></td>
      <td>0.074 (pval: 15%)</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td>0.054 (pval: 3%)</td>
      <td>0.053 (pval: 3%)</td>
    </tr>
    <tr>
      <th>not_my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td>0.007 (pval: 79%)</td>
      <td>0.012 (pval: 65%)</td>
    </tr>
    <tr>
      <th>opposition-my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>-0.027 (pval: 28%)</td>
    </tr>
    <tr>
      <th>opposition-not_my_game-weighted_similarity</th>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>-0.005 (pval: 86%)</td>
    </tr>
  </tbody>
</table>
