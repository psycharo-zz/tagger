#!/usr/bin/env python

import cv2
import numpy as np
from scipy.io import savemat
import os, sys, time, glob, copy, pickle

WINDOW_NAME = 'tagger'

KEY_SPACE = 32
KEY_DEL = 127
KEY_UP = 63232
KEY_DOWN = 63233
KEY_LEFT = 63234
KEY_RIGHT = 63235

BLUE_COLOR = [255,0,0]
GREEN_COLOR = [0,255,0]
RED_COLOR = [0,0,255]
YELLOW_COLOR = [0,255,255]

def main():
    curr_points = []

    def on_mouse_event(event,x,y,flags,param):
        if cv2.EVENT_FLAG_LBUTTON & flags and event == cv2.EVENT_MOUSEMOVE:
            curr_points.append((x,y))

    def draw_selected_points(pts, color):
        for p in pts:
            cv2.circle(frame, p, 2, color, 1)

    def rescale_points(pts, f):
        return [(int(p[0] * f), int(p[1] * f)) for p in pts]

    def rescale_gt(gt, f):
        gt_rescaled = {}
        for fid in gt:
            gt_rescaled[fid] = {}
            for oid in gt[fid]:
                gt_rescaled[fid][oid] = {'points' : rescale_points(gt[fid][oid]['points'], f)}
        return gt_rescaled

    def update_gt(overwrite=False):
        if len(curr_points) == 0:
            return

        if not fid in gt:
            gt[fid] = {}

        if not curr_oid in gt[fid] or overwrite:
            gt[fid][curr_oid] = {'points': copy.deepcopy(curr_points)}

    def save_gt(gt):
        # taking into account image resize
        gt_rescaled = rescale_gt(gt, 1.0 / resize_factor)
        pickle.dump(gt_rescaled, open(os.path.join(gt_path, 'ground_truth.pickle'), 'w'))

        # matlab
        gt_mat = {}
        for fid in gt_rescaled:
            gt_mat['f%d' % fid] = {} 
            for oid in gt_rescaled[fid]:
                gt_mat['f%d' % fid]['o%d' % oid] = gt_rescaled[fid][oid]
        savemat(os.path.join(gt_path, 'ground_truth.mat'), gt_mat)    
        

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse_event)

    fid = 0

    gt = {fid: {}}
    if os.path.exists(os.path.join(gt_path, 'ground_truth.pickle')):
        gt = rescale_gt(pickle.load(open(os.path.join(gt_path, 'ground_truth.pickle'))), resize_factor)

    curr_oid = 0
    frame = frames[fid]

    while True:
        key = cv2.waitKey(1)
        oid = key - ord('0')

        frame = np.copy(frames[fid])
        cv2.putText(frame, str(fid), (20,20), cv2.FONT_HERSHEY_PLAIN, 1, YELLOW_COLOR, 1)
        cv2.putText(frame, 'class: %d' % curr_oid, (frame.shape[1]-80,20), cv2.FONT_HERSHEY_PLAIN, 1, YELLOW_COLOR, 1)        

        draw_selected_points(curr_points, RED_COLOR)

        if fid in gt and curr_oid in gt[fid]:
            pts = gt[fid][curr_oid]['points']
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
        elif key == ord('='):
            curr_oid += 1
        elif key == ord('-'):
            curr_oid = max(0, curr_oid-1)
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
            save_gt(gt)
            pickle.dump(gt, open(os.path.join(tmp_path, 'ground_truth.%d.pickle' % int(time.time())), 'w'))
            
        elif 0 <= oid <= 9:
            curr_oid = oid
        elif key == ord('q'):
            break

        if fid != fid_prev:
            update_gt()
            frame = frames[fid]

    save_gt(gt)
    cv2.destroyAllWindows()

if len(sys.argv) != 4:
    print 'Usage:'
    print 'tagger.py <dataset_path> <format, e.g. rgb%06d.png> <resize factor>'
    exit(-1)

# you can also just fill these in
dataset_path = os.path.abspath(sys.argv[1]) #'/Users/timur/Documents/data/kinect2/ours-drones/seq3/'
input_format = os.path.join(dataset_path, sys.argv[2]) #'depth%06d.png'
resize_factor = float(sys.argv[3])
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

frames = { fid : cv2.resize(cv2.imread(input_format % fid), (0,0), None, resize_factor, resize_factor)
           for fid in range(start_fid,end_fid+1) }
main()
