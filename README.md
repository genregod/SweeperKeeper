# SweeperKeeper

SweeperKeeper is an automated social casino tracker and free coin claimer built with Python and Flask. It helps users efficiently manage their social casino accounts and maximize their free coin earnings.

## Features

- Multi-casino support (Chumba Casino, LuckyLand Slots, Global Poker, Funzpoints, Pulsz Casino)
- Automated coin claiming with multi-threading
- User authentication and account management
- Detailed analytics dashboard
- Mobile-friendly web interface
- Load balancing for high availability
- Real-time system resource monitoring
- Responsible gaming guidelines

## Technology Stack

- Backend: Python, Flask
- Database: PostgreSQL
- Frontend: Bootstrap, JavaScript
- Mobile: React Native with Expo
- Load Balancing: Custom implementation with gevent

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sweeperkeeper.git
cd sweeperkeeper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
- FLASK_SECRET_KEY
- DATABASE_URL
- PGHOST
- PGPORT
- PGUSER
- PGPASSWORD
- PGDATABASE

4. Initialize the database:
```bash
python manage.py init_db
```

5. Run the application:
```bash
# Development
python app.py

# Production
FLASK_ENV=production python manage.py runserver --port 5000
```

## Project Structure

- `app.py` - Main Flask application
- `models.py` - Database models
- `analytics.py` - Analytics functionality
- `coin_claimer.py` - Core coin claiming logic
- `casino_locator.py` - Casino discovery and verification
- `load_balancer.py` - Production load balancer
- `SweeperKeeperMobile/` - Mobile application

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Users are responsible for complying with the terms of service of any social casino platforms they interact with.
