#!/usr/bin/env python
import sys
import chess
import chess.pgn
import chess.engine

def format_score(score):
    return "%+.2f" % (round(score.white().score()/100, 2))

def format_percentage(score):
    return "%.2f%%" % (round(score.wdl().white().expectation() * 100, 2))

def format_wdl(score):
    wdl = score.wdl().white()
    return "W: %d D: %d L: %d" % (wdl.wins, wdl.draws, wdl.losses)

def evaluate(board):
    engine = chess.engine.SimpleEngine.popen_uci(r"stockfish")
    engine.configure({"Hash": 2048})
    engine.configure({"Threads": 3})

    print("Starting analysis...")
    
    multipv = 3

    analysis = engine.analysis(board=board, limit=chess.engine.Limit(depth=40), multipv=multipv) 
    # TO DO: don't hard code this, initialize cache based on multipv value.
    cache = ["#1","#2","#3"]

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

            # multipv is 1-indexed not 0-indexed, so we subract 1 for cache list location:
            cache[info.get("multipv") - 1] = "#%d Depth: %d %s %s %s" % (info.get("multipv"), info.get("depth"), format_score(score), format_percentage(score), truncpv)

            # Print cache,
            # then go up a line for each line in cache 
            # (see https://stackoverflow.com/a/5291044):
            for line in cache:
                print(line)
            for line in cache:
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
    
    print("Event: " + game.headers['Event'])
    print("White: " + game.headers['White'])
    print("Black: " + game.headers['Black'])
    print("Last move: " + str(game.end()))
    print("Position: " + game.end().board().fen())
    print("\n")

    if (game.headers['White'] == me) and game.end().turn():
        print("White to play, my turn.\n\n")
        result = evaluate(game.end().board())
    elif (game.headers['Black'] == me) and not(game.end().turn()):
        print("Black to play, my turn.\n\n")
        result = evaluate(game.end().board())
    else: 
        print("Not my turn.")
        print("------------------------------------\n\n\n")
        continue

    print("------------------------------------\n\n\n")
