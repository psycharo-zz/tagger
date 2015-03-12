# tagger
a simplistic tool for tagging multiple objects in images

# Usage
```
python tagger.py <path-to-dataset> <format>
```
`<format>` has to contain `%d`, e.g. `rgb%06d.png`

When you switch frames, the current tag points are saved automatically and copied to the next frame
- ']' - next frame
- '[' - prev frame
- 'q' - quit
- 'w' - write the ground truth to the file
- 's' - save currently added points to the target
- 'd' - delete point added at this run
- 'p' - completely delete all the points for the current target
- '0'-'9' - select current target number
