ICCF ?= .
PGN ?= $(ICCF)/events.pgn
clean:
	rm -f ~/*.pgn $(PGN)

$(PGN):
	cd $(ICCF) && awk 'FNR==1 && NR!=1 {print ""}{print}' ~/*.pgn > events.pgn

pgn: $(PGN)

evaluate_games:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @$(CONFIG_FILE) $(PGN)

o:
	make -s evaluate_games summary CONFIG_FILE=only-40.txt

o.%:
	make -s evaluate_games summary CONFIG_FILE=only-$(*).txt

a:
	make -s evaluate_games summary CONFIG_FILE=args.txt

a.%:
	make -s evaluate_games summary CONFIG_FILE=args-$(*).txt

$(ICCF)/logrotate.conf:
	cd $(ICCF) && envsubst < logrotate.conf.tmpl > logrotate.conf

rotate: $(ICCF)/logrotate.conf
	cd $(ICCF) && logrotate -s ./logrotate.status ./logrotate.conf

summary:
	@cd $(ICCF) && jq -r '["Event","Opponent","Last","Colour","Eval","Best"], (.[] | [.event,.opponent,.last_move,.color,.eval,.best_move]) | @csv'  results.json | csvlook --max-column-width 16

summary.%:
	@cd $(ICCF) && jq -r '["Event","Opponent","Last","Colour","Eval","Best"], (.[] | [.event,.opponent,.last_move,.color,.eval,.best_move]) | @csv'  results.json.$(*) | csvlook --max-column-width 16
