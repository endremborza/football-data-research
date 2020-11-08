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


### Model performance

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

{metric_table}

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

### Determinants of pass success

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

{result_of_sample_match}

On example of the away teams passes originating in one zone, 
distributed across formation slots

{source_example}

this gives a gini coefficient of X. 
calculating this gini coefficient 
for all source zones gives the following table

{all_ginis}

which gives a weighted average

{style_agged}


## Success Association

Turns out the above defined rigidity of a teams performance
can be associated with its success, based on the opposition.

![style-heatmap](figures/heatmap.png)

## Association to causation

## Entity Coreference


## Pipeline
