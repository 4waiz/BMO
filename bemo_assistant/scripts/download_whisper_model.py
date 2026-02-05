import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="small.en")
    parser.add_argument("--output", default="models/whisper")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    from faster_whisper import WhisperModel

    print(f"Downloading model {args.model} to {out_dir}")
    WhisperModel(args.model, device="cpu", compute_type="int8", download_root=str(out_dir))
    print("Done")


if __name__ == "__main__":
    main()
