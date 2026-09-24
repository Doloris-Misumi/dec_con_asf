# TaskDec Weather PCA Analysis

Export: weather-balanced foreground/background patch sample.

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 52.22% | 26.58% |
| common | 54.05% | 22.41% |
| unique | 60.95% | 24.42% |

## Foreground Gate By Weather

| Weather | Gate fg | Gate bg | Delta |
|---|---:|---:|---:|
| normal | 0.2732 | 0.1445 | 0.1287 |
| overcast | 0.2893 | 0.1264 | 0.1628 |
| fog | 0.3038 | 0.1174 | 0.1864 |
| rain | 0.2764 | 0.1287 | 0.1478 |
| sleet | 0.2612 | 0.1180 | 0.1432 |
| lightsnow | 0.2825 | 0.1231 | 0.1594 |
| heavysnow | 0.2611 | 0.1169 | 0.1442 |

## Mean Modality-Centroid Distance

| Weather | Raw | Common | Unique |
|---|---:|---:|---:|
| normal | 18.26 | 3.88 | 22.17 |
| overcast | 18.32 | 3.89 | 21.43 |
| fog | 18.07 | 3.25 | 18.97 |
| rain | 18.22 | 3.76 | 21.52 |
| sleet | 18.24 | 3.61 | 18.37 |
| lightsnow | 18.34 | 3.46 | 19.89 |
| heavysnow | 18.14 | 3.67 | 19.52 |

## Suggested Figure Choices

- Largest common-state sensor spread: `overcast` (3.89).
- Largest unique-state sensor spread: `normal` (22.17).
- In this checkpoint, the learned reliability is strongly LiDAR-dominant across all weather groups, so PCA/centroid-distance plots are more informative than reliability bars for showing sensor-specific structure.