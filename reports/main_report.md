# This is a frame for filling

`final_report` dvc step creates this report 
and all figures and tables used by it

## Model
In the `train-pass-success-model`


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

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>side</th>
      <th>source</th>
      <th>formation</th>
      <th>is_success</th>
      <th>spot_1</th>
      <th>spot_10</th>
      <th>spot_11</th>
      <th>spot_2</th>
      <th>spot_3</th>
      <th>spot_4</th>
      <th>spot_5</th>
      <th>spot_6</th>
      <th>spot_7</th>
      <th>spot_8</th>
      <th>spot_9</th>
      <th>total</th>
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
      <td>1.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>1.0</td>
      <td>6.0</td>
      <td>4.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>19</td>
      <td>0.675325</td>
    </tr>
    <tr>
      <th>1</th>
      <td>away</td>
      <td>0-1</td>
      <td>433</td>
      <td>43.0</td>
      <td>3.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>8.0</td>
      <td>3.0</td>
      <td>5.0</td>
      <td>8.0</td>
      <td>4.0</td>
      <td>2.0</td>
      <td>6.0</td>
      <td>0.0</td>
      <td>46</td>
      <td>0.376623</td>
    </tr>
    <tr>
      <th>2</th>
      <td>away</td>
      <td>0-2</td>
      <td>433</td>
      <td>32.0</td>
      <td>4.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>5.0</td>
      <td>8.0</td>
      <td>3.0</td>
      <td>3.0</td>
      <td>5.0</td>
      <td>1.0</td>
      <td>41</td>
      <td>0.480938</td>
    </tr>
    <tr>
      <th>3</th>
      <td>away</td>
      <td>1-0</td>
      <td>433</td>
      <td>108.0</td>
      <td>0.0</td>
      <td>11.0</td>
      <td>1.0</td>
      <td>17.0</td>
      <td>2.0</td>
      <td>10.0</td>
      <td>12.0</td>
      <td>24.0</td>
      <td>13.0</td>
      <td>10.0</td>
      <td>4.0</td>
      <td>116</td>
      <td>0.409091</td>
    </tr>
    <tr>
      <th>4</th>
      <td>away</td>
      <td>1-1</td>
      <td>433</td>
      <td>176.0</td>
      <td>0.0</td>
      <td>10.0</td>
      <td>3.0</td>
      <td>20.0</td>
      <td>14.0</td>
      <td>32.0</td>
      <td>16.0</td>
      <td>26.0</td>
      <td>15.0</td>
      <td>30.0</td>
      <td>9.0</td>
      <td>190</td>
      <td>0.354286</td>
    </tr>
    <tr>
      <th>5</th>
      <td>away</td>
      <td>1-2</td>
      <td>433</td>
      <td>99.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>5.0</td>
      <td>3.0</td>
      <td>14.0</td>
      <td>18.0</td>
      <td>10.0</td>
      <td>33.0</td>
      <td>2.0</td>
      <td>8.0</td>
      <td>3.0</td>
      <td>106</td>
      <td>0.539831</td>
    </tr>
    <tr>
      <th>6</th>
      <td>away</td>
      <td>2-0</td>
      <td>433</td>
      <td>87.0</td>
      <td>0.0</td>
      <td>19.0</td>
      <td>1.0</td>
      <td>14.0</td>
      <td>0.0</td>
      <td>6.0</td>
      <td>9.0</td>
      <td>6.0</td>
      <td>13.0</td>
      <td>17.0</td>
      <td>1.0</td>
      <td>113</td>
      <td>0.484144</td>
    </tr>
    <tr>
      <th>7</th>
      <td>away</td>
      <td>2-1</td>
      <td>433</td>
      <td>52.0</td>
      <td>0.0</td>
      <td>3.0</td>
      <td>3.0</td>
      <td>4.0</td>
      <td>2.0</td>
      <td>10.0</td>
      <td>0.0</td>
      <td>6.0</td>
      <td>4.0</td>
      <td>11.0</td>
      <td>9.0</td>
      <td>76</td>
      <td>0.430070</td>
    </tr>
    <tr>
      <th>8</th>
      <td>away</td>
      <td>2-2</td>
      <td>433</td>
      <td>51.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>7.0</td>
      <td>0.0</td>
      <td>7.0</td>
      <td>4.0</td>
      <td>3.0</td>
      <td>4.0</td>
      <td>14.0</td>
      <td>11.0</td>
      <td>1.0</td>
      <td>61</td>
      <td>0.527629</td>
    </tr>
    <tr>
      <th>9</th>
      <td>home</td>
      <td>0-0</td>
      <td>451</td>
      <td>8.0</td>
      <td>2.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>4.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>22</td>
      <td>0.750000</td>
    </tr>
    <tr>
      <th>10</th>
      <td>home</td>
      <td>0-1</td>
      <td>451</td>
      <td>19.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>2.0</td>
      <td>8.0</td>
      <td>39</td>
      <td>0.565657</td>
    </tr>
    <tr>
      <th>11</th>
      <td>home</td>
      <td>0-2</td>
      <td>451</td>
      <td>11.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>3.0</td>
      <td>3.0</td>
      <td>25</td>
      <td>0.595041</td>
    </tr>
    <tr>
      <th>12</th>
      <td>home</td>
      <td>1-0</td>
      <td>451</td>
      <td>18.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>3.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>2.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>3.0</td>
      <td>31</td>
      <td>0.460606</td>
    </tr>
    <tr>
      <th>13</th>
      <td>home</td>
      <td>1-1</td>
      <td>451</td>
      <td>15.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>3.0</td>
      <td>2.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>3.0</td>
      <td>17</td>
      <td>0.517483</td>
    </tr>
    <tr>
      <th>14</th>
      <td>home</td>
      <td>1-2</td>
      <td>4411</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>0.909091</td>
    </tr>
    <tr>
      <th>15</th>
      <td>home</td>
      <td>1-2</td>
      <td>451</td>
      <td>13.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>3.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>1.0</td>
      <td>23</td>
      <td>0.512397</td>
    </tr>
    <tr>
      <th>16</th>
      <td>home</td>
      <td>2-0</td>
      <td>4411</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>17</th>
      <td>home</td>
      <td>2-0</td>
      <td>451</td>
      <td>18.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>5.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>2.0</td>
      <td>4.0</td>
      <td>1.0</td>
      <td>33</td>
      <td>0.556150</td>
    </tr>
    <tr>
      <th>18</th>
      <td>home</td>
      <td>2-1</td>
      <td>4411</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>19</th>
      <td>home</td>
      <td>2-1</td>
      <td>451</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>5</td>
      <td>0.909091</td>
    </tr>
    <tr>
      <th>20</th>
      <td>home</td>
      <td>2-2</td>
      <td>451</td>
      <td>7.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>1.0</td>
      <td>13</td>
      <td>0.623377</td>
    </tr>
  </tbody>
</table>

## Success Association

## Association to causation

## Entity Coreference


## Pipeline
