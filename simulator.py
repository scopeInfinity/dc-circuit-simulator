from build import circuit_pb2
from google.protobuf import text_format
import runner
import argparse

def parse_args():
    parser = argparse.ArgumentParser(prog='Circuit Simulator')
    parser.add_argument('config', type=argparse.FileType('rb'))
    return parser.parse_args()

def get_config(file):
    textpb = file.read()
    config = text_format.Parse(textpb, circuit_pb2.Simulator())
    return config

def main():
    args = parse_args()
    config = get_config(args.config)
    runner.Sim(config).run()

if __name__ == '__main__':
    main()
