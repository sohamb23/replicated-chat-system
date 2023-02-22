# this script launches the pytest on part 2
pytest --cov=./ test_part2.py & sleep 5 ; kill -9 $!
pkill -f "server.py"