# Weather Sensor Reliability

Values are computed from sampled raw canonical patch records. `fg` and `bg` are selected by the GT foreground patch mask used by TaskDec.

| Weather | Group | Camera | LiDAR | 4D Radar | Gate mean | Sensor spread |
|---|---|---:|---:|---:|---:|---:|
| normal | fg | nan | 0.9989 | 0.0011 | 0.1997 | 0.9977 |
| normal | all | nan | 0.9987 | 0.0013 | 0.1562 | 0.9974 |
| normal | bg | nan | 0.9984 | 0.0016 | 0.0700 | 0.9969 |
| overcast | fg | nan | 0.9990 | 0.0010 | 0.1913 | 0.9980 |
| overcast | all | nan | 0.9989 | 0.0011 | 0.1479 | 0.9977 |
| overcast | bg | nan | 0.9986 | 0.0014 | 0.0631 | 0.9972 |
| fog | fg | nan | 0.9990 | 0.0010 | 0.2470 | 0.9980 |
| fog | all | nan | 0.9990 | 0.0010 | 0.1770 | 0.9979 |
| fog | bg | nan | 0.9989 | 0.0011 | 0.0547 | 0.9979 |
| rain | fg | nan | 0.9989 | 0.0011 | 0.1974 | 0.9977 |
| rain | all | nan | 0.9988 | 0.0012 | 0.1511 | 0.9977 |
| rain | bg | nan | 0.9988 | 0.0012 | 0.0608 | 0.9975 |
| sleet | fg | nan | 0.9990 | 0.0010 | 0.2194 | 0.9981 |
| sleet | all | nan | 0.9991 | 0.0009 | 0.1622 | 0.9981 |
| sleet | bg | nan | 0.9991 | 0.0009 | 0.0584 | 0.9983 |
| lightsnow | fg | nan | 0.9989 | 0.0011 | 0.2238 | 0.9978 |
| lightsnow | all | nan | 0.9989 | 0.0011 | 0.1663 | 0.9979 |
| lightsnow | bg | nan | 0.9990 | 0.0010 | 0.0578 | 0.9980 |
| heavysnow | fg | nan | 0.9989 | 0.0011 | 0.2162 | 0.9978 |
| heavysnow | all | nan | 0.9989 | 0.0011 | 0.1604 | 0.9979 |
| heavysnow | bg | nan | 0.9990 | 0.0010 | 0.0555 | 0.9980 |

## Most Sensor-Differentiated Weather Groups

| Weather | Group | Dominant sensor | Mean reliability | Runner-up | Margin |
|---|---|---|---:|---|---:|
| sleet | bg | LiDAR | 0.9991 | 4D Radar (0.0009) | 0.9983 |
| sleet | all | LiDAR | 0.9991 | 4D Radar (0.0009) | 0.9981 |
| sleet | fg | LiDAR | 0.9990 | 4D Radar (0.0010) | 0.9981 |
| overcast | fg | LiDAR | 0.9990 | 4D Radar (0.0010) | 0.9980 |
| heavysnow | bg | LiDAR | 0.9990 | 4D Radar (0.0010) | 0.9980 |
| lightsnow | bg | LiDAR | 0.9990 | 4D Radar (0.0010) | 0.9980 |
| fog | fg | LiDAR | 0.9990 | 4D Radar (0.0010) | 0.9980 |
| fog | all | LiDAR | 0.9990 | 4D Radar (0.0010) | 0.9979 |
| fog | bg | LiDAR | 0.9989 | 4D Radar (0.0011) | 0.9979 |
| heavysnow | all | LiDAR | 0.9989 | 4D Radar (0.0011) | 0.9979 |
| lightsnow | all | LiDAR | 0.9989 | 4D Radar (0.0011) | 0.9979 |
| lightsnow | fg | LiDAR | 0.9989 | 4D Radar (0.0011) | 0.9978 |