# Report

`final_report` dvc step creates this report 
and all figures and tables used by it

## Model
In the `train_pass_success_model` step, a boosted tree model is trained 
on selected features of the event data to estimate expected success 
of a pass.

### Features

(with hopefully sufficiently self explanitory names)

- boolean qualifiers
  - `longball`, `headpass`, `throwin`, `chipped`, `cross`, `cornertaken`, `freekicktaken`, `layoff`, `indirectfreekicktaken`, `throughball`, `keeperthrow`, `goalkick`
- categorical variables
  - `period`, `event_side`, `pass_direction_cat`
- numeric variables
  - `x`, `y`, `passendy`, `passendx`, `length`, `distance_from_opp_goal`, `distance_from_own_goal`, `minute`


### Model Performance

The model is evaluated on a test set 
in the `evaluate_pass_success_model` step

The output of the model is intended to extend pass data
 with estimated riskiness of a pass. 
 So although it is worth noting that the confusion 
matrix and point metrics show that these variables predict the success of a 
pass quite well, more in depth look at the predicted probabilities is needed

#### Confusion matrix
![cm](figures/confusion_matrix.png)

#### Point metrics

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>accuracy</th>
      <td>0.869612</td>
    </tr>
    <tr>
      <th>recall</th>
      <td>0.926676</td>
    </tr>
    <tr>
      <th>f1</th>
      <td>0.916718</td>
    </tr>
    <tr>
      <th>brier</th>
      <td>0.092574</td>
    </tr>
  </tbody>
</table>

One way to assess prediction probabilities is the ROC curve, which 
is also sufficiently promising with an AUC of over 90%

#### ROC
![roc](figures/roc.png)

To have a more complete look at the prediction probabilities is to create
subsets of the test set based on bins of prediction probabilities. 
Here, we can see that nearly half of all passes are predicted to 
succeed with over 90% chance. However the predictions can still be used
to create subsets of of passes where the success rate is very close to 
the mean of predicted probability. 

#### Predicted success bins
![binsizes](figures/pred_bins.png)

![binpreds](figures/pred_bin_means.png)

These metrics and figures should be sufficient to conclude that the model
meaningfully extends the data with estimated pass riskiness

### Determinants of Pass Success

