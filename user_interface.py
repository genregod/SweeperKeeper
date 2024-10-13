import cmd
import logging
from datetime import datetime, timedelta

class SweeperKeeperCLI(cmd.Cmd):
    intro = "Welcome to SweeperKeeper. Type 'help' to list commands."
    prompt = "(sweeper_keeper) "

    def __init__(self, db, casinos, coin_claimer, scheduler):
        super().__init__()
        self.db = db
        self.casinos = casinos
        self.coin_claimer = coin_claimer
        self.scheduler = scheduler
        self.mode = "manual"

    def do_add_casino(self, arg):
        """Add a new social casino. Usage: add_casino <name> <website>"""
        args = arg.split(maxsplit=1)
        if len(args) != 2:
            print("Invalid number of arguments. Usage: add_casino <name> <website>")
            return
        
        name, website = args
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO casinos (name, website) VALUES (?, ?)", (name, website))
        self.db.commit()
        print(f"Added casino: {name}")

    def do_list_casinos(self, arg):
        """List all stored casinos"""
        cursor = self.db.cursor()
        cursor.execute("SELECT id, name, website FROM casinos")
        casinos = cursor.fetchall()
        for casino in casinos:
            print(f"ID: {casino[0]}, Name: {casino[1]}, Website: {casino[2]}")

    def do_add_account(self, arg):
        """Add a user account for a casino. Usage: add_account <casino_id> <username>"""
        args = arg.split()
        if len(args) != 2:
            print("Invalid number of arguments. Usage: add_account <casino_id> <username>")
            return
        
        casino_id, username = args
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO accounts (casino_id, username) VALUES (?, ?)", (casino_id, username))
        self.db.commit()
        print(f"Added account: {username} for casino ID: {casino_id}")

    def do_list_accounts(self, arg):
        """List all stored accounts"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT accounts.id, casinos.name, accounts.username 
            FROM accounts 
            JOIN casinos ON accounts.casino_id = casinos.id
        """)
        accounts = cursor.fetchall()
        for account in accounts:
            print(f"ID: {account[0]}, Casino: {account[1]}, Username: {account[2]}")

    def do_set_reminder(self, arg):
        """Set a reminder for free coin collection. Usage: set_reminder <account_id> <hours>"""
        args = arg.split()
        if len(args) != 2:
            print("Invalid number of arguments. Usage: set_reminder <account_id> <hours>")
            return
        
        account_id, hours = args
        try:
            hours = int(hours)
            reminder_time = datetime.now() + timedelta(hours=hours)
            cursor = self.db.cursor()
            cursor.execute("UPDATE accounts SET next_reminder = ? WHERE id = ?", (reminder_time, account_id))
            self.db.commit()
            print(f"Reminder set for account ID {account_id} in {hours} hours")
        except ValueError:
            print("Invalid hours value. Please enter a number.")

    def do_check_reminders(self, arg):
        """Check for due reminders"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT accounts.id, casinos.name, accounts.username, accounts.next_reminder 
            FROM accounts 
            JOIN casinos ON accounts.casino_id = casinos.id
            WHERE accounts.next_reminder <= ?
        """, (datetime.now(),))
        due_reminders = cursor.fetchall()
        for reminder in due_reminders:
            print(f"Reminder: Collect free coins for {reminder[2]} on {reminder[1]}")
            self.do_set_reminder(f"{reminder[0]} 24")  # Automatically set next reminder for 24 hours

    def do_claim_coins(self, arg):
        """Manually claim coins for an account. Usage: claim_coins <account_id>"""
        if not arg:
            print("Please provide an account ID. Usage: claim_coins <account_id>")
            return
        try:
            account_id = int(arg)
            success = self.coin_claimer.claim_coins(account_id)
            if success:
                print(f"Successfully claimed coins for account {account_id}")
            else:
                print(f"Failed to claim coins for account {account_id}")
        except ValueError:
            print("Invalid account ID. Please enter a number.")

    def do_set_mode(self, arg):
        """Set the operation mode (manual/automated). Usage: set_mode <manual/automated>"""
        if arg not in ["manual", "automated"]:
            print("Invalid mode. Please choose 'manual' or 'automated'.")
            return
        self.mode = arg
        if self.mode == "automated":
            self.scheduler.start()
            print("Automated mode activated. Coin claiming will be performed automatically.")
        else:
            self.scheduler.stop()
            print("Manual mode activated. You'll need to claim coins manually.")

    def do_responsible_gaming(self, arg):
        """Display responsible gaming guidelines and resources"""
        print("Responsible Gaming Guidelines:")
        print("1. Set a budget for your gaming activities and stick to it.")
        print("2. Set time limits for your gaming sessions.")
        print("3. Take regular breaks during gaming sessions.")
        print("4. Never chase your losses.")
        print("5. Don't play when you're feeling stressed or depressed.")
        print("\nResources for help:")
        print("- National Problem Gambling Helpline: 1-800-522-4700")
        print("- Gamblers Anonymous: https://www.gamblersanonymous.org/")
        print("- National Council on Problem Gambling: https://www.ncpgambling.org/")

    def do_exit(self, arg):
        """Exit the program"""
        print("Exiting SweeperKeeper. Goodbye!")
        if self.mode == "automated":
            self.scheduler.stop()
        return True

def start_cli(db, casinos, coin_claimer, scheduler):
    SweeperKeeperCLI(db, casinos, coin_claimer, scheduler).cmdloop()
