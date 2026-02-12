import sys
import os
import unittest
import ast

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestUIStructure(unittest.TestCase):
    def test_search_async(self):
        """
        Verify that search logic in PlayerScreen is asynchronous.
        """
        path = "src/tui/screens/player.py"
        with open(path, "r") as f:
            tree = ast.parse(f.read())

        player_screen = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PlayerScreen")

        # Check if run_search is async (previously perform_search)
        # It should be an AsyncFunctionDef
        run_search = next((n for n in player_screen.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "run_search"), None)

        self.assertIsNotNone(run_search, "run_search method missing")

        has_work = False
        for d in run_search.decorator_list:
            if isinstance(d, ast.Call) and getattr(d.func, 'id', '') == 'work':
                has_work = True
            elif isinstance(d, ast.Name) and d.id == 'work':
                has_work = True

        self.assertTrue(has_work, "run_search must be decorated with @work")

    def test_login_oauth_async(self):
        """
        Verify OAuth logic in LoginScreen is asynchronous.
        """
        path = "src/tui/screens/login.py"
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            tree = ast.parse(f.read())

        login_screen = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LoginScreen")

        start_oauth = next((n for n in login_screen.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "start_oauth_flow"), None)
        self.assertIsNotNone(start_oauth)

        has_work = any(
            (isinstance(d, ast.Call) and getattr(d.func, 'id', '') == 'work') or
            (isinstance(d, ast.Name) and d.id == 'work')
            for d in start_oauth.decorator_list
        )
        self.assertTrue(has_work, "start_oauth_flow must be decorated with @work")

if __name__ == '__main__':
    unittest.main()
