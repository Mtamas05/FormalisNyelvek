from project.problem import Problem
import argparse
import importlib
import pkgutil

class Main(object):

    def __init__(self):
        self.problems = []

    def load_problems(self):
        """
        Load all the problems from the problems package
        """
        import os
        from pathlib import Path
        package = 'project.problems'
        package_dir = Path(__file__).parent / 'problems'

        for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
            module = importlib.import_module(f"{package}.{module_name}")

            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if isinstance(attribute, type) and issubclass(attribute, Problem) and attribute is not Problem:
                    self.problems.append(attribute())
    
    def initialize_parser(self):
        """
        Initialize the parser by adding the necessary arguments
        of all the problems
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--input', help='input file')
        parser.add_argument('--output', help='output file')

        for problem in self.problems:
            problem.initialize_parser(parser)

        return parser

    def run(self):
        # First, load the problems
        self.load_problems()

        # Then, initialize the parser
        parser = self.initialize_parser()
        args = parser.parse_args()

        # Find the problem that is chosen
        for problem in self.problems:
            if problem.is_chosen_problem(args):
                # Run the chosen problem
                problem.run(args)
                return
    
        # No problem was chosen
        parser.print_help()

if __name__ == '__main__':
    main = Main()
    main.run()