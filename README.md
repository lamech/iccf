Automate analysis of chess games in PGN format.
```
$ ./evaluate-games.py -h
usage: evaluate-games.py [-h] [--path PATH] [--multipv MULTIPV]
                         [--threads THREADS] [--depth DEPTH] [--hash HASH]
                         [--player PLAYER]
                         file

Script to analyze multiple games in a PGN file.

positional arguments:
  file

options:
  -h, --help         show this help message and exit
  --path PATH        Engine path. (default: stockfish)
  --multipv MULTIPV  How many prinicpal variations the engine should look at
                     concurrently. (default: 5)
  --threads THREADS  How many threads the engine should use. (default: 5)
  --depth DEPTH      How deep the engine should look. (default: 20)
  --hash HASH        How big a hash the engine should use. (default: 256)
  --player PLAYER    Optional. If supplied: only look at games in which it is
                     this player's turn.
```

Author: Dan Friedman
