#!/usr/bin/env python

import os
import sys
import chess
import chess.pgn
import chess.engine
import argparse
import pathlib

logfile = "evaluate-games.log"

# TODO: Use python logging someday.
# TODO: Don't hard code the log file name.
def printLog(*args, **kwargs):
    print(*args, **kwargs)
    log(*args, **kwargs)

def log(*args, **kwargs):
    with open(logfile,'a') as file:
        print(*args, **kwargs, file=file)

_arg_parser = argparse.ArgumentParser(description='Script to analyze multiple games in a PGN file.', fromfile_prefix_chars='@', )
_arg_parser.add_argument('--path', default="stockfish", type=pathlib.Path, help='Engine path. (default: %(default)s)')
_arg_parser.add_argument('--multipv', default=5, type=int, help='How many prinicpal variations the engine should look at concurrently. (default: %(default)s)')
_arg_parser.add_argument('--threads', default=5, type=int, help='How many threads the engine should use. (default: %(default)s)')
_arg_parser.add_argument('--depth', default=20, type=int, help='How deep the engine should look. (default: %(default)s)')
_arg_parser.add_argument('--hash', default=256, type=int, help='How big a hash the engine should use. (default: %(default)s)')
_arg_parser.add_argument('--player', help="Optional. If supplied: only look at games in which it is this player's turn.")
_arg_parser.add_argument('file', type=pathlib.Path)

args = _arg_parser.parse_args()
printLog(args)

if (args.player != None):
    printLog("\n")
    printLog(f"Only analyzing games where it's {args.player}'s turn.")
    printLog("------------------------------------\n\n\n")

def is_player_turn(game,player):
    if ((game.headers['White'] == player) and (game.end().turn() == chess.WHITE)): 
        printLog(f"White to play, {player}'s turn.")
        return True
    elif ((game.headers['Black'] == player) and (game.end().turn() == chess.BLACK)):
        printLog(f"Black to play, {player}'s turn.")
        return True
    else:
        return False

def format_score(score):
    s = score.white().score()
    if s is None:
        if score.is_mate():
            return "M%s" % score.relative.mate() 
        else: return score
    else:
        return "%+.2f" % (round(score.white().score()/100, 2))

def format_percentage(score):
    if score.is_mate():
        return "100%"
    else:
        return "%.2f%%" % (round(score.wdl().white().expectation() * 100, 2))

def format_wdl(score):
    wdl = score.wdl().white()
    return "W: %d D: %d L: %d" % (wdl.wins, wdl.draws, wdl.losses)

def evaluate(board, path, enginehash, threads, multipv, depth):
    engine = chess.engine.SimpleEngine.popen_uci(path)
    engine.configure({"Hash": enginehash})
    engine.configure({"Threads": threads})

    printLog("Starting analysis...")
    
    analysis = engine.analysis(board=board, limit=chess.engine.Limit(depth=depth), multipv=multipv) 

    # multipv data is 1-indexed not 0-indexed, so our lines list is too:
    lines = [str(i+1) + "." for i in range(int(multipv))]

    with analysis:

        # Stream live engine output:
        for info in analysis:
            if info.get("pv") is None:
                continue
            tempboard = board.copy()
            
            moves = []
            for move in info.get("pv"):
                moves.append(tempboard.san(move))
                tempboard.push(move)
            score = info.get("score")

            pvstr = ' '.join(moves)
            # A fun hack for truncating a string to a specified length in python:
            # (see https://stackoverflow.com/a/2873416)
            truncpv = pvstr[:50] + (pvstr[:50] and '..')

            # multipv is 1-indexed not 0-indexed, so we subract 1 for lines list location:
            lines[info.get("multipv") - 1] = "#%d Depth: %d %s %s %s" % (info.get("multipv"), info.get("depth"), format_score(score), format_percentage(score), truncpv)

            # Print lines list,
            # then go up a line for each line in list 
            # (see https://stackoverflow.com/a/5291044):
            for line in lines:
                print(line)
            for line in lines:
                sys.stdout.write("\033[F")

        # Add extra newlines to make up for the output shenanigans above:
        print("\n\n\n")

        # Now that analysis is done, print lines to log file.
        for line in lines:
            log(line)

        # Grab result of analysis (expecting type chess.engine.BestMove):
        result = analysis.wait()

        printLog("Best move: " + board.san(result.move))
        printLog("Eval: " + format_score(analysis.info["score"]))
        printLog("Percentage: " + format_percentage(analysis.info["score"]))
        printLog("WDL: " + format_wdl(analysis.info["score"]))

    engine.quit()

# ICCF seems to use latin-1 encoding.
f = open(args.file, 'r', encoding='latin-1')

games = {}
i = 0
while True:
    i += 1
    game = chess.pgn.read_game(f)
    if game is None:
        break

    # Skip games that have ended.
    if game.headers['Result'] != '*':
        continue
    
    if 'Event' in game.headers: 
        printLog("Event: " + game.headers['Event'])
    if 'White' in game.headers: 
        printLog("White: " + game.headers['White'])
    if 'Black' in game.headers: 
        printLog("Black: " + game.headers['Black'])

    printLog("Last move: " + str(game.end()))
    printLog("Position: " + game.end().board().fen())
    printLog("\n")

    if (args.player != None):
        if (is_player_turn(game,args.player)):
            result = evaluate(game.end().board(), args.path, args.hash, args.threads, args.multipv, args.depth)
        else: 
            printLog(f"Not {args.player}'s turn.")
    else:
        result = evaluate(game.end().board(), args.path, args.hash, args.threads, args.multipv, args.depth)

    printLog("------------------------------------\n\n\n")

printLog("Finished.\n")
