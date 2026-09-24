# TaskDec Weather PCA Analysis

Export: weather-balanced foreground/background patch sample.

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 62.58% | 20.52% |
| common | 59.94% | 25.17% |
| unique | 52.43% | 33.59% |

## Foreground Gate By Weather

| Weather | Gate fg | Gate bg | Delta |
|---|---:|---:|---:|
| normal | 0.2512 | 0.1204 | 0.1308 |
| overcast | 0.2422 | 0.1116 | 0.1306 |
| fog | 0.3004 | 0.1068 | 0.1936 |
| rain | 0.2496 | 0.1130 | 0.1366 |
| sleet | 0.2775 | 0.1188 | 0.1587 |
| lightsnow | 0.2793 | 0.1143 | 0.1650 |
| heavysnow | 0.2699 | 0.1105 | 0.1594 |

## Mean Modality-Centroid Distance

| Weather | Raw | Common | Unique |
|---|---:|---:|---:|
| normal | 19.33 | 4.99 | 20.74 |
| overcast | 19.44 | 5.02 | 19.98 |
| fog | 19.26 | 4.49 | 18.41 |
| rain | 19.35 | 5.13 | 20.01 |
| sleet | 19.30 | 4.39 | 17.40 |
| lightsnow | 19.44 | 4.66 | 18.37 |
| heavysnow | 19.29 | 4.51 | 18.20 |

## Suggested Figure Choices

- Largest common-state sensor spread: `rain` (5.13).
- Largest unique-state sensor spread: `normal` (20.74).
- In this checkpoint, the learned reliability is strongly LiDAR-dominant across all weather groups, so PCA/centroid-distance plots are more informative than reliability bars for showing sensor-specific structure.