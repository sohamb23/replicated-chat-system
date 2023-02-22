# this script launches the pytest on part 2
pytest --cov=./ test_part1.py & sleep 5 ; kill -9 $!
pkill -f "python3 server.py"