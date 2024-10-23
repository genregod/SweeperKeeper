import click
import os
import signal
import sys
from app import app
import logging
import time
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, exiting gracefully...")
    sys.exit(0)

def check_port_available(port):
    """Check if the port is available"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return False
    return True

@click.group()
def cli():
    """Management script for the SweeperKeeper application"""
    pass

@cli.command()
@click.option('--port', default=5000, help='Port to run the server on')
@click.option('--workers', default=None, help='Number of worker processes')
def runserver(port, workers):
    """Run the application server"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if port is available
    if not check_port_available(port):
        logger.error(f"Port {port} is already in use")
        sys.exit(1)
    
    if os.environ.get('FLASK_ENV') == 'production':
        from load_balancer import LoadBalancer
        load_balancer = LoadBalancer(app, port=port)
        try:
            logger.info(f"Starting production server with load balancer on port {port}")
            load_balancer.start()
        except KeyboardInterrupt:
            logger.info("\nShutting down gracefully...")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error starting production server: {str(e)}")
            sys.exit(1)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)

@cli.command()
def init_db():
    """Initialize the database"""
    with app.app_context():
        from models import db
        db.create_all()
        click.echo('Database initialized.')

if __name__ == '__main__':
    cli()
