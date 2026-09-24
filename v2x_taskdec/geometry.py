"""KITTI camera/LiDAR geometry without dataset-specific yaw shortcuts."""
from pathlib import Path
import numpy as np


def read_calibration(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            values[key] = np.asarray([float(x) for x in value.split()], dtype=np.float64)
    rect = np.eye(4)
    rect[:3, :3] = values.get('R0_rect', np.eye(3).ravel()).reshape(3, 3)
    extrinsic = np.eye(4)
    extrinsic[:3] = values['Tr_velo_to_cam'].reshape(3, 4)
    raw_lidar_to_camera = rect @ extrinsic
    # Released files include rigs with raw x-forward and raw y-forward LiDAR.
    # Use the camera optical axis projected onto the LiDAR ground plane as ego x.
    forward = raw_lidar_to_camera[2, :2]
    forward = forward / np.linalg.norm(forward)
    raw_lidar_to_ego = np.eye(4)
    raw_lidar_to_ego[:2, :2] = [[forward[0], forward[1]], [-forward[1], forward[0]]]
    lidar_to_camera = raw_lidar_to_camera @ np.linalg.inv(raw_lidar_to_ego)
    projection = values['P2'].reshape(3, 4)
    assert np.isfinite(lidar_to_camera).all() and np.isfinite(projection).all()
    assert abs(np.linalg.det(lidar_to_camera[:3, :3]) - 1) < .05
    radar_to_raw_lidar = np.eye(4)
    radar_to_raw_lidar[:3] = values['Tr_radar_to_velo'].reshape(3, 4)
    return dict(values=values, lidar_to_camera=lidar_to_camera,
                raw_lidar_to_camera=raw_lidar_to_camera, raw_lidar_to_ego=raw_lidar_to_ego,
                radar_to_ego=raw_lidar_to_ego @ radar_to_raw_lidar,
                camera_to_lidar=np.linalg.inv(lidar_to_camera), projection=projection)


def transform_points(points, matrix):
    return points @ matrix[:3, :3].T + matrix[:3, 3]


def project_points(points, calibration):
    camera = transform_points(points, calibration['lidar_to_camera'])
    homogeneous = np.column_stack((camera, np.ones(len(camera))))
    uvz = homogeneous @ calibration['projection'].T
    pixels = uvz[:, :2] / np.maximum(uvz[:, 2:], 1e-6)
    return pixels, camera[:, 2]


def camera_box_to_lidar(location, dimensions_hwl, rotation_y, calibration):
    h, w, length = dimensions_hwl
    center_camera = np.asarray(location, dtype=np.float64) + [0, -h / 2, 0]
    center = transform_points(center_camera[None], calibration['camera_to_lidar'])[0]
    heading_camera = np.array([np.cos(rotation_y), 0, -np.sin(rotation_y)])
    heading_lidar = calibration['camera_to_lidar'][:3, :3] @ heading_camera
    yaw = np.arctan2(heading_lidar[1], heading_lidar[0])
    return np.array([*center, length, w, h, yaw], dtype=np.float32)


def lidar_box_to_camera(box, calibration):
    x, y, z, length, w, h, yaw = box[:7]
    center = transform_points(np.asarray([[x, y, z]]), calibration['lidar_to_camera'])[0]
    location = center + [0, h / 2, 0]
    heading = calibration['lidar_to_camera'][:3, :3] @ np.array([np.cos(yaw), np.sin(yaw), 0])
    rotation_y = np.arctan2(-heading[2], heading[0])
    return location, np.array([h, w, length]), rotation_y


def corners_lidar(boxes):
    signs = np.array([[1,1,1],[1,-1,1],[-1,-1,1],[-1,1,1],
                      [1,1,-1],[1,-1,-1],[-1,-1,-1],[-1,1,-1]], dtype=np.float32)
    local = signs[None] * boxes[:, None, 3:6] * .5
    c, s = np.cos(boxes[:, 6]), np.sin(boxes[:, 6])
    x = local[..., 0] * c[:, None] - local[..., 1] * s[:, None]
    y = local[..., 0] * s[:, None] + local[..., 1] * c[:, None]
    return np.stack([x, y, local[..., 2]], axis=-1) + boxes[:, None, :3]


def augment_world(points_list, boxes, angle, scale, flip_y):
    """Same transform for each sensor and GT; return matrix for camera lifting."""
    c, s = np.cos(angle), np.sin(angle)
    matrix = np.eye(4, dtype=np.float32)
    rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float32)
    reflect = np.diag([1, -1 if flip_y else 1, 1]).astype(np.float32)
    matrix[:3, :3] = scale * rotation @ reflect
    outputs = []
    for points in points_list:
        result = points.copy()
        result[:, :3] = transform_points(points[:, :3], matrix)
        outputs.append(result)
    boxes = boxes.copy()
    boxes[:, :3] = transform_points(boxes[:, :3], matrix)
    boxes[:, 3:6] *= scale
    boxes[:, 6] = angle + (-boxes[:, 6] if flip_y else boxes[:, 6])
    return outputs, boxes, matrix
