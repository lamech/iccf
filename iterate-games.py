#!/usr/bin/env python

import os
import sys
import chess
import chess.pgn
import chess.engine
#import argparse
# TODO: replace all this env var parsing with argparse
#_arg_parser = argparse.ArgumentParser()
#_arg_parser.add_argument()
#args = _arg_parser.parse()

_engine_path = os.environ.get('ICCF_ENGINE_PATH', r"stockfish")
_engine_multipv = os.environ.get('ICCF_MULTIPV', 5)
_engine_threads = os.environ.get('ICCF_THREADS', 5)
_engine_depth = os.environ.get('ICCF_DEPTH', 20)
_engine_hash = os.environ.get('ICCF_HASH', 256)

# Default to True, require the string 'True':
_only_my_turn = (os.getenv('ICCF_ONLY_MY_TURN', 'True') == 'True')
if (_only_my_turn):
    print("\n")
    print("Only analyzing games where it's my turn.")
    print("------------------------------------\n\n\n")

def is_my_turn(game):
    if ((game.headers['White'] == me) and (game.end().turn() == chess.WHITE)): 
        print("White to play, my turn.")
        return True
    elif ((game.headers['Black'] == me) and (game.end().turn() == chess.BLACK)):
        print("White to play, my turn.")
        return True
    else:
        return False

def format_score(score):
    return "%+.2f" % (round(score.white().score()/100, 2))

def format_percentage(score):
    return "%.2f%%" % (round(score.wdl().white().expectation() * 100, 2))

def format_wdl(score):
    wdl = score.wdl().white()
    return "W: %d D: %d L: %d" % (wdl.wins, wdl.draws, wdl.losses)

def evaluate(board):
    engine = chess.engine.SimpleEngine.popen_uci(_engine_path)
    engine.configure({"Hash": _engine_hash})
    engine.configure({"Threads": _engine_threads})

    print("Starting analysis...")
    
    analysis = engine.analysis(board=board, limit=chess.engine.Limit(depth=_engine_depth), multipv=_engine_multipv) 

    # multipv data is 1-indexed not 0-indexed, so our lines list is too:
    lines = [str(i+1) + "." for i in range(int(_engine_multipv))]

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

        # Grab result of analysis (expecting type chess.engine.BestMove):
        result = analysis.wait()

        print("Best move: " + board.san(result.move))
        print("Eval: " + format_score(analysis.info["score"]))
        print("Percentage: " + format_percentage(analysis.info["score"]))
        print("WDL: " + format_wdl(analysis.info["score"]))

    engine.quit()

# ICCF seems to use latin-1 encoding.
f = open(sys.argv[1], 'r', encoding='latin-1')

me = 'Friedman, Dan'

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
        print("Event: " + game.headers['Event'])
    if 'White' in game.headers: 
        print("White: " + game.headers['White'])
    if 'Black' in game.headers: 
        print("Black: " + game.headers['Black'])

    print("Last move: " + str(game.end()))
    print("Position: " + game.end().board().fen())
    print("\n")

    # TODO: move is_my_turn and all the analysis code out to a module.

    if _only_my_turn:
        if (is_my_turn(game)):
            result = evaluate(game.end().board())
        else: 
            print("Not my turn.")
    else:
        result = evaluate(game.end().board())

    print("------------------------------------\n\n\n")

