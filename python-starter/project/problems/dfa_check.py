import argparse
from project.problem import Problem


class DFACheckProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--check',
            type=str,
            help='Check comma-separated words against the DFA',
        )

    def is_chosen_problem(self, args):
        return args.check is not None

    def run(self, args):
        input_file = args.input
        output_file = args.output
        words_to_check = [w for w in args.check.split(',')]

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        states = lines[0].split()
        alphabet = set(lines[1].split())
        start_state = lines[2].strip()
        accept_states = set(lines[3].split())

        transitions = {}
        for line in lines[4:]:
            parts = line.split()
            if len(parts) == 3:
                src, sym, dst = parts
                transitions[(src, sym)] = dst

        results = []
        for word in words_to_check:
            current_state = start_state
            valid = True

            for char in word:
                if (current_state, char) in transitions:
                    current_state = transitions[(current_state, char)]
                else:
                    valid = False
                    break

            if valid and (current_state in accept_states):
                results.append("IGEN")
            else:
                results.append("NEM")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))