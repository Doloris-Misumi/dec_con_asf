# Weather Sensor Reliability

Values are computed from sampled raw canonical patch records. `fg` and `bg` are selected by the GT foreground patch mask used by TaskDec.

| Weather | Group | Camera | LiDAR | 4D Radar | Gate mean | Sensor spread |
|---|---|---:|---:|---:|---:|---:|
| normal | fg | 0.0060 | 0.9930 | 0.0009 | 0.2512 | 0.9921 |
| normal | all | 0.0072 | 0.9918 | 0.0010 | 0.2073 | 0.9907 |
| normal | bg | 0.0095 | 0.9892 | 0.0013 | 0.1204 | 0.9880 |
| overcast | fg | 0.0055 | 0.9938 | 0.0008 | 0.2422 | 0.9930 |
| overcast | all | 0.0067 | 0.9924 | 0.0009 | 0.1980 | 0.9915 |
| overcast | bg | 0.0091 | 0.9897 | 0.0012 | 0.1116 | 0.9885 |
| fog | fg | 0.0052 | 0.9940 | 0.0008 | 0.3004 | 0.9932 |
| fog | all | 0.0057 | 0.9935 | 0.0008 | 0.2300 | 0.9926 |
| fog | bg | 0.0066 | 0.9925 | 0.0009 | 0.1068 | 0.9916 |
| rain | fg | 0.0060 | 0.9931 | 0.0009 | 0.2496 | 0.9922 |
| rain | all | 0.0066 | 0.9925 | 0.0009 | 0.2033 | 0.9916 |
| rain | bg | 0.0076 | 0.9914 | 0.0010 | 0.1130 | 0.9903 |
| sleet | fg | 0.0047 | 0.9945 | 0.0008 | 0.2775 | 0.9938 |
| sleet | all | 0.0049 | 0.9943 | 0.0008 | 0.2211 | 0.9936 |
| sleet | bg | 0.0053 | 0.9940 | 0.0007 | 0.1188 | 0.9932 |
| lightsnow | fg | 0.0056 | 0.9935 | 0.0009 | 0.2793 | 0.9926 |
| lightsnow | all | 0.0058 | 0.9934 | 0.0009 | 0.2221 | 0.9925 |
| lightsnow | bg | 0.0061 | 0.9931 | 0.0008 | 0.1143 | 0.9922 |
| heavysnow | fg | 0.0057 | 0.9935 | 0.0009 | 0.2699 | 0.9926 |
| heavysnow | all | 0.0059 | 0.9932 | 0.0009 | 0.2145 | 0.9924 |
| heavysnow | bg | 0.0063 | 0.9928 | 0.0009 | 0.1105 | 0.9920 |

## Most Sensor-Differentiated Weather Groups

| Weather | Group | Dominant sensor | Mean reliability | Runner-up | Margin |
|---|---|---|---:|---|---:|
| sleet | fg | LiDAR | 0.9945 | Camera (0.0047) | 0.9898 |
| sleet | all | LiDAR | 0.9943 | Camera (0.0049) | 0.9894 |
| fog | fg | LiDAR | 0.9940 | Camera (0.0052) | 0.9889 |
| sleet | bg | LiDAR | 0.9940 | Camera (0.0053) | 0.9887 |
| overcast | fg | LiDAR | 0.9938 | Camera (0.0055) | 0.9883 |
| lightsnow | fg | LiDAR | 0.9935 | Camera (0.0056) | 0.9879 |
| fog | all | LiDAR | 0.9935 | Camera (0.0057) | 0.9878 |
| heavysnow | fg | LiDAR | 0.9935 | Camera (0.0057) | 0.9878 |
| lightsnow | all | LiDAR | 0.9934 | Camera (0.0058) | 0.9876 |
| heavysnow | all | LiDAR | 0.9932 | Camera (0.0059) | 0.9874 |
| rain | fg | LiDAR | 0.9931 | Camera (0.0060) | 0.9871 |
| normal | fg | LiDAR | 0.9930 | Camera (0.0060) | 0.9870 |