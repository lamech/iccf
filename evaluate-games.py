#!/usr/bin/env python

# Based on original code by Matthew P. Tedesco:
# https://github.com/mptedesco/python-chess-analysis

import os
import sys
import time
import chess
import chess.pgn
import chess.engine
import argparse
import pathlib

logfile = "evaluate-games.log"

# TODO: Use python logging someday.
# TODO: Don't hard code the log file name.
def print_log(*args, **kwargs):
    print(*args, **kwargs)
    log(*args, **kwargs)

def log(*args, **kwargs):
    with open(logfile,'a') as file:
        print(*args, **kwargs, file=file)

def log_game_info(game):
    if 'Event' in game.headers: 
        print_log("Event: " + game.headers['Event'])
    if 'White' in game.headers: 
        print_log("White: " + game.headers['White'])
    if 'Black' in game.headers: 
        print_log("Black: " + game.headers['Black'])
    print_log("Last move: " + str(game.end()))
    print_log("Position: " + game.end().board().fen())
    print_log("\n")

# Given a result dictionary, create a summary.
def result_summary(result):
    summary = ""

    if "opponent" in result:
        trunc_event = result['event'][:12] + "..." if len(result['event']) > 15 else f"{result['event']}"
        trunc_opponent = result['opponent'][:12] + "..." if len(result['opponent']) > 15 else f"{result['opponent']}"
        summary += f"{trunc_event} | {trunc_opponent} | "
    summary += f"Last: {result['last_move']}\n"

    if "color" in result:
        summary += f"{result['color']} | "
    summary += f"Best: {result['best_move']} | Eval: {result['eval']}\n" 

    return summary

# Format a move (node) as a string, with no comments.
def move_str(node):
    board = node.parent.board()
    move_number = node.parent.board().fullmove_number
    move_san = node.san()

    # Format based on whose turn it is.
    if board.turn == chess.WHITE:
        return(f"{move_number}. {move_san}")
    else:
        return(f"{move_number}... {move_san}")

# If we've been given a player, we want to skip games where it's not that
# player's turn.  If we haven't been given a player, we'll want to analyze 
# all the games.

# Given a game object and a player's name, return their opponent's name.
def get_opponent_name(game,player):

    if player is None:
      return None

    if (game.headers['White'] == player):
        return game.headers['Black']
    elif (game.headers['Black'] == player):
        return game.headers['White']
    else:
        return None

# What color is the given player in the given game?
# Returns chess.WHITE, chess.BLACK or None.
def get_color(game,player):

    if (game.headers['White'] == player):
        return chess.WHITE
    elif (game.headers['Black'] == player):
        return chess.BLACK
    else:
        return None

# Convert chess.WHITE or chess.BLACK to a string representation.
# Returns None if neither chess.WHITE nor chess.BLACk is given.
def color_str(color):
   if (color == chess.WHITE):
       return 'White' 
   elif (color == chess.BLACK):
       return 'Black' 
   else:
       return None

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

def log_result(result):
    print_log("Best move: " + result['best_move'])

    if (args.fullpv):
        print_log("Full PV: " + result['full_pv'])

    print_log("Eval: " + result['eval'])
    print_log("Percentage: " + result['percentage'])
    print_log("WDL: " + result['wdl']);
    print_log("------------------------------------\n\n\n")

