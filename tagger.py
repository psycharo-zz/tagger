#!/usr/bin/env python

import cv2
import numpy as np
import os, sys, time, glob, copy, pickle

WINDOW_NAME = 'current frame'

KEY_SPACE = 32
KEY_DEL = 127
KEY_UP = 63232
KEY_DOWN = 63233
KEY_LEFT = 63234
KEY_RIGHT = 63235

BLUE_COLOR = [1,0,0]
GREEN_COLOR = [0,1,0]
RED_COLOR = [0,0,1]
YELLOW_COLOR = [0,1,1]

# HOWTO
# when you switch frames, the current tag points are saved automatically and copied to the next frame
# ']' - next frame
# '[' - prev frame
# 'q' - quit
# 'w' - write the ground truth to the file
# 's' - save currently added points to the target
# 'd' - delete point added at this run
# 'p' - completely delete all the points for the current target
# '0'-'9' - select current target number

def main():
    curr_points = []

    def on_mouse_event(event,x,y,flags,param):
        if cv2.EVENT_FLAG_LBUTTON & flags and event == cv2.EVENT_MOUSEMOVE:
            curr_points.append((x,y))

    def draw_selected_points(pts, color):
        for p in pts:
            cv2.circle(frame, tuple(p), 2, color, 1)

    def update_gt(overwrite=False):
        if len(curr_points) == 0:
            return

        if not fid in gt:
            gt[fid] = {}

        if not curr_oid in gt[fid] or overwrite:
            gt[fid][curr_oid] = {'points_image': copy.deepcopy(curr_points)}

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse_event)

    fid = 0

    gt = {fid: {}}
    if os.path.exists(gt_path + 'ground_truth.pickle'):
        gt = pickle.load(open(gt_path + 'ground_truth.pickle'))

    curr_oid = 0
    frame = frames[fid]

    while True:
        key = cv2.waitKey(1)
        oid = key - ord('0')

        frame = np.copy(frames[fid])
        cv2.putText(frame, str(fid), (20,20), cv2.FONT_HERSHEY_PLAIN, 1, YELLOW_COLOR, 1)

        draw_selected_points(curr_points, RED_COLOR)

        if fid in gt and curr_oid in gt[fid]:
            pts = gt[fid][curr_oid]['points_image']
            draw_selected_points(pts, BLUE_COLOR)
            # drawing text
            p = tuple(np.mean(np.vstack(pts), 0).astype(np.int))
            cv2.putText(frame, str(curr_oid), p, cv2.FONT_HERSHEY_PLAIN, 1, YELLOW_COLOR, 2)

        cv2.imshow(WINDOW_NAME, frame)

        fid_prev = fid

        if key == ord('[') and not fid == start_fid:
            fid -= 1
        elif key == ord(']') and not fid == end_fid:
            fid += 1
        elif key == KEY_DEL:
            if fid in gt and curr_oid in gt[fid]:
                del gt[fid][curr_oid]
        elif key == ord('s'):
            update_gt(True)
        elif key == ord('p'):
            curr_points = []
            if fid in gt and curr_oid in gt[fid]:
                del gt[fid][curr_oid]
        elif key == ord('d'):
            curr_points = []
        elif key == ord('w'):
            pickle.dump(gt, open(gt_path + 'ground_truth.pickle', 'w'))
            pickle.dump(gt, open(tmp_path + 'ground_truth.%d.pickle' % int(time.time()), 'w'))
        elif 0 <= oid <= 9:
            curr_oid = oid
        elif key == ord('q'):
            break

        if fid != fid_prev:
            update_gt()
            frame = frames[fid]

    pickle.dump(gt, open(gt_path + 'ground_truth.pickle', 'w'))
    cv2.destroyAllWindows()

if len(sys.argv) != 3:
    print 'Usage:'
    print 'tagger.py <dataset_path> <format, e.g. rgb%06d.png>'
    exit(-1)

# you can also just fill these in
dataset_path = os.path.abspath(sys.argv[1]) #'/Users/timur/Documents/data/kinect2/ours-drones/seq3/'
input_format = os.path.join(dataset_path, sys.argv[2]) #'depth%06d.png'
# where to save/look for the ground truth
gt_path = dataset_path
# where to save temporary ground truth
tmp_path = '/tmp/'

ext = os.path.splitext(input_format)[1]
start_fid = 0
end_fid = len(glob.glob(os.path.join(dataset_path, '*%s' % ext)))-1

if not os.path.exists(gt_path):
    os.mkdir(gt_path)

print 'loading data from %s, frames %d to %d' % (input_format, start_fid, end_fid)

frames = { fid : cv2.imread(input_format % fid).astype(np.double) / 255.0
           for fid in range(start_fid,end_fid+1) }
main()