Looking at [shap](https://github.com/slundberg/shap) generated values
for impact on predicted success, the most important determinants of 
success of a pass apper to be its target location, direction as lenght. 
These align with the expectations that passes targeting places closer 
to the opposition goal and forward passes are riskier than backward passes
far from the opposition goal.

![shap](figures/shap.png)

## Network

Networks are created based on pass events in the games, 
in the `create-match-networks` step.
Pass targets are not straightforward, as they are not recorded. 
A specific `player_with_next_touch` variable is created for all passes,
where the chronologically next touch event is found, for successful passes

### Network Types
Three types of networks are created for every game. Specific for the 
home and away sides and the formations they played in the game.
These networks are based on the passes attempted when the team played 
in the formation the graph is based on.

(in the sample graph plots, the nodes are placed based on the mean source 
location of pass attempts)
 
- `field_zone` based, where sources and targets represent one specific 
 third of the field in either direction, splitting the pitch to 9 equal sized
 areas. (this is the only type of graph that includes unsuccessful passes, as 
 pass end location is recorded for incomplete passes as well, but pass target 
 player is not)
![nw1](figures/field_zone-1190485-home-433.svg)

- `formation_slot` based, where sources and targets represent a slot in the 
 teams formation. in this example, `spot_2` is the right wing-back position 
 in 3-5-2 
 filled in the game by Kyle Walker 
 (as seen in the next figure)
![nw2](figures/formation_slot-1190551-away-352.svg)

- `player` based, where sources and targets are simply players
![nw3](figures/player-1190551-away-352.svg)


### Edge Attributes

As each edge represents a set of passes a number of metrics are available describing 
that set.

For each edge we know:

- number of passes, categorized by
  - general category:
    - longball, headpass, throwin, chipped, cross, cornertaken, 
    freekicktaken, layoff, indirectfreekicktaken, throughball, 
    keeperthrow, goalkick, is_success
  - attempted in first half / second half
  - pass direction left/right/forward/backward
  - source and target formation slots and field zones
  - predicted success bin
    - (0, 0.1], (0.1, 0.2], (0.2, 0.3], ... , (0.9, 1]
    - this is supposed to indicate the riskyness of passes
- mean statistics for passes:
  - pass start location (x, y), pass end location, (passendy, passendx)
  - length, start distance from opposition goal, distance from own goal
  - attempt minute
  - predicted success probability

## Style

Based on the networks created for each game, a wide range of possible
style metrics could be calculated for a team playing in a formation.

I will present just one here.

### Rigidity

Lets define a broad basis for the rigidity of a teams 
performance in a match:

> A performance is rigid, if the passing patterns of the team 
> can be discovered to follow a fairly simple  algorithm

In this concrete rigidity metric, the algorithm is:

> If player X finds himself with tha ball in field zone Z
> look to pass to another player playing in S position of the formation

An estimate about how strictly a teams passing pattern follows this
 algorithm can be made, using data about successful passes from 
 specific field zones to different formation slots.

Take the following match

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>wh_match_id</th>
      <th>home_team</th>
      <th>away_team</th>
      <th>fulltime_score</th>
      <th>date</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1190306</td>
      <td>Huddersfield</td>
      <td>Man City</td>
      <td>1 : 2</td>
      <td>2017-11-26</td>
    </tr>
  </tbody>
</table>

One example of the away teams passes originating in zone `1-0`, 
(right side of midfield) distributed across formation slots:

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>source</th>
      <th>target</th>
      <th>successful passes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1-0</td>
      <td>spot_1</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1-0</td>
      <td>spot_10</td>
      <td>11.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1-0</td>
      <td>spot_11</td>
      <td>1.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1-0</td>
      <td>spot_2</td>
      <td>17.0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1-0</td>
      <td>spot_3</td>
      <td>2.0</td>
    </tr>
    <tr>
      <th>5</th>
      <td>1-0</td>
      <td>spot_4</td>
      <td>10.0</td>
    </tr>
    <tr>
      <th>6</th>
      <td>1-0</td>
      <td>spot_5</td>
      <td>13.0</td>
    </tr>
    <tr>
      <th>7</th>
      <td>1-0</td>
      <td>spot_6</td>
      <td>24.0</td>
    </tr>
    <tr>
      <th>8</th>
      <td>1-0</td>
      <td>spot_7</td>
      <td>13.0</td>
    </tr>
    <tr>
      <th>9</th>
      <td>1-0</td>
      <td>spot_8</td>
      <td>10.0</td>
    </tr>
    <tr>
      <th>10</th>
      <td>1-0</td>
      <td>spot_9</td>
      <td>7.0</td>
    </tr>
  </tbody>
</table>

Though spots 1, 3, and 11 
(goalkeeper, left back and left forward in a 4-3-3 played by Man City here)
don't really receive passes from this zone, the rest of the passes are 
fairly well spread out.

So we could have an estimate of how strictly this pattern follows 
a simple version of the rigid algorithm by determining some sort of 
concentration metric of these numbers, e. g. the gini coefficient. 
These concrete numbers givee a gini coefficient of about 41%, 
which is fairly low.
Looking at calculated gini coefficients
for all source zones of both teams gives the following table.
Notice that the lowest gini score for Huddersfield is 46%, 
so based on this metric Huddersfield seems the more rigid team.

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>side</th>
      <th>source</th>
      <th>formation</th>
      <th>is_success</th>
      <th>gini</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>away</td>
      <td>0-0</td>
      <td>433</td>
      <td>16.0</td>
      <td>0.613636</td>
    </tr>
    <tr>
      <th>1</th>
      <td>away</td>
      <td>0-1</td>
      <td>433</td>
      <td>44.0</td>
      <td>0.342975</td>
    </tr>
    <tr>
      <th>2</th>
      <td>away</td>
      <td>0-2</td>
      <td>433</td>
      <td>32.0</td>
      <td>0.494318</td>
    </tr>
    <tr>
      <th>3</th>
      <td>away</td>
      <td>1-0</td>
      <td>433</td>
      <td>108.0</td>
      <td>0.387205</td>
    </tr>
    <tr>
      <th>4</th>
      <td>away</td>
      <td>1-1</td>
      <td>433</td>
      <td>176.0</td>
      <td>0.353306</td>
    </tr>
    <tr>
      <th>5</th>
      <td>away</td>
      <td>1-2</td>
      <td>433</td>
      <td>99.0</td>
      <td>0.536272</td>
    </tr>
    <tr>
      <th>6</th>
      <td>away</td>
      <td>2-0</td>
      <td>433</td>
      <td>87.0</td>
      <td>0.480669</td>
    </tr>
    <tr>
      <th>7</th>
      <td>away</td>
      <td>2-1</td>
      <td>433</td>
      <td>52.0</td>
      <td>0.430070</td>
    </tr>
    <tr>
      <th>8</th>
      <td>away</td>
      <td>2-2</td>
      <td>433</td>
      <td>51.0</td>
      <td>0.527629</td>
    </tr>
    <tr>
      <th>9</th>
      <td>home</td>
      <td>0-0</td>
      <td>451</td>
      <td>8.0</td>
      <td>0.750000</td>
    </tr>
    <tr>
      <th>10</th>
      <td>home</td>
      <td>0-1</td>
      <td>451</td>
      <td>19.0</td>
      <td>0.574163</td>
    </tr>
    <tr>
      <th>11</th>
      <td>home</td>
      <td>0-2</td>
      <td>451</td>
      <td>11.0</td>
      <td>0.595041</td>
    </tr>
    <tr>
      <th>12</th>
      <td>home</td>
      <td>1-0</td>
      <td>451</td>
      <td>18.0</td>
      <td>0.484848</td>
    </tr>
    <tr>
      <th>13</th>
      <td>home</td>
      <td>1-1</td>
      <td>451</td>
      <td>15.0</td>
      <td>0.387879</td>
    </tr>
    <tr>
      <th>14</th>
      <td>home</td>
      <td>1-2</td>
      <td>4411</td>
      <td>1.0</td>
      <td>0.909091</td>
    </tr>
    <tr>
      <th>15</th>
      <td>home</td>
      <td>1-2</td>
      <td>451</td>
      <td>13.0</td>
      <td>0.559441</td>
    </tr>
    <tr>
      <th>16</th>
      <td>home</td>
      <td>2-0</td>
      <td>4411</td>
      <td>0.0</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>17</th>
      <td>home</td>
      <td>2-0</td>
      <td>451</td>
      <td>18.0</td>
      <td>0.555556</td>
    </tr>
    <tr>
      <th>18</th>
      <td>home</td>
      <td>2-1</td>
      <td>4411</td>
      <td>0.0</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>19</th>
      <td>home</td>
      <td>2-1</td>
      <td>451</td>
      <td>1.0</td>
      <td>0.909091</td>
    </tr>
    <tr>
      <th>20</th>
      <td>home</td>
      <td>2-2</td>
      <td>451</td>
      <td>7.0</td>
      <td>0.623377</td>
    </tr>
  </tbody>
</table>

Taking the weighted averages of the gini coefficients, and extending the 
data with the pass success rates of the teams we can deduce a 
notable difference in style.

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>side</th>
      <th>weighted means of ginis --&gt; rigidity</th>
      <th>pass success rate</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>away</td>
      <td>0.434450</td>
      <td>0.863636</td>
    </tr>
    <tr>
      <th>1</th>
      <td>home</td>
      <td>0.553645</td>
      <td>0.521127</td>
    </tr>
  </tbody>
</table>

Of course many different style features can be defined on this rich dataset, 
this example is serves a purpose in the next section.

## Style-Success Association

Turns out, the above defined rigidity of a teams performance
can be associated with its success, based on the opposition.

Take this heatmap of win rates by the intersection of a teams 
pass success rate and the opponents rigidity.

![style-heatmap](figures/heatmap.png)

It would seem that when a team has low pass success rate, the opponents
measure rigidity has no correlation with the win rate. However,
when a team is accurate in it's passing, a strong association appears,
with the more rigid the opponent, the more likely the well-passing team wins.

The interesting challenge here of course, is identifying a casual relationship
underlying this association.

## Association to Causation

### Observation

The observation in the previous section can be stated as follows:

> If team A's performance is characterised by high passing accuracy in a match, 
> the more "rigid" the opponents performance is, the more likely it is 
> that team A ends up winning the game

with the [rigid](#rigidity) definition given above. 

Giving a formal statement for this observation:

running a probit model on winning gives the following coefficients,
for teams with pass success rate in the bottom two thirds:

<table class="simpletable">
<tr>
           <td></td>              <th>coef</th>     <th>std err</th>      <th>z</th>      <th>P>|z|</th>  <th>[0.025</th>    <th>0.975]</th>  
</tr>
<tr>
  <th>opposition rigidity</th> <td>   -0.4118</td> <td>    1.087</td> <td>   -0.379</td> <td> 0.705</td> <td>   -2.543</td> <td>    1.719</td>
</tr>
<tr>
  <th>const</th>               <td>   -0.3037</td> <td>    0.501</td> <td>   -0.606</td> <td> 0.544</td> <td>   -1.286</td> <td>    0.678</td>
</tr>
</table>

and in the top third:

<table class="simpletable">
<tr>
           <td></td>              <th>coef</th>     <th>std err</th>      <th>z</th>      <th>P>|z|</th>  <th>[0.025</th>    <th>0.975]</th>  
</tr>
<tr>
  <th>opposition rigidity</th> <td>    3.1209</td> <td>    1.288</td> <td>    2.423</td> <td> 0.015</td> <td>    0.597</td> <td>    5.645</td>
</tr>
<tr>
  <th>const</th>               <td>   -1.4422</td> <td>    0.606</td> <td>   -2.379</td> <td> 0.017</td> <td>   -2.630</td> <td>   -0.254</td>
</tr>
</table>

with the coefficient for `opposition rigidity` only significant in
the top third case.

### Possible paths

There are many possible causal models that are capable of producing 
data like this. To list a few, with some explanation:

- Teams develop a specific style of play 
and certain styles suit certain opponents better.
  - the key to wictory _is_ the difference in style
- Some teams are more adaptive in style than others, 
and the ones who can not adapt to a fluid playing style
against an opponent with high pass success rate, lose.
  - the key to victory is adaptability
- The causal path is actually reversed: 
a teams performance appears more rigid, when the team is losing
more prominently against a side with accurate passing
  - these style metrics have no impact on winning chances
- players with better technical ability pass more accurately, 
and when facing good players, other players more 
likely produce a rigid performance.
  - the key to victory is technical ability

The point of this section is to find out which of these, or possible other
causal explanation is most likely to generate data like the one we observed.

To answer this, the data must be extended first

## Entity Coreference

[this](https://github.com/endremborza/encoref) WIP package is used
for entity coreference, mainly to match players.

Matching is not a straightforward tasks, as lot of the names of teams or
players dont match closely, so a sophisticated algorithm is needed
to match these entities. A few examples can be seen in the next table, 
of the difficult to match, but coreferent entities.



## Pipeline

[entry points for pipeline elements](dvcdag.md)