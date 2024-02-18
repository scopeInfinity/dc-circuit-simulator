from build import circuit_pb2
from google.protobuf import text_format
import runner
import argparse

def parse_args():
    parser = argparse.ArgumentParser(prog='Circuit Simulator')
    parser.add_argument('config', type=argparse.FileType('rb'))
    parser.add_argument('-i', '--interactive', action='store_true', help="enable interactive simulation mode")
    parser.add_argument('-pc', '--print-circuit', action='store_true', help="print circuit state with current flows")
    parser.add_argument('-dc', '--draw-circuit', action='store_true', help="visually draw circuit")
    return parser

def get_config(file):
    textpb = file.read()
    config = text_format.Parse(textpb, circuit_pb2.Simulator())
    return config

def main():
    parser = parse_args()
    args = parser.parse_args()
    config = get_config(args.config)
    sim = runner.Sim(config)
    if args.print_circuit or args.draw_circuit:
        sim.step()
        if args.draw_circuit:
            sim.draw(clrscr=False)
        if args.print_circuit:
            sim.print()
    elif args.interactive:
        sim.run()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
