### launch three processes in parallel that run server.py

from multiprocessing import Process
import server

if __name__ == '__main__':
    p1 = Process(target=server.serve, args=('50051', '1'))
    p2 = Process(target=server.serve, args=('50052', '2'))
    p3 = Process(target=server.serve, args=('50053', '3'))
    p1.start()
    p2.start()
    p3.start()

    ## kill p1
    #p1.terminate()
    p1.join()
    p2.join()
    p3.join()