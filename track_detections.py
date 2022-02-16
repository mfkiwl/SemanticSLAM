import cv2
import os
import numpy as np

from KITTI_Classes import *
from utils import *
from SemanticFeatureMatcher import *
from TransformUtils import *

from Open3DRenderer import *
np.set_printoptions(suppress=True, precision=4, linewidth=np.inf)

class TrackingApp:
    def __init__(self):

        self.start = 160
        self.end = 161

        self.kitti_path = '/home/quantum/Workspace/Storage/Other/Temp/dataset/sequences/00/image_0/'
        self.kitti_detections_path = '/home/quantum/Workspace/Storage/Other/Temp/dataset/sequences/00/detections_0/'
        self.kitti_poses_path = '/home/quantum/Workspace/Storage/Other/Temp/dataset/data_odometry_poses/poses/00.txt'

        self.data_exists = os.path.isdir(self.kitti_path)
        self.kitti_imgs = sorted(os.listdir(self.kitti_path)) if self.data_exists else None
        self.detections = load_detections(self.kitti_detections_path + self.kitti_imgs[self.start].replace('image_0', 'detections_0').replace('.png', '.txt')) if self.data_exists else []
        self.prevImg = cv2.imread(self.kitti_path + self.kitti_imgs[self.start]) if self.data_exists else None
        self.gt = np.loadtxt(self.kitti_poses_path, delimiter=' ') if self.data_exists else None

        self.objects = create_tracks(self.detections)
        self.matcher = SemanticFeatureMatcher()
        self.matcher.initialize_tracks(self.objects)
        self.renderer = Open3DRenderer()

        self.pose = np.eye(4)
        self.delta_pose = get_rotation_y(0.4)
        self.delta_pose[0, 3] = 5
        self.delta_pose[2, 3] = 0

    def semantic_matching(self, img, prevImg, file):


        detections = load_detections(
            self.kitti_detections_path + file.replace('image_0', 'detections_0').replace('.png', '.txt'))
        objects = create_tracks(detections)

        self.matcher.associate_detections(objects)

        plot_detection_boxes(img, objects, 2, self.matcher.classes)
        combined = combine_images_vertical(prevImg, img)

        plot_associations(combined, self.matcher, objects)
        display(combined)

        return objects, img

    def run(self):
        for file in self.kitti_imgs:
            img = cv2.imread(self.kitti_path + file)
            objects, img = self.semantic_matching(img, self.prevImg, file)

            self.prevImg = img
            self.matcher.features = objects



    def run_no_data(self):
        gt = np.loadtxt('/home/quantum/Workspace/Storage/Other/Temp/dataset/data_odometry_poses/poses/00.txt', delimiter=' ')
        i = 0
        while True:
            # pose = np.eye(4)
            # pose[:3,:4] = gt[i].reshape((3,4))
            # self.renderer.submit_pose(pose)

            self.renderer.update()
            i+=1

    def init_experimental(self):

        prevImg = cv2.imread(self.kitti_path + self.kitti_imgs[self.start])
        img = cv2.imread(self.kitti_path + self.kitti_imgs[self.end])
        plot_detection_boxes(prevImg, self.objects, 2, self.matcher.classes)
        objects, img = self.semantic_matching(img, prevImg, self.kitti_imgs[self.end])

        print("Total Matches: ", len(self.matcher.matches))

        gt = np.loadtxt('/home/quantum/Workspace/Storage/Other/Temp/dataset/data_odometry_poses/poses/00.txt', delimiter=' ')
        pose = np.eye(4)
        pose[:3,:4] = gt[self.start + 1].reshape((3,4))
        second_pose = np.eye(4)
        second_pose[:3, :4] = gt[self.end + 1].reshape((3, 4))
        pose = np.linalg.inv(second_pose) @ pose

        print("Pose: ")
        print(pose)

        print(self.matcher.table)
        print(self.matcher.matches)

        for i in range(len(self.matcher.features)):
            if self.matcher.table[i, self.matcher.matches[i]] != 0:

                det1 = self.matcher.features[i].bbox
                det2 = objects[self.matcher.matches[i]].bbox

                print("Detections: ", det1, det2)

                psx1, psx2, polytope_x = triangulate_convex_polytope(det2, det1, pose, axis=0)
                psy1, psy2, polytope_y = triangulate_convex_polytope(det2, det1, pose, axis=1)

                point1 = get_object_location_from_size(det1, 2.0)
                point2 = get_object_location_from_size(det2, 2.0)

                self.renderer.submit_pose(pose)

                # self.renderer.submit_quad(np.array([0,0,0]), ps1[0][:3], 5.0, 1.0, [0.3, 0.4, 0.6])
                # self.renderer.submit_quad(np.array([0,0,0]), ps1[1][:3], 5.0, 1.0, [0.6, 0.7, 0.3])
                #
                # self.renderer.submit_quad(ps2[0][:3], ps2[0][3:], 5.0, 1.0, [0.5, 0.8, 0.3])
                # self.renderer.submit_quad(ps2[1][:3], ps2[1][3:], 5.0, 1.0, [0.3, 0.7, 0.5])

                # self.renderer.submit_polytope(polytope)

                polytope = polytope_x + polytope_y
                polytope[:,2] /= 2

                self.renderer.submit_sphere(np.mean(polytope, axis = 0), radius=0.3)
                self.renderer.submit_sphere(point1/4, radius=0.3, color=[0.4, 0.8, 0.5])
                self.renderer.submit_sphere(point2/4, radius=0.3, color=[0.4, 0.4, 0.8])



if __name__ == "__main__":
    app = TrackingApp()
    app.init_experimental()
    app.run_no_data()