import sys
import chess
import chess.pgn
import chess.engine

def evaluate(board):
    engine = chess.engine.SimpleEngine.popen_uci(r"/opt/homebrew/bin/stockfish")
    engine.configure({"Hash": 2048})
    engine.configure({"Threads": 3})

    with engine.analysis(board=board, limit=chess.engine.Limit(depth=40)    , multipv=3) as analysis:
        # Expect result of type chess.engine.BestMove:
        result = analysis.wait()
        # TO DO: can I both stream live engine output *and* collect resulting best move?
        print("Best move: " + board.san(result.move))
        print("Ponder (expected next move from opponent): " + board.san(result.ponder))

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
