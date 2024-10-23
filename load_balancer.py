from gevent.pywsgi import WSGIServer
from gevent import monkey
monkey.patch_all()  # Patch all blocking operations

import multiprocessing
import os
import logging
import psutil
import time
import signal
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def timeout(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError()
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

class LoadBalancer:
    def __init__(self, app, host='0.0.0.0', port=5000):
        self.app = app
        self.host = host
        self.port = port
        self.num_workers = self._calculate_workers()
        self.server = None
        self.workers = []
        self.running = True
        
    def _calculate_workers(self):
        """Calculate the optimal number of workers based on CPU cores"""
        cpu_count = multiprocessing.cpu_count()
        return (cpu_count * 2) + 1
    
    def _check_system_resources(self):
        """Monitor system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_memory = memory.available / (1024 * 1024)  # Convert to MB
            
            logger.info(f"System Status - CPU: {cpu_percent}%, Memory: {memory_percent}%, Available Memory: {available_memory:.2f}MB")
            return cpu_percent, memory_percent, available_memory
        except Exception as e:
            logger.error(f"Error checking system resources: {str(e)}")
            return 0, 0, 0
    
    def _adjust_workers(self):
        """Adjust number of workers based on system load"""
        cpu_percent, memory_percent, available_memory = self._check_system_resources()
        
        # Don't scale up if memory is too low (less than 500MB available)
        if available_memory < 500:
            if self.num_workers > multiprocessing.cpu_count():
                self.num_workers = max(self.num_workers - 1, multiprocessing.cpu_count())
                logger.warning("Low memory detected, scaling down workers")
            return

        # Scale up if CPU or memory usage is high but we have enough resources
        if (cpu_percent > 80 or memory_percent > 80) and available_memory > 1000:
            new_workers = min(self.num_workers + 1, multiprocessing.cpu_count() * 4)
            if new_workers > self.num_workers:
                self.num_workers = new_workers
                logger.info(f"Scaling up to {self.num_workers} workers")
            
        # Scale down if resource usage is low
        elif cpu_percent < 30 and memory_percent < 50:
            new_workers = max(self.num_workers - 1, multiprocessing.cpu_count())
            if new_workers < self.num_workers:
                self.num_workers = new_workers
                logger.info(f"Scaling down to {self.num_workers} workers")

    def _spawn_worker(self):
        """Spawn a new worker process"""
        if not self.server:
            logger.error("Cannot spawn worker: server not initialized")
            return None
        
        try:
            process = multiprocessing.Process(target=self._worker_process)
            process.daemon = True
            process.start()
            logger.info(f"Started worker process {process.pid}")
            return process
        except Exception as e:
            logger.error(f"Error spawning worker: {str(e)}")
            return None

    def _worker_process(self):
        """Worker process function"""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Worker process error: {str(e)}")

    def _cleanup_workers(self):
        """Clean up worker processes"""
        logger.info("Cleaning up worker processes")
        for worker in self.workers:
            try:
                if worker and worker.is_alive():
                    worker.terminate()
                    worker.join(timeout=5)
            except Exception as e:
                logger.error(f"Error cleaning up worker: {str(e)}")

    def _initialize_server(self):
        """Initialize the WSGI server with retries"""
        retries = 3
        for attempt in range(retries):
            try:
                self.server = WSGIServer((self.host, self.port), self.app, log=logger)
                with timeout(5):  # 5 seconds timeout for binding
                    self.server.init_socket()
                logger.info(f"Server successfully bound to {self.host}:{self.port}")
                return True
            except TimeoutError:
                logger.error("Timeout while binding to port")
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"Failed to bind to port {self.port}, attempt {attempt + 1}/{retries}")
                    time.sleep(5)
                else:
                    logger.error(f"Failed to initialize server after {retries} attempts: {str(e)}")
                    return False
        return False

    def start(self):
        """Start the load balancer with multiple worker processes"""
        logger.info(f"Starting load balancer with {self.num_workers} workers")
        
        try:
            # Initialize the server
            if not self._initialize_server():
                raise RuntimeError("Failed to initialize server")
            
            # Create initial worker processes
            for _ in range(self.num_workers):
                worker = self._spawn_worker()
                if worker:
                    self.workers.append(worker)
            
            # Monitor and adjust workers
            while self.running:
                self._adjust_workers()
                
                # Check and replace dead workers
                for i, worker in enumerate(self.workers):
                    if not worker or not worker.is_alive():
                        logger.warning(f"Worker {i} is dead, spawning replacement")
                        if worker:
                            worker.terminate()
                        new_worker = self._spawn_worker()
                        if new_worker:
                            self.workers[i] = new_worker
                
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error in load balancer: {str(e)}")
            raise
        finally:
            self.running = False
            logger.info("Shutting down load balancer")
            if self.server:
                try:
                    self.server.stop()
                except Exception as e:
                    logger.error(f"Error stopping server: {str(e)}")
            self._cleanup_workers()

if __name__ == '__main__':
    from app import app
    load_balancer = LoadBalancer(app)
    load_balancer.start()
