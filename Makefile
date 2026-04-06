ICCF ?= .
clean:
	rm -f ~/*.pgn $(ICCF)/*.pgn

$(ICCF)/events.pgn:
	cd $(ICCF) && awk 'FNR==1 && NR!=1 {print ""}{print}' ~/*.pgn > events.pgn

pgn: $(ICCF)/events.pgn

o:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @only.txt events.pgn

o20:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @only-20.txt events.pgn

o45:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @only-45.txt events.pgn

o50:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @only-50.txt events.pgn

a:
	cd $(ICCF) && make -s rotate && time ./evaluate-games.py @args.txt events.pgn

$(ICCF)/logrotate.conf:
	cd $(ICCF) && envsubst < logrotate.conf.tmpl > logrotate.conf

rotate: $(ICCF)/logrotate.conf
	cd $(ICCF) && logrotate -s ./logrotate.status ./logrotate.conf
