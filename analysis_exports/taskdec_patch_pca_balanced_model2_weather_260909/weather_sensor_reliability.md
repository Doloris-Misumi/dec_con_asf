# Weather Sensor Reliability

Values are computed from sampled raw canonical patch records. `fg` and `bg` are selected by the GT foreground patch mask used by TaskDec.

| Weather | Group | Camera | LiDAR | 4D Radar | Gate mean | Sensor spread |
|---|---|---:|---:|---:|---:|---:|
| normal | fg | 0.0000 | 1.0000 | 0.0000 | 0.2732 | 1.0000 |
| normal | all | 0.0000 | 1.0000 | 0.0000 | 0.2292 | 1.0000 |
| normal | bg | 0.0000 | 1.0000 | 0.0000 | 0.1445 | 1.0000 |
| overcast | fg | 0.0000 | 1.0000 | 0.0000 | 0.2893 | 1.0000 |
| overcast | all | 0.0000 | 1.0000 | 0.0000 | 0.2336 | 1.0000 |
| overcast | bg | 0.0000 | 1.0000 | 0.0000 | 0.1264 | 1.0000 |
| fog | fg | 0.0000 | 1.0000 | 0.0000 | 0.3038 | 1.0000 |
| fog | all | 0.0000 | 1.0000 | 0.0000 | 0.2297 | 1.0000 |
| fog | bg | 0.0000 | 1.0000 | 0.0000 | 0.1174 | 1.0000 |
| rain | fg | 0.0000 | 1.0000 | 0.0000 | 0.2764 | 1.0000 |
| rain | all | 0.0000 | 1.0000 | 0.0000 | 0.2260 | 1.0000 |
| rain | bg | 0.0000 | 1.0000 | 0.0000 | 0.1287 | 1.0000 |
| sleet | fg | 0.0000 | 1.0000 | 0.0000 | 0.2612 | 1.0000 |
| sleet | all | 0.0000 | 1.0000 | 0.0000 | 0.2058 | 1.0000 |
| sleet | bg | 0.0000 | 1.0000 | 0.0000 | 0.1180 | 1.0000 |
| lightsnow | fg | 0.0000 | 1.0000 | 0.0000 | 0.2825 | 1.0000 |
| lightsnow | all | 0.0000 | 1.0000 | 0.0000 | 0.2229 | 1.0000 |
| lightsnow | bg | 0.0000 | 1.0000 | 0.0000 | 0.1231 | 1.0000 |
| heavysnow | fg | 0.0000 | 1.0000 | 0.0000 | 0.2611 | 1.0000 |
| heavysnow | all | 0.0000 | 1.0000 | 0.0000 | 0.2070 | 1.0000 |
| heavysnow | bg | 0.0000 | 1.0000 | 0.0000 | 0.1169 | 1.0000 |

## Most Sensor-Differentiated Weather Groups

| Weather | Group | Dominant sensor | Mean reliability | Runner-up | Margin |
|---|---|---|---:|---|---:|
| sleet | fg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| sleet | all | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| fog | fg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| sleet | bg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| lightsnow | fg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| lightsnow | all | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| fog | all | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| heavysnow | bg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| heavysnow | all | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| heavysnow | fg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| lightsnow | bg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |
| fog | bg | LiDAR | 1.0000 | Camera (0.0000) | 1.0000 |