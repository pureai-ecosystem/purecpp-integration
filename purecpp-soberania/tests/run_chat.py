# tests/run_chat.py
import os
import sys

from purecpp.soberania import SoberanoChatModel, Message

API_KEY  = os.getenv("SOBERANO_API_KEY", "")
BASE_URL = os.getenv("SOBERANO_BASE_URL", "")

def main():
    args = sys.argv[1:]
    stream = "--stream" in args
    args   = [a for a in args if a != "--stream"]

    prompt = "Olá" if not args else " ".join(args)

    model = SoberanoChatModel(api_key=API_KEY, base_url=BASE_URL)

    if stream:
        print("\n=== STREAM ===")
        for tok in model.stream([Message(role="user", content=prompt)]):
            print(tok, end="", flush=True)
        print("\n=== END ===")
    else:
        resp = model.invoke([Message(role="user", content=prompt)])
        print("\n=== ANSWER ===\n", resp)

if __name__ == "__main__":
    main()
