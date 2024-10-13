import cmd
import logging

class CasinoBotCLI(cmd.Cmd):
    intro = "Welcome to the Social Casino Bot. Type 'help' to list commands."
    prompt = "(casino_bot) "

    def __init__(self, db, coin_claimer, scheduler):
        super().__init__()
        self.db = db
        self.coin_claimer = coin_claimer
        self.scheduler = scheduler

    def do_list_casinos(self, arg):
        """List all stored casinos"""
        cursor = self.db.cursor()
        cursor.execute("SELECT id, name, website FROM casinos")
        casinos = cursor.fetchall()
        for casino in casinos:
            print(f"ID: {casino[0]}, Name: {casino[1]}, Website: {casino[2]}")

    def do_add_credentials(self, arg):
        """Add user credentials for a casino. Usage: add_credentials <casino_id> <username> <password>"""
        args = arg.split()
        if len(args) != 3:
            print("Invalid number of arguments. Usage: add_credentials <casino_id> <username> <password>")
            return
        
        casino_id, username, password = args
        try:
            casino_id = int(casino_id)
            self.db.store_user_credentials(casino_id, username, password)
            print(f"Credentials stored for casino {casino_id}")
        except ValueError:
            print("Invalid casino ID. Please enter a number.")
        except Exception as e:
            print(f"Error storing credentials: {str(e)}")

    def do_claim_coins(self, arg):
        """Manually claim coins for a specific casino. Usage: claim_coins <casino_id>"""
        try:
            casino_id = int(arg)
            success = self.coin_claimer.claim_coins(casino_id)
            if success:
                print(f"Successfully claimed coins for casino {casino_id}")
            else:
                print(f"Failed to claim coins for casino {casino_id}")
        except ValueError:
            print("Invalid casino ID. Please enter a number.")

    def do_exit(self, arg):
        """Exit the program"""
        print("Exiting Social Casino Bot. Goodbye!")
        return True

def start_cli(db, coin_claimer, scheduler):
    CasinoBotCLI(db, coin_claimer, scheduler).cmdloop()

