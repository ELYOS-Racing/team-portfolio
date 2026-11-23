# Energy strategy

Plans, metre by metre, how fast to go and when to pulse or glide to spend the least energy inside the time limit, and explains where every watt goes. It also produces the data that trains the predictive co-pilot.

| Aspect | Detail |
|---|---|
| Track | The 3,844.6 m Indianapolis loop from Shell's official coordinates, with elevation, rebuilt as a smooth curve with curvature, slope and width at every metre |
| Optimisation | A longitudinal model of the car solved with optimal control (CasADi) and genetic algorithms (pymoo): speed profile, pulse and glide |
| Loss budget | Ranks where the energy goes (motor and driver, rolling resistance, fixed electronics, aerodynamics) and how much each improvement is worth |
| Output | Speed targets for the driver and training data for the co-pilot |

## History

### 2027 · Loss budget and the choice of motor (in progress)

What the 2026 attempt tells us:


- **Consistent driving.** Five valid attempts within about 8 % of each other, from 309 to 336 km/kWh. The winning car reached 469.7 km/kWh, so the gap is in the car, not in the driving or the strategy.
- **About 22 W to find.** Our attempt averaged about 80 W over 15.33 km; the winner about 58 W.
- **Where it is, in the model:** chain, clutch and pulse-and-glide save about 20 % against the hub motor; every 0.001 less rolling resistance is worth about 10 % more km/kWh, 2 W less of electronics about 3 %, and 0.01 m² less drag area about 4 %.

The 2027 motor: about 500 W at 48 V with chain and clutch: it puts the 150–300 W pulses in the motor's most efficient zone, lets the motor driver measure current well at the 2–5 A where it runs most of the time, and keeps mass down. The model's parameters stay assumptions until the coast-down and bench tests replace them.

The code is private.