def evaluate(board, path, enginehash, threads, multipv, depth):
    engine = chess.engine.SimpleEngine.popen_uci(path)
    engine.configure({"Hash": enginehash})
    engine.configure({"Threads": threads})

    print("Starting analysis...")

    analysis = engine.analysis(board=board, limit=chess.engine.Limit(depth=depth), multipv=multipv) 

    # multipv data is 1-indexed not 0-indexed, so our lines list is too:
    lines = [str(i+1) + "." for i in range(int(multipv))]
    full_lines = lines.copy()
    result = {}

    with analysis:

      try:
  
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
  
              full_lines[info.get("multipv") - 1] = "#%d Depth: %d %s %s %s" % (info.get("multipv"), info.get("depth"), format_score(score), format_percentage(score), pvstr)
  
              # Print lines list,
              # then go up a line for each line in list 
              # (see https://stackoverflow.com/a/5291044):
              for line in lines:
                  print(line)
              for line in lines:
                  sys.stdout.write("\033[F")
  
          # Add extra newlines to make up for the output shenanigans above:
          print("\n\n\n")
  
          # Now that analysis is done, print full lines.
          #for line in full_lines:
          #    print(line)
  
          # Grab result of analysis (expecting type chess.engine.BestMove):
          bm = analysis.wait()
  
          result = { 
            'eval': format_score(analysis.info["score"]),
            'best_move': board.san(bm.move),
            'percentage': format_percentage(analysis.info["score"]),
            'wdl': format_wdl(analysis.info["score"]),
            'full_pv': full_lines[0]
          }

      except KeyboardInterrupt:
        print("\n-----------------------------------------\n\n\n\n\n")
        print_log("SIGINT! Here's what the analysis looked like when it got interrupted...")
        engine.quit()
        for line in full_lines:
            print_log(line)
        print("\n-----------------------------------------\n")
        
    engine.quit()
    return result

# Deal with CLI arguments:
_arg_parser = argparse.ArgumentParser(description='Script to analyze multiple games in a PGN file.', fromfile_prefix_chars='@', )
_arg_parser.add_argument('--path', default="stockfish", type=pathlib.Path, help='Engine path. (default: %(default)s)')
_arg_parser.add_argument('--multipv', default=5, type=int, help='How many prinicpal variations the engine should look at concurrently. (default: %(default)s)')
_arg_parser.add_argument('--threads', default=5, type=int, help='How many threads the engine should use. (default: %(default)s)')
_arg_parser.add_argument('--depth', default=20, type=int, help='How deep the engine should look. (default: %(default)s)')
_arg_parser.add_argument('--hash', default=256, type=int, help='How big a hash the engine should use. (default: %(default)s)')
_arg_parser.add_argument('--fullpv', help='Optional. If present: print full Principal Variation after analysis.', action=argparse.BooleanOptionalAction)
_arg_parser.add_argument('--player', help="Optional. If supplied: only look at games in which it is this player's turn.")
_arg_parser.add_argument('file', type=pathlib.Path)

args = _arg_parser.parse_args()
print_log(args)

if (args.player is not None):
    print_log("\n")
    print_log(f"Only analyzing games where it's {args.player}'s turn.")
    print_log("------------------------------------\n\n\n")

# ICCF seems to use latin-1 encoding.
f = open(args.file, 'r', encoding='latin-1')

games = {}
results = []

while True:
    game = chess.pgn.read_game(f)
    if game is None:
        break

    # Skip games that have ended.
    if game.headers['Result'] != '*':
        continue
    
    color_turn = color_str(game.end().turn())

    if (args.player is not None):
        player_color = color_str(get_color(game, args.player))
        if (color_turn == player_color):
            print_log(f"{args.player}'s turn.")
            opponent = get_opponent_name(game,args.player)
        else:
            # If we were given a player, skip games where it's not that player's turn.
            continue
    else:
        print_log(f"{color_turn} to play.")

    if ((args.player is None) or (color_turn == player_color)):
        print_log(f"Evaluating game.")
        log_game_info(game)
        result = evaluate(game.end().board(), args.path, args.hash, args.threads, args.multipv, args.depth)
        if (game.headers['Event'] != ''):
            result['event'] = game.headers['Event']
        if (opponent is not None):
            result['opponent'] = opponent
            result['color'] = player_color
        result['last_move'] = move_str(game.end())
        log_result(result)
        results.append(result)

("------------------------------------\n\n")
print_log("Summary:\n\n")

for result in results:
    print_log(result_summary(result))

print_log("Finished.\n")
